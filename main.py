import streamlit as st
import os
import time
import pandas as pd
import threading
from services.auth.login_wall import render_auth_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles, load_premium_theme, hero_banner
from services.persistence.exercise_repository import init_db, get_user_stats
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio

def logout():
    """Logout user and clear session"""
    for key in ["user_id", "username", "user_email", "workout_started", 
                "exercise_type", "target_sets", "reps_per_set", "reps",
                "current_set_reps", "sets_completed", "video_processor"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="wide"
    )

    # Load premium styling
    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")
    load_premium_theme()

    # Initialize database
    init_db()

    # Show auth wall if not logged in
    if not render_auth_wall():
        return 

    # Initialize session defaults
    initial_session_defaults()

    # Initialize voice pipeline
    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            
            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
            
            if st.session_state.get("username"):
                st.session_state.voice_pipeline.set_user_name(st.session_state.username)
                
        except Exception as e:
            print(f"Error initializing voice pipeline: {e}")
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    
    # ============================================
    # SIDEBAR
    # ============================================
    with st.sidebar:
        # Premium header
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <div style="font-size: 1.5rem;">🏋️‍♂️</div>
            <div style="font-weight: 700; font-size: 1rem;">AI Coach Pro</div>
        </div>
        """, unsafe_allow_html=True)
        
        # User profile section
        if st.session_state.get("username"):
            with st.expander("👤 My Profile", expanded=False):
                st.markdown(f"**Welcome, {st.session_state.username}!**")
                st.caption(f"📧 {st.session_state.get('user_email', 'Not set')}")
                
                stats = get_user_stats(st.session_state.user_id)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏋️ Workouts", stats['total_workouts'])
                    st.metric("💪 Reps", stats['total_reps'])
                with col2:
                    st.metric("📊 Sets", stats['total_sets'])
                    st.metric("⏱️ Time", f"{stats['total_time']}s")
                
                if st.button("🚪 Logout", use_container_width=True):
                    logout()
        
        st.divider()
        
        # Workout Plan Section
        st.markdown("### 📋 Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox(
                "Choose Exercise", 
                options=EXERCISE_OPTIONS, 
                key="plan_exercise"
            )

            col1, col2 = st.columns(2)
            with col1:
                plan_sets = st.number_input(
                    "Number of Sets", 
                    min_value=1, 
                    max_value=50, 
                    key="plan_sets", 
                    step=1,
                    value=3,
                    help="How many sets you want to complete"
                )
            with col2:
                plan_reps = st.number_input(
                    "Reps per Set", 
                    min_value=1, 
                    max_value=50, 
                    key="plan_reps", 
                    step=1,
                    value=10,
                    help="How many repetitions in each set"
                )

            st.caption("💡 Tip: Start with fewer reps to master your form")
            
            start_session_button = st.button(
                "▶️ Start Workout", 
                use_container_width=True, 
                key="start_session_button",
                type="primary"
            )

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.workout_started_notified = False
                st.session_state.last_face_notification = 0
                st.session_state.last_pose_notification = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={"reps_per_set": plan_reps, "target_sets": plan_sets}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            # Active Workout Section in Sidebar
            exercise = st.session_state.get("exercise_type", "Unknown")
            sets = st.session_state.get("target_sets", 0)
            reps = st.session_state.get("reps_per_set", 0)
            
            # Active workout card
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #00d4ff 0%, #667eea 100%);
                padding: 0.75rem;
                border-radius: 10px;
                margin: 0.5rem 0;
                text-align: center;
            ">
                <div style="font-size: 1rem;">🔥 ACTIVE WORKOUT 🔥</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"**{exercise}**")
            st.caption(f"🎯 Goal: {sets} Sets × {reps} Reps")

            end_session_button = st.button(
                "⏹️ End Workout", 
                key="end_session_button", 
                use_container_width=True
            )

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={"reps": st.session_state.get("reps", 0)}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result
                st.rerun()

            st.divider()
            
            # Live Progress in Sidebar
            st.markdown("### 📊 Live Progress")
            
            sets_completed = st.session_state.get("sets_completed", 0)
            target_sets = st.session_state.get("target_sets", 1)
            set_progress = sets_completed / target_sets if target_sets > 0 else 0
            
            st.markdown(f"**Sets Completed:** {sets_completed} / {target_sets}")
            st.progress(set_progress, text=f"{int(set_progress * 100)}% Complete")
            
            current_set_reps = st.session_state.get("current_set_reps", 0)
            reps_per_set = st.session_state.get("reps_per_set", 1)
            rep_progress = current_set_reps / reps_per_set if reps_per_set > 0 else 0
            
            st.markdown(f"**Current Set Reps:** {current_set_reps} / {reps_per_set}")
            st.progress(rep_progress, text=f"{int(rep_progress * 100)}% of this set")
            
            total_reps = st.session_state.get("reps", 0)
            st.metric("🏆 Total Reps Completed", f"{total_reps}")
            
            st.divider()
            
            # Exercise-specific metrics in sidebar
            exercise = st.session_state.get("exercise_type", "Unknown")
            
            if exercise == "Squats":
                st.markdown("### 🦵 Squat Form")
                knee_angle = st.session_state.get('knee_angle', 0)
                st.metric("Knee Angle", f"{knee_angle}°", help="Ideal: 90-110°")
                back_angle = st.session_state.get('back_angle', 0)
                st.metric("Back Angle", f"{back_angle}°", help="Keep back straight")
                depth = st.session_state.get('depth_status', 'N/A')
                st.metric("Depth", depth, help="How low you're going")

            elif exercise == "Push-ups":
                st.markdown("### 💪 Push-up Form")
                elbow_angle = st.session_state.get('elbow_angle', 0)
                st.metric("Elbow Angle", f"{elbow_angle}°", help="Ideal: 90° at bottom")
                alignment = st.session_state.get('body_alignment', 'N/A')
                st.metric("Body Alignment", alignment, help="Keep body straight")
                hips = st.session_state.get('hip_status', 'N/A')
                st.metric("Hip Position", hips, help="Don't sag or pike")

            elif exercise == "Biceps Curls (Dumbbell)":
                st.markdown("### 💪 Curl Form")
                elbow_angle = st.session_state.get('elbow_angle', 0)
                st.metric("Elbow Angle", f"{elbow_angle}°", help="Full contraction at top")
                shoulders = st.session_state.get('shoulder_status', 'N/A')
                st.metric("Shoulders", shoulders, help="Keep shoulders stable")
                swing = st.session_state.get('swing_status', 'N/A')
                st.metric("Swing", swing, help="Avoid using momentum")

            elif exercise == "Shoulder Press":
                st.markdown("### 🏋️ Shoulder Press")
                elbow_angle = st.session_state.get('elbow_angle', 0)
                st.metric("Elbow Angle", f"{elbow_angle}°", help="Full extension at top")
                extension = st.session_state.get('extension_status', 'N/A')
                st.metric("Extension", extension, help="Full arm extension")
                back = st.session_state.get('back_arch_status', 'N/A')
                st.metric("Back Arch", back, help="Keep back straight")

            elif exercise == "Lunges":
                st.markdown("### 🦵 Lunge Form")
                knee_angle = st.session_state.get('front_knee_angle', 0)
                st.metric("Front Knee", f"{knee_angle}°", help="90° angle ideal")
                torso = st.session_state.get('torso_angle', 0)
                st.metric("Torso Angle", f"{torso}°", help="Keep torso upright")
                balance = st.session_state.get('balance_status', 'N/A')
                st.metric("Balance", balance, help="Stability check")
            
            # Show detected exercise if mismatch
            if st.session_state.get("video_processor"):
                processor = st.session_state.video_processor
                if processor:
                    metrics = processor.get_latest_metrics()
                    if metrics and metrics.get("detected_exercise"):
                        detected = metrics.get("detected_exercise")
                        if detected != exercise:
                            st.warning(f"⚠️ Detected: {detected}")
                        else:
                            st.success(f"✅ Form Detected")

    # ============================================
    # MAIN CONTENT AREA
    # ============================================
    
    hero_banner()
    
    # Voice feedback
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)
        def clear_audio():
            time.sleep(0.1)
            if "audio_to_play" in st.session_state:
                st.session_state.audio_to_play = None
        threading.Thread(target=clear_audio, daemon=True).start()

    if st.session_state.get("coach_feedback"):
        st.success(f"🤖 **AI Coach:** {st.session_state.coach_feedback}")
        def clear_feedback():
            time.sleep(0.5)
            if "coach_feedback" in st.session_state:
                st.session_state.coach_feedback = None
        threading.Thread(target=clear_feedback, daemon=True).start()

    if not workout_started:
        # Welcome screen when no workout is active
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
                border-radius: 20px;
                padding: 3rem 2rem;
                text-align: center;
                border: 2px solid rgba(102,126,234,0.3);
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
                <h2 style="color: #00d4ff;">Ready to Train?</h2>
                <p style="font-size: 1rem; color: #cbd5e1;">
                    Set up your workout plan in the sidebar and click <strong>Start Workout</strong>
                </p>
                <div style="margin-top: 1.5rem;">
                    <span style="background: rgba(0,212,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem;">
                        💪 Squats  •  Push-ups  •  Curls  •  Shoulder Press  •  Lunges
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Live camera feed
        st.markdown("### 🎥 Live Camera Feed")
        st.caption("Position yourself so your full body is visible")
        
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )
        
        if context and context.video_processor:
            st.session_state.video_processor = context.video_processor

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    # ============================================
    # WORKOUT HISTORY
    # ============================================
    st.markdown("## 📜 Workout History")
    
    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)
        
        if history_rows:
            arr = []
            for row in history_rows:
                arr.append({
                    "🏋️ Exercise": row['exercise_name'],
                    "🔄 Reps": row['reps'],
                    "📊 Sets": row['sets'],
                    "⏱️ Time (sec)": row['time'],
                    "📅 Date": row['created_at'][:10] if row['created_at'] else 'N/A'
                })

            df = pd.DataFrame(arr)

            if not df.empty:
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "🏋️ Exercise": st.column_config.TextColumn("Exercise"),
                        "🔄 Reps": st.column_config.NumberColumn("Total Reps"),
                        "📊 Sets": st.column_config.NumberColumn("Sets"),
                        "⏱️ Time (sec)": st.column_config.NumberColumn("Duration"),
                        "📅 Date": st.column_config.TextColumn("Date")
                    }
                )
            else:
                st.info("✨ No workout history yet. Start your fitness journey!")
        else:
            st.info("✨ No workout history yet. Start your first workout!")

if __name__ == "__main__":
    main()