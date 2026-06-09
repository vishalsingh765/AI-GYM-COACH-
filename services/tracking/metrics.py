import streamlit as st
import time
import threading
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise
from services.coaching.voice_pipeline import autoplay_audio
def sync_metrics_update(context):
    if not context or not hasattr(context, "state") or not context.state.playing:
        return

    processor = getattr(context, "video_processor", None)

    if not processor:
        return

    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return

    processor.set_exercise(exercise)

    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return

    reps = latest_metrics.get("reps", 0)

    if reps is None:
        reps = 0

    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise)

    if fields:
        for key, default in fields.items():
            st.session_state[key] = latest_metrics.get(key, default)

    reps_per_set = st.session_state.get("reps_per_set", 0)
    target_sets = st.session_state.get("target_sets", 0)

    if reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    last_saved_sets = st.session_state.get(
        "last_saved_sets_completed",
        0
    )

    now = time.time()

    # ==========================
    # WORKOUT STARTED
    # ==========================
    if not st.session_state.get("workout_started_notified", False):
        if reps > 0 or sets_completed > 0 or current_set_reps > 0:
            if st.session_state.get("voice_pipeline"):
                result = st.session_state.voice_pipeline.process_event(
                    event="workout_started",
                    exercise=exercise,
                    metrics=latest_metrics,
                )
                if result and not st.session_state.get("audio_to_play"):
                    audio, feedback = result
                    print(f"🔊 WORKOUT STARTED: {feedback}")
                    st.session_state.audio_to_play = audio
                    st.session_state.coach_feedback = feedback
                    st.session_state.workout_started_notified = True

    # ==========================
    # SET COMPLETED
    # ==========================
    if (
        target_sets > 0
        and reps_per_set > 0
        and sets_completed > last_saved_sets
    ):

        newly_completed = sets_completed - last_saved_sets

        now_ts = time.time()
        started_at = st.session_state.get(
            "set_cycle_started_at",
            now_ts
        )

        time_taken = now_ts - started_at

        user_id = st.session_state.get("user_id", 0)

        add_exercise(
            user_id,
            exercise,
            newly_completed * reps_per_set,
            newly_completed,
            time_taken
        )

        if st.session_state.get("voice_pipeline"):

            result = st.session_state.voice_pipeline.process_event(
                event="set_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )

            if (
                result
                and not st.session_state.get("audio_to_play")
            ):
                audio, feedback = result

                print(f"🔊 SET COMPLETED: {feedback}")

                st.session_state.audio_to_play = audio
                st.session_state.coach_feedback = feedback

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

    # ==========================
    # REPS ANNOUNCEMENT
    # ==========================
    if st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event="reps_announcement",
            exercise=exercise,
            metrics=latest_metrics,
        )
        if result and not st.session_state.get("audio_to_play"):
            audio, feedback = result
            print(f"🔊 REPS ANNOUNCEMENT: {feedback}")
            st.session_state.audio_to_play = audio
            st.session_state.coach_feedback = feedback

    # ==========================
    # WORKOUT COMPLETED
    # ==========================
    if (
        workout_completed
        and not st.session_state.get(
            "last_notified_workout_complete",
            False
        )
    ):

        st.session_state.last_notified_workout_complete = True

        if st.session_state.get("voice_pipeline"):

            result = st.session_state.voice_pipeline.process_event(
                event="workout_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )

            if (
                result
                and not st.session_state.get("audio_to_play")
            ):
                audio, feedback = result

                print(f"🔊 WORKOUT COMPLETED: {feedback}")

                st.session_state.audio_to_play = audio
                st.session_state.coach_feedback = feedback

    # ==========================
    # EXERCISE MISMATCH DETECTION - FIXED
    # ==========================
    detected_exercise = latest_metrics.get("detected_exercise", None)
    selected_exercise = exercise
    
    # Get last notification time to avoid spam
    last_mismatch_notification = st.session_state.get("last_mismatch_notification", 0)
    mismatch_cooldown = 15  # Wait 15 seconds between mismatch notifications
    
    if (detected_exercise and 
        detected_exercise != selected_exercise and
        now - last_mismatch_notification > mismatch_cooldown):
        
        print(f"⚠️ EXERCISE MISMATCH DETECTED! Selected: {selected_exercise}, Detected: {detected_exercise}")
        
        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="exercise_mismatch",
                exercise=selected_exercise,
                metrics=latest_metrics,
                detected_exercise=detected_exercise,
            )
            
            if result and not st.session_state.get("audio_to_play"):
                audio, feedback = result
                print(f"🔊 EXERCISE MISMATCH VOICE: {feedback}")
                st.session_state.audio_to_play = audio
                st.session_state.coach_feedback = feedback
                st.session_state.last_mismatch_notification = now
                
                # Also store in session state to show in UI
                st.session_state.last_mismatch_message = feedback
                # Clear after 5 seconds
                threading.Timer(5.0, lambda: st.session_state.pop("last_mismatch_message", None)).start()
    
    # ==========================
    # FACE NOT VISIBLE
    # ==========================
    print("FACE_VISIBLE =", latest_metrics.get("face_visible"))
    print("POSE_DETECTED =", latest_metrics.get("pose_detected"))
    face_visible = latest_metrics.get("face_visible", True)
    last_face_notification = st.session_state.get("last_face_notification", 0)
    
    if not face_visible and now - last_face_notification > 10:
        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="no_pose_detected",
                exercise=exercise,
                metrics={
                    "issue": "Face not visible. Please face the camera so I can see you."
                },
            )
            
            if result and not st.session_state.get("audio_to_play"):
                audio, feedback = result
                print(f"🔊 FACE NOT VISIBLE: {feedback}")
                st.session_state.audio_to_play = audio
                st.session_state.coach_feedback = feedback
                st.session_state.last_face_notification = now

    # ==========================
    # NO POSE DETECTED
    # ==========================
    pose_detected = latest_metrics.get("pose_detected", True)
    last_pose_notification = st.session_state.get("last_pose_notification", 0)
    
    if (not pose_detected and 
        st.session_state.get("voice_pipeline") and 
        now - last_pose_notification > 8):
        
        if face_visible and not pose_detected:
            issue_text = "I can see your face but not your full body. Please step back so I can see your whole body for pose detection."
        else:
            issue_text = "No pose detected. Please step into the camera frame and make sure your full body is visible."
        
        result = st.session_state.voice_pipeline.process_event(
            event="no_pose_detected",
            exercise=exercise,
            metrics={"issue": issue_text},
        )
        
        if result and not st.session_state.get("audio_to_play"):
            audio, feedback = result
            print(f"🔊 NO POSE DETECTED: {feedback}")
            st.session_state.audio_to_play = audio
            st.session_state.coach_feedback = feedback
            st.session_state.last_pose_notification = now
        # Assuming 'tracker' is an instance of your PoseTracker class

        if result:
            voice, feedback_text = result
            if voice:
             autoplay_audio(voice)
            print("FEEDBACK:", feedback_text)
    # ==========================
    # WRONG EXERCISE CONTINUOUS CHECK (every 30 seconds if still wrong)
    # ==========================
    if detected_exercise and detected_exercise != selected_exercise:
        last_reminder = st.session_state.get("last_wrong_exercise_reminder", 0)
        if now - last_reminder > 30 and now - last_mismatch_notification > 20:
            if st.session_state.get("voice_pipeline"):
                result = st.session_state.voice_pipeline.process_event(
                    event="exercise_mismatch",
                    exercise=selected_exercise,
                    metrics=latest_metrics,
                    detected_exercise=detected_exercise,
                )
                if result and not st.session_state.get("audio_to_play"):
                    audio, feedback = result
                    print(f"🔊 REMINDER: {feedback}")
                    st.session_state.audio_to_play = audio
                    st.session_state.coach_feedback = feedback
                    st.session_state.last_wrong_exercise_reminder = now

    # ==========================
    # LIVE FORM CORRECTION
    # ==========================
    if st.session_state.get("voice_pipeline"):

        detected_exercise = latest_metrics.get("detected_exercise", None)
        
        result = st.session_state.voice_pipeline.process_event(
            event="ongoing_form_check",
            exercise=exercise,
            metrics=latest_metrics,
            detected_exercise=detected_exercise,
        )

        if (
            result
            and not st.session_state.get("audio_to_play")
        ):
            audio, feedback = result

            print(f"🔊 FORM CORRECTION: {feedback}")

            st.session_state.audio_to_play = audio
            st.session_state.coach_feedback = feedback