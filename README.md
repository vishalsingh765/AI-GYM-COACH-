# 🏋️ AI Real-Time Gym Coach

An intelligent fitness coaching application that uses **Computer Vision**, **MediaPipe**, and **Streamlit** to provide real-time exercise tracking, posture analysis, rep counting, and voice-based feedback.

## 🚀 Features

### 🎯 Real-Time Exercise Detection

* Squats
* Push-Ups
* Biceps Curls
* Shoulder Press
* Lunges

### 📊 Performance Tracking

* Automatic repetition counting
* Set tracking
* Workout statistics
* Calories estimation
* Exercise history

### 🎥 Pose Estimation

* Real-time body landmark detection using MediaPipe
* Posture correction analysis
* Movement tracking and validation

### 🔊 AI Voice Coaching

* Live voice feedback during workouts
* Form correction alerts
* Motivation and guidance
* Safety reminders

### 👤 User Management

* Login system
* User workout history
* Personalized workout tracking

### 📈 Dashboard & Analytics

* Workout summaries
* Progress visualization
* Performance metrics
* Session reports

---

## 🛠️ Tech Stack

### Frontend

* Streamlit

### Computer Vision

* OpenCV
* MediaPipe

### Machine Learning / AI

* MediaPipe Pose Landmarker
* Groq API (AI-powered coaching)

### Database

* SQLite

### Additional Libraries

* Pandas
* NumPy
* gTTS
* Streamlit-WebRTC

---

## 📂 Project Structure

```text
AI-REAL-TIME-GYM-COACH-V2/
│
├── app.py
├── data.db
├── requirements.txt
│
├── detectors/
│   ├── squat.py
│   ├── pushup.py
│   ├── biceps_curl.py
│   ├── shoulder_press.py
│   └── lunges.py
│
├── ml_models/
│   └── pose_landmarker_full.task
│
├── pages/
│   ├── Dashboard.py
│   ├── Workout_History.py
│   └── Analytics.py
│
├── utils/
│   ├── database.py
│   ├── voice.py
│   └── metrics.py
│
└── assets/
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-REAL-TIME-GYM-COACH-V2.git

cd AI-REAL-TIME-GYM-COACH-V2
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
streamlit run app.py
```

---

## 📦 Requirements

```txt
streamlit==1.54.0
streamlit-webrtc==0.64.5
mediapipe==0.10.14
opencv-python-headless==4.10.0.84
pandas==2.2.3
groq>=0.12.0
gtts==2.5.3
python-dotenv==1.2.2
```

---

## 🎮 How It Works

1. Launch the application.
2. Select an exercise.
3. Enable your webcam.
4. Perform the exercise.
5. The system:

   * Detects body landmarks.
   * Analyzes posture.
   * Counts repetitions.
   * Tracks workout performance.
   * Provides voice coaching feedback.

---

## 📸 Screenshots

Add screenshots of:

* Home Page
* Real-Time Workout Tracking
* Dashboard
* Analytics Page
* Voice Coaching Interface

Example:

```md
![Home Page](screenshots/home.png)
![Workout Tracking](screenshots/workout.png)
```

---

## 🔮 Future Improvements

* Multi-person tracking
* Custom workout plans
* AI-generated fitness recommendations
* Diet and nutrition assistant
* Mobile application
* Cloud database integration
* Wearable device support

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push changes

```bash
git push origin feature-name
```

5. Create a Pull Request

---

## ⭐ Support

If you find this project useful, please consider giving it a ⭐ on GitHub.

---

## 👨‍💻 Author

**Vishal Singh**

Software Developer | AI & Computer Vision Enthusiast

GitHub: https://github.com/vishalsingh765
LinkedIn: https://www.linkedin.com/in/vishal-singh-ab2944294/

---


