import time
import random
import streamlit as st
from collections import deque
from datetime import datetime


def autoplay_audio(audio_bytes):
    """Helper function to autoplay audio in Streamlit"""
    if not audio_bytes:
        return
    
    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self.last_reps_announcement = 0
        self.reps_announcement_interval = 3
        self.last_reminder_time = 0
        self.reminder_interval = 30
        
        # New features for real coach experience
        self.performance_history = deque(maxlen=50)
        self.streak_counter = 0
        self.bad_form_counter = 0
        self.encouragement_cooldown = 0
        self.last_major_milestone = 0
        self.user_name = None
        self.workout_start_time = None
        self.personal_bests = {}
        
        # Motivational phrases pool
        self.encouragements = [
            "Great form! Keep it up!",
            "You're crushing it!",
            "Looking strong!",
            "Perfect technique!",
            "That's how it's done!",
            "Beautiful rep!",
            "You're on fire today!",
            "Excellent control!"
        ]
        
        self.form_corrections = {
            "gentle": [
                "Try to {correction}, you've got this!",
                "A small adjustment: {correction}",
                "Let's {correction}, the rest looks good!",
                "Focus on {correction}, everything else is perfect!"
            ],
            "direct": [
                "Remember to {correction}",
                "Keep {correction}",
                "Focus on {correction}",
                "Make sure you {correction}"
            ]
        }
        
        self.celebration_phrases = [
            "Yes! That's a personal best!",
            "Incredible work! New record!",
            "You're getting stronger every day!",
            "That's what I'm talking about!",
            "Unbelievable set! Keep pushing!"
        ]
        
        self.encouragement_after_correction = [
            "Much better!",
            "That's the way!",
            "Perfect adjustment!",
            "Great correction!"
        ]

    def set_user_name(self, name):
        """Set user's name for personalized coaching"""
        self.user_name = name

    def _get_personalized_greeting(self):
        """Return personalized greeting based on time of day"""
        hour = datetime.now().hour
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        if self.user_name:
            return f"{time_greeting}, {self.user_name}! Ready to crush your workout?"
        return f"{time_greeting}! Ready to crush your workout?"

    def _track_performance(self, metrics, exercise):
        """Track form quality over time for trend analysis"""
        form_quality = self._calculate_form_quality(metrics, exercise)
        self.performance_history.append({
            'timestamp': time.time(),
            'quality': form_quality,
            'exercise': exercise,
            'reps': metrics.get('reps', 0)
        })
        
        # Update streaks
        if form_quality > 0.8:
            self.streak_counter += 1
            self.bad_form_counter = 0
        elif form_quality < 0.5:
            self.bad_form_counter += 1
            self.streak_counter = 0
        else:
            self.streak_counter = 0
            self.bad_form_counter = 0
            
        return form_quality

    def _calculate_form_quality(self, metrics, exercise):
        """Calculate form quality score (0-1)"""
        quality_score = 1.0
        
        if exercise == "Squats":
            if metrics.get("depth_status") == "TOO HIGH":
                quality_score -= 0.4
            back_angle = metrics.get("back_angle", 180)
            if isinstance(back_angle, (int, float)) and back_angle < 130:
                quality_score -= 0.3
                
        elif exercise == "Push-ups":
            if metrics.get("body_alignment") == "Poor Form":
                quality_score -= 0.4
            if metrics.get("hip_status") in ["SAGGING", "PIKED UP"]:
                quality_score -= 0.3
                
        elif exercise == "Biceps Curls (Dumbbell)":
            if metrics.get("swing_status") == "SWINGING":
                quality_score -= 0.4
            if metrics.get("shoulder_status") == "ELBOW DRIFTING":
                quality_score -= 0.3
                
        return max(0, quality_score)

    def _check_personal_best(self, metrics, exercise):
        """Check if user achieved a personal best"""
        current_reps = metrics.get('reps', 0)
        exercise_key = f"{exercise}_max_reps"
        
        if exercise_key not in self.personal_bests:
            self.personal_bests[exercise_key] = current_reps
            return False
            
        if current_reps > self.personal_bests[exercise_key]:
            self.personal_bests[exercise_key] = current_reps
            return True
            
        return False

    def _get_improvement_suggestion(self, exercise):
        """Provide specific improvement suggestions based on history"""
        if len(self.performance_history) < 5:
            return None
            
        recent_scores = [h['quality'] for h in self.performance_history if h['exercise'] == exercise]
        if not recent_scores:
            return None
            
        avg_recent = sum(recent_scores[-5:]) / 5
        avg_older = sum(recent_scores[:-5]) / max(1, len(recent_scores)-5) if len(recent_scores) > 5 else avg_recent
        
        if avg_recent < avg_older - 0.2:
            if exercise == "Squats":
                return "Your form is declining. Let's focus on depth and keeping your chest up."
            elif exercise == "Push-ups":
                return "I'm noticing fatigue affecting your form. Focus on keeping your body straight."
            elif exercise == "Biceps Curls":
                return "You might be getting tired. Consider slowing down and focusing on form."
                
        return None

    def _get_encouragement(self, form_quality, consecutive_bad_form):
        """Get context-aware encouragement"""
        if self.encouragement_cooldown > time.time():
            return None
            
        if self.streak_counter >= 5:
            self.encouragement_cooldown = time.time() + 15
            return "5 reps with perfect form! You're on a roll!"
            
        if self.streak_counter >= 3:
            self.encouragement_cooldown = time.time() + 10
            return random.choice(["Great streak! Keep it up!", "Perfect form continues! Excellent!"])
        
        if consecutive_bad_form == 2:
            self.encouragement_cooldown = time.time() + 5
            return "Let's focus on form for this next rep. You've got this!"
            
        if consecutive_bad_form >= 3:
            self.encouragement_cooldown = time.time() + 8
            return "Take a breath and reset. Quality over quantity. Let's fix the form."
        
        if form_quality > 0.9:
            self.encouragement_cooldown = time.time() + random.randint(20, 40)
            return random.choice(self.encouragements)
            
        return None

    def _get_workout_summary(self, duration, total_reps, avg_form_quality):
        """Generate personalized workout summary"""
        if self.user_name:
            summary = f"Great workout today, {self.user_name}! "
        else:
            summary = "Great workout today! "
            
        summary += f"You completed {total_reps} reps in {int(duration//60)} minutes and {int(duration%60)} seconds. "
        
        if avg_form_quality > 0.9:
            summary += "Your form was absolutely exceptional!"
        elif avg_form_quality > 0.7:
            summary += "Your form was solid overall. Keep practicing!"
        else:
            summary += "Focus on form next time. Quality matters more than quantity."
            
        if self.streak_counter >= 10:
            summary += f" Plus, you had an impressive {self.streak_counter} rep streak of perfect form!"
            
        return summary

    def _find_form_issue(self, exercise, metrics):
        """Enhanced form issue detection with more specific feedback"""
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            
            if depth == "TOO HIGH":
                return "lower your hips and go deeper into the squat"

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "keep your chest up and back straight"

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            
            if alignment == "Poor Form":
                return "keep your body in a straight line from head to heels"

            if hip_status == "SAGGING":
                return "engage your core to prevent your hips from sagging"

            if hip_status == "PIKED UP":
                return "lower your hips to form a straight line"

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            
            if swing == "SWINGING":
                return "keep your upper body still and avoid swinging"

            if shoulder == "ELBOW DRIFTING":
                return "keep your elbows pinned to your sides"

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            
            if back_arch == "Excessive Arch":
                return "brace your core to prevent back arching"

            if back_arch == "Slight Arch":
                return "keep your core tight"

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            
            if balance == "OFF BALANCE":
                return "keep your feet hip-width apart for better balance"

        return None

    def _announce_reps_remaining(self, metrics, exercise):
        """Announce remaining reps with motivation"""
        reps = metrics.get("reps", 0)
        reps_per_set = metrics.get("reps_per_set", 0)
        
        if reps_per_set > 0 and reps > 0:
            reps_completed_in_set = reps % reps_per_set
            if reps_completed_in_set == 0:
                reps_completed_in_set = reps_per_set
            
            reps_remaining = reps_per_set - reps_completed_in_set
            
            if reps_remaining in [1, 3, 5] and reps_remaining != self.last_reps_announcement:
                self.last_reps_announcement = reps_remaining
                
                if reps_remaining == 1:
                    return "Last rep of the set! Push through!"
                elif reps_remaining == 3:
                    return "Halfway through the set! Keep the form tight!"
                else:
                    return f"{reps_remaining} reps remaining. You've got this!"
        
        return None

    def _get_reminder_text(self, exercise):
        """Get periodic reminder with variety"""
        reminders = {
            "Squats": [
                "Remember: chest up, weight on heels, go deep.",
                "Keep your knees tracking over your toes.",
                "Drive through your heels on the way up."
            ],
            "Push-ups": [
                "Keep your core tight and body straight.",
                "Lower yourself with control, then explode up.",
                "Imagine squeezing a pencil between your shoulder blades."
            ],
            "Biceps Curls (Dumbbell)": [
                "Keep those elbows pinned to your sides.",
                "Don't swing - slow and controlled is better.",
                "Squeeze your biceps at the top of the movement."
            ],
            "Shoulder Press": [
                "Keep your core braced and don't arch your back.",
                "Drive the weight straight up, not forward.",
                "Control the descent - don't drop the weight."
            ],
            "Lunges": [
                "Keep your front knee over your ankle.",
                "Engage your core for better balance.",
                "Lower until both knees form 90 degree angles."
            ]
        }
        
        exercise_reminders = reminders.get(exercise, ["Keep up the good form!"])
        return random.choice(exercise_reminders)

    def process_event(self, event, exercise, metrics, detected_exercise=None):
        now = time.time()
        
        if event in ["ongoing_form_check", "rep_completed"]:
            form_quality = self._track_performance(metrics, exercise)
        else:
            form_quality = 1.0

        # ========== WORKOUT START ==========
        if event == "workout_started":
            self.workout_start_time = now
            self.performance_history.clear()
            self.streak_counter = 0
            text = self._get_personalized_greeting()
            
            tips = {
                "Squats": " Remember to keep your chest up and go deep.",
                "Push-ups": " Keep your body straight and core tight.",
                "Biceps Curls (Dumbbell)": " Keep your elbows pinned to your sides.",
                "Shoulder Press": " Keep your core braced and back straight.",
                "Lunges": " Keep your front knee over your ankle."
            }
            text += tips.get(exercise, " Let's focus on good form!")
            
            voice = self.tts.speak(text)
            self.last_spoken_at = now
            return voice, text

        # ========== WORKOUT COMPLETED ==========
        elif event == "workout_completed":
            if self.workout_start_time:
                duration = now - self.workout_start_time
                total_reps = metrics.get('reps', 0)
                avg_form_quality = sum([h['quality'] for h in self.performance_history]) / max(1, len(self.performance_history))
                
                text = self._get_workout_summary(duration, total_reps, avg_form_quality)
            else:
                text = "Workout completed. Excellent work today!"
                
            voice = self.tts.speak(text)
            self.last_spoken_at = now
            return voice, text

        # ========== SET COMPLETED ==========
        elif event == "set_completed":
            is_pr = self._check_personal_best(metrics, exercise)
            
            if is_pr:
                text = random.choice(self.celebration_phrases)
            else:
                text = "Set completed!"
                
                if self.streak_counter >= 3:
                    text += f" That's {self.streak_counter} great reps in a row!"
            
            voice = self.tts.speak(text)
            self.last_spoken_at = now
            return voice, text

        # ========== NO POSE DETECTED ==========
        # ========== NO POSE DETECTED ==========

        # ========== NO POSE DETECTED ==========
        elif event == "no_pose_detected":  # Or 'elif' if it follows another 'if'

            print("🔥 NO POSE DETECTED EVENT CALLED")

            text = metrics.get(
                "issue",
                "No body detected. Please step into the camera frame."
            )

            if "face" not in text.lower() and "full body" not in text.lower():
                text += " Make sure your full body is visible."

            voice = self.tts.speak(text)

            print("🔥 VOICE GENERATED:", voice is not None)

            self.last_spoken_at = now
            return voice, text

        

        # ========== EXERCISE MISMATCH ==========
        elif event == "exercise_mismatch":
            text = f"I notice you're doing {detected_exercise} but you selected {exercise}. Please check your form or select the correct exercise."
            voice = self.tts.speak(text)
            self.last_spoken_at = now
            return voice, text

        # ========== REPS ANNOUNCEMENT ==========
        elif event == "reps_announcement":
            reps_announcement = self._announce_reps_remaining(metrics, exercise)
            if reps_announcement:
                voice = self.tts.speak(reps_announcement)
                self.last_spoken_at = now
                return voice, reps_announcement
            return None

        # ========== ONGOING FORM CHECK ==========
        elif event == "ongoing_form_check":
            if detected_exercise and detected_exercise != exercise:
                return self.process_event("exercise_mismatch", exercise, metrics, detected_exercise)
            
            issue = self._find_form_issue(exercise, metrics)
            
            if issue:
                if now - self.last_spoken_at >= 5:
                    if self.bad_form_counter >= 3:
                        template = random.choice(self.form_corrections["direct"])
                        text = template.format(correction=issue)
                    else:
                        template = random.choice(self.form_corrections["gentle"])
                        text = template.format(correction=issue)
                    
                    voice = self.tts.speak(text)
                    self.last_spoken_at = now
                    return voice, text
            
            if now - self.last_spoken_at >= 15:
                improvement_tip = self._get_improvement_suggestion(exercise)
                if improvement_tip:
                    voice = self.tts.speak(improvement_tip)
                    self.last_spoken_at = now
                    return voice, improvement_tip
            
            encouragement = self._get_encouragement(form_quality, self.bad_form_counter)
            if encouragement and now - self.last_spoken_at >= 10:
                voice = self.tts.speak(encouragement)
                self.last_spoken_at = now
                return voice, encouragement
            
            if now - self.last_reminder_time >= self.reminder_interval:
                self.last_reminder_time = now
                reminder_text = self._get_reminder_text(exercise)
                if reminder_text:
                    voice = self.tts.speak(reminder_text)
                    self.last_spoken_at = now
                    return voice, reminder_text
            
            reps_announcement = self._announce_reps_remaining(metrics, exercise)
            if reps_announcement and now - self.last_spoken_at >= 3:
                voice = self.tts.speak(reps_announcement)
                self.last_spoken_at = now
                return voice, reps_announcement

        return None