import os
import cv2
import av
import time
import numpy as np
import mediapipe as mp
import threading
import sys
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"
        self.last_exercise_check_time = 0
        self.detected_exercise = None
        
        # For exercise detection tracking
        self._last_arm_elevation = 0
        self._exercise_confidence = {}
        self._exercise_detection_counter = 0
        self._arm_movement_history = []
        self._knee_angle_history = []

        # FIX: Get the correct absolute path to the model
        # Get the directory where THIS file is located
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up 2 levels to reach project root (services/vision -> services -> project_root)
        project_root = os.path.dirname(os.path.dirname(current_file_dir))
        
        # Build the absolute path to the model
        model_path = os.path.join(project_root, "ml_models", "pose_landmarker_full.task")
        
        # Also try alternative locations
        alternative_paths = [
            model_path,
            os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task"),
            os.path.join(os.path.dirname(sys.argv[0]), "ml_models", "pose_landmarker_full.task"),
            "ml_models/pose_landmarker_full.task",
            "./ml_models/pose_landmarker_full.task"
        ]
        
        # Find the first existing path
        found_path = None
        for path in alternative_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path is None:
            error_msg = f"""
            ❌ ERROR: Pose landmarker model not found!
            
            Tried these paths:
            {chr(10).join(alternative_paths)}
            
            Please run: python download_model.py
            Or manually download the model from:
            https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task
            
            Save it to: {os.path.join(project_root, "ml_models", "pose_landmarker_full.task")}
            """
            print(error_msg)
            raise FileNotFoundError(error_msg)
        
        print(f"✅ Loading pose model from: {found_path}")
        
        # Use the found path
        base_option = python.BaseOptions(model_asset_path=found_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        
        # Initialize face detection
        self.face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
        }

        self._frame_timestamps_ms = 0
        self.frame_count = 0
    
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type
    
    def _calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        import math
        
        ab = [a.x - b.x, a.y - b.y]
        cb = [c.x - b.x, c.y - b.y]
        
        dot_product = ab[0]*cb[0] + ab[1]*cb[1]
        
        mag_ab = math.sqrt(ab[0]**2 + ab[1]**2)
        mag_cb = math.sqrt(cb[0]**2 + cb[1]**2)
        
        if mag_ab * mag_cb == 0:
            return 0
        
        angle = math.acos(dot_product / (mag_ab * mag_cb))
        return math.degrees(angle)
    
    def _detect_exercise_from_pose(self, landmarks):
        """Detect which exercise user is performing based on pose"""
        if not landmarks:
            return None
        
        try:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_elbow = landmarks[13]
            right_elbow = landmarks[14]
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            left_knee = landmarks[25]
            right_knee = landmarks[26]
            left_ankle = landmarks[27]
            right_ankle = landmarks[28]
            
            left_arm_angle = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_arm_angle = self._calculate_angle(right_shoulder, right_elbow, right_wrist)
            avg_arm_angle = (left_arm_angle + right_arm_angle) / 2
            
            left_arm_elevation = left_wrist.y - left_shoulder.y
            right_arm_elevation = right_wrist.y - right_shoulder.y
            avg_arm_elevation = (left_arm_elevation + right_arm_elevation) / 2
            
            self._arm_movement_history.append(avg_arm_elevation)
            if len(self._arm_movement_history) > 10:
                self._arm_movement_history.pop(0)
            
            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
            hip_y = (left_hip.y + right_hip.y) / 2
            knee_y = (left_knee.y + right_knee.y) / 2
            
            body_vertical_diff = abs(shoulder_y - hip_y)
            
            left_knee_angle = self._calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = self._calculate_angle(right_hip, right_knee, right_ankle)
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
            
            self._knee_angle_history.append(avg_knee_angle)
            if len(self._knee_angle_history) > 10:
                self._knee_angle_history.pop(0)
            
            # SHOULDER PRESS DETECTION
            if avg_arm_angle > 150 and avg_arm_elevation < -0.15:
                if len(self._arm_movement_history) > 5:
                    movement = self._arm_movement_history[-1] - self._arm_movement_history[0]
                    if movement < -0.05:
                        return "Shoulder Press"
                if avg_arm_elevation < -0.2:
                    return "Shoulder Press"
            
            # SQUAT DETECTION
            elif avg_knee_angle < 140 and knee_y > hip_y:
                if len(self._knee_angle_history) > 5:
                    knee_movement = self._knee_angle_history[-1] - self._knee_angle_history[0]
                    if knee_movement < -10:
                        return "Squats"
                if avg_knee_angle < 120:
                    return "Squats"
            
            # BICEPS CURL DETECTION
            elif 30 < avg_arm_angle < 120 and shoulder_y > hip_y:
                avg_wrist_x = (left_wrist.x + right_wrist.x) / 2
                avg_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
                if abs(avg_wrist_x - avg_shoulder_x) < 0.3:
                    return "Biceps Curls (Dumbbell)"
            
            # PUSH-UP DETECTION
            elif body_vertical_diff < 0.12 and shoulder_y > 0.4 and hip_y > 0.4:
                return "Push-ups"
            
            # LUNGE DETECTION
            elif abs(left_knee.y - right_knee.y) > 0.12:
                return "Lunges"
            
        except Exception as e:
            print(f"Error detecting exercise: {e}")
            
        return None
    
    def _get_exercise_with_confidence(self, landmarks):
        """Get exercise with confidence score over multiple frames"""
        detected = self._detect_exercise_from_pose(landmarks)
        
        if detected:
            self._exercise_confidence[detected] = self._exercise_confidence.get(detected, 0) + 1
            for ex in list(self._exercise_confidence.keys()):
                if ex != detected:
                    self._exercise_confidence[ex] = self._exercise_confidence.get(ex, 0) - 1
                    if self._exercise_confidence[ex] <= 0:
                        del self._exercise_confidence[ex]
        else:
            for ex in list(self._exercise_confidence.keys()):
                self._exercise_confidence[ex] -= 1
                if self._exercise_confidence[ex] <= 0:
                    del self._exercise_confidence[ex]
        
        self._exercise_detection_counter += 1
        if self._exercise_detection_counter > 15:
            if self._exercise_confidence:
                best_exercise = max(self._exercise_confidence, key=self._exercise_confidence.get)
                if self._exercise_confidence[best_exercise] > 8:
                    return best_exercise
        
        return None

    def _check_face_visibility(self, image):
        """Check if face is visible in the frame"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_image)
            
            if results.detections:
                return True, len(results.detections)
            return False, 0
        except Exception as e:
            print(f"Face detection error: {e}")
            return False, 0

    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.5 and p2.visibility > 0.5:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 255, 0),
                    4
                )
        
        for lm in landmarks:
            if lm.visibility > 0.5:
                cv2.circle(
                    img, 
                    (int(lm.x * w), int(lm.y * h)),
                    5,
                    (255, 0, 0),
                    -1
                )
    
    def _draw_exercise_mismatch_warning(self, img, selected, detected):
        """Draw warning when exercise mismatch detected"""
        h, w = img.shape[:2]
        cv2.rectangle(img, (5, h - 90), (w - 5, h - 10), (0, 0, 255), -1)
        cv2.putText(
            img,
            f"MISMATCH: Doing {detected} but selected {selected}",
            (10, h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
            
    def _draw_no_pose_warnings(self, img):
        h, w = img.shape[:2]
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
    
    def _draw_face_warning(self, img):
        """Draw warning when face not visible"""
        h, w = img.shape[:2]
        cv2.putText(
            img,
            "FACE NOT VISIBLE",
            (30, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            "PLEASE LOOK AT CAMERA",
            (30, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        if ex_type == "Squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Biceps Curls (Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunge_overlays(img, metrics)

    def _draw_squats_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        cv2.putText(
            img,
            f"DEPTH: {metrics.get('depth_status', 'N/A')}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
    
    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        cv2.putText(
            img,
            f"BODY: {metrics.get('body_alignment', 'N/A')} | HIP: {metrics.get('hip_status', 'N/A')}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        cv2.putText(
            img,
            f"SWING: {metrics.get('swing_status', 'N/A')}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        cv2.putText(
            img,
            f"EXT: {metrics.get('extension_status', 'N/A')} | BACK: {metrics.get('back_arch_status', 'N/A')}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        cv2.putText(
            img,
            f"BALANCE: {metrics.get('balance_status', 'N/A')}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )
        
        face_visible, face_count = self._check_face_visibility(image)
        
        if not face_visible:
            self._draw_face_warning(image)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            self._draw_skeleton(image, landmarks)

            ex_type = self.get_exercise()

            detector = self._detectors.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True
                metrics["face_visible"] = face_visible
                metrics["face_count"] = face_count
                
                current_time = time.time()
                if current_time - self.last_exercise_check_time > 0.5:
                    detected_ex = self._get_exercise_with_confidence(landmarks)
                    if detected_ex:
                        self.detected_exercise = detected_ex
                        metrics["detected_exercise"] = self.detected_exercise
                        
                        if self.detected_exercise != ex_type:
                            self._draw_exercise_mismatch_warning(image, ex_type, self.detected_exercise)
                    
                    self.last_exercise_check_time = current_time
                else:
                    if self.detected_exercise:
                        metrics["detected_exercise"] = self.detected_exercise
                        if self.detected_exercise != ex_type:
                            self._draw_exercise_mismatch_warning(image, ex_type, self.detected_exercise)

                self._draw_overlays(image, metrics, ex_type)

                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warnings(image)
            
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                    self._latest_metrics["face_visible"] = face_visible
                else:
                    self._latest_metrics = {"pose_detected": False, "face_visible": face_visible}
        
        self.frame_count += 1
        return av.VideoFrame.from_ndarray(image, format="bgr24")