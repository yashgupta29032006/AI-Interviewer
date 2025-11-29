import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QComboBox, QStackedWidget, QMessageBox, QProgressBar,
                             QDialog, QFormLayout, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QImage, QPixmap
import cv2
import mss
import numpy as np
import speech_recognition as sr
import pyttsx3
import threading
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
from textblob import TextBlob
import time
import random
import queue
import subprocess
import platform
import os
from dotenv import set_key

from interview_engine import InterviewEngine
from code_executor import CodeExecutor

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        layout = QFormLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Gemini", "OpenAI"])
        current_provider = os.getenv("LLM_PROVIDER", "gemini").title()
        self.provider_combo.setCurrentText(current_provider)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API Key")
        
        # Pre-fill if exists
        if current_provider.lower() == "gemini":
            self.api_key_input.setText(os.getenv("GEMINI_API_KEY", ""))
        else:
            self.api_key_input.setText(os.getenv("OPENAI_API_KEY", ""))
            
        layout.addRow("LLM Provider:", self.provider_combo)
        layout.addRow("API Key:", self.api_key_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
        
        self.provider_combo.currentTextChanged.connect(self.update_key_placeholder)

    def update_key_placeholder(self, text):
        if text.lower() == "gemini":
            self.api_key_input.setText(os.getenv("GEMINI_API_KEY", ""))
        else:
            self.api_key_input.setText(os.getenv("OPENAI_API_KEY", ""))

    def save_settings(self):
        provider = self.provider_combo.currentText().lower()
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Missing Key", "Please enter an API Key.")
            return

        env_path = os.path.join(os.getcwd(), ".env")
        
        # Save to .env
        try:
            set_key(env_path, "LLM_PROVIDER", provider)
            if provider == "gemini":
                set_key(env_path, "GEMINI_API_KEY", api_key)
            else:
                set_key(env_path, "OPENAI_API_KEY", api_key)
                
            QMessageBox.information(self, "Success", "Settings saved! Restart may be required for full effect.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

class TTSThread(QThread):
    started_speaking = pyqtSignal()
    finished_speaking = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.running = True

    def run(self):
        # pyttsx3 can be unstable in threads on macOS. 
        # Using system 'say' command is much more robust.
        is_mac = platform.system() == 'Darwin'
        
        if not is_mac:
            engine = pyttsx3.init()
        
        while self.running:
            try:
                text = self.queue.get(timeout=1)
                if text is None:
                    break
                
                self.started_speaking.emit()
                
                if is_mac:
                    # macOS native TTS
                    subprocess.run(['say', text])
                else:
                    # Windows/Linux fallback
                    engine.say(text)
                    engine.runAndWait()
                    
                self.finished_speaking.emit()
                
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS Error: {e}")

    def speak(self, text):
        self.queue.put(text)

    def stop(self):
        self.running = False
        self.wait()

class ListenerThread(QThread):
    text_recognized = pyqtSignal(str, float, int) # text, wpm, filler_count
    
    def __init__(self):
        super().__init__()
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def run(self):
        self.running = True
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            
        while self.running:
            try:
                with mic as source:
                    start_time = time.time()
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    end_time = time.time()
                
                if self.paused:
                    continue

                text = recognizer.recognize_google(audio)
                if text:
                    # Calculate WPM
                    duration = end_time - start_time
                    words = len(text.split())
                    wpm = (words / duration) * 60 if duration > 0 else 0
                    
                    # Count Fillers
                    fillers = ["um", "uh", "like", "you know", "actually", "basically"]
                    filler_count = sum(text.lower().count(f) for f in fillers)
                    
                    self.text_recognized.emit(text, wpm, filler_count)
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Listener Error: {e}")
                
    def stop(self):
        self.running = False
        self.wait()

class CameraThread(QThread):
    frame_captured = pyqtSignal(QImage)
    warning_signal = pyqtSignal(str)
    behavior_signal = pyqtSignal(dict) # {looking_away: bool, eyes_closed: bool}

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)
        
        if MEDIAPIPE_AVAILABLE:
            mp_face_mesh = mp.solutions.face_mesh
            face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                looking_away = False
                h, w, _ = frame.shape

                if MEDIAPIPE_AVAILABLE:
                    results = face_mesh.process(rgb_frame)
                    
                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            # Simple Head Pose Estimation (Nose tip vs ears/eyes)
                            # This is a simplified heuristic. Real pose estimation requires PnP.
                            nose_tip = face_landmarks.landmark[1]
                            nose_x = nose_tip.x * w
                            
                            # Check if nose is too far left or right (looking away)
                            if nose_x < w * 0.3 or nose_x > w * 0.7:
                                looking_away = True
                                
                            # Draw mesh (optional, maybe just landmarks)
                            # mp.solutions.drawing_utils.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_TESSELATION)

                if looking_away:
                    self.warning_signal.emit("Please maintain eye contact.")
                    cv2.putText(frame, "LOOKING AWAY", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    self.warning_signal.emit("")
                
                self.behavior_signal.emit({"looking_away": looking_away})

                # Convert to QImage
                qt_image = QImage(rgb_frame.data, w, h, w*3, QImage.Format.Format_RGB888)
                self.frame_captured.emit(qt_image)
            self.msleep(30)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

class ScreenCaptureThread(QThread):
    def run(self):
        self.running = True
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]
            while self.running:
                # Just capture for now to simulate monitoring
                sct.grab(monitor)
                # In a real app, we would process or save this
                self.msleep(2000) # Capture every 2 seconds

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Mock Interviewer - Video Call Mode")
        self.resize(1280, 800)
        
        self.engine = InterviewEngine()
        self.executor = CodeExecutor()
        self.camera_thread = None
        self.screen_thread = None
        self.listener_thread = None
        
        # TTS Thread (Persistent)
        self.tts_thread = TTSThread()
        self.tts_thread.started_speaking.connect(self.start_speaking_animation)
        self.tts_thread.finished_speaking.connect(self.stop_speaking_animation)
        self.tts_thread.start()
        
        # Animation Timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_mouth)
        self.is_speaking = False
        
        # Preload Avatar Images
        self.avatar_images = {}
        for name in ["neutral", "open", "o", "wide"]:
            path = f"assets/avatar_{name}.png" if name != "neutral" else "assets/avatar.png"
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.avatar_images[name] = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Setup UI
        # Setup UI
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        self.init_welcome_screen()
        self.init_interview_screen()
        self.init_summary_screen()
        
        self.central_widget.setCurrentWidget(self.welcome_widget)
        
        self.apply_styles()
        
    def apply_styles(self):
        # Dark Theme with Glassmorphism feel
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444444;
                border-color: #007acc;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                border-radius: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 10px;
            }
            QComboBox {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 5px;
            }
        """)

    def init_welcome_screen(self):
        self.welcome_widget = QWidget()
        self.resume_path = None # Store selected resume path
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("AI Mock Interviewer")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Select a domain to start your interview")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(["Python", "DSA", "OOP", "DBMS", "OS", "HR"])
        self.domain_combo.setFixedWidth(200)
        
        start_btn = QPushButton("Start Interview")
        start_btn.setFixedWidth(200)
        start_btn.clicked.connect(self.start_interview)
        
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedWidth(200)
        settings_btn.setStyleSheet("background-color: #555; border: 1px solid #777;")
        settings_btn.clicked.connect(self.open_settings)

        self.upload_btn = QPushButton("Upload Resume (PDF)")
        self.upload_btn.setFixedWidth(200)
        self.upload_btn.setStyleSheet("background-color: #0078d7; border: 1px solid #005a9e;")
        self.upload_btn.clicked.connect(self.upload_resume)
        
        self.resume_label = QLabel("No resume uploaded")
        self.resume_label.setStyleSheet("color: #aaa; font-size: 12px;")
        self.resume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.domain_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.resume_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.welcome_widget.setLayout(layout)
        self.central_widget.addWidget(self.welcome_widget)

    def upload_resume(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Resume", "", "PDF Files (*.pdf)")
        if file_path:
            self.resume_path = file_path
            self.resume_label.setText(f"Uploaded: {os.path.basename(file_path)}")
            self.resume_label.setStyleSheet("color: #4caf50; font-size: 12px;")

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload engine to pick up new key
            self.engine.llm._setup_client()
            self.engine.use_llm = self.engine.llm.is_configured()

    def init_interview_screen(self):
        self.interview_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Left: Main Video Area (AI Avatar + User PIP) ---
        video_area = QWidget()
        video_area.setStyleSheet("background-color: #000000;")
        video_layout = QVBoxLayout(video_area)
        
        # AI Avatar
        self.ai_avatar = QLabel()
        self.ai_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load Avatar Image
        avatar_path = "assets/avatar.png"
        try:
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                # Scale to a reasonable size, e.g., 400x400 or fit the area
                self.ai_avatar.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.ai_avatar.setText("AI Interviewer")
                self.ai_avatar.setFont(QFont("Segoe UI", 24))
                self.ai_avatar.setStyleSheet("color: #555;")
        except Exception as e:
            print(f"Error loading avatar: {e}")
            self.ai_avatar.setText("AI Interviewer")
            self.ai_avatar.setFont(QFont("Segoe UI", 24))
            self.ai_avatar.setStyleSheet("color: #555;")
        
        # User PIP (Overlay logic is hard in simple layouts, so we'll stack or place it)
        # For simplicity in this iteration, we place PIP at top-left of this area
        self.camera_label = QLabel("Camera")
        self.camera_label.setFixedSize(240, 180)
        self.camera_label.setScaledContents(True)
        self.camera_label.setStyleSheet("background-color: #222; border: 2px solid #444; border-radius: 10px;")
        
        # Warning Label
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-weight: bold; background-color: rgba(0,0,0,0.7); padding: 5px; border-radius: 5px;")
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_label.hide()

        # Layout for Video Area
        # We use a grid or stack to simulate overlay, but VBox is safer for now
        # Let's put camera on top of AI for now (vertical stack)
        video_layout.addWidget(self.camera_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        video_layout.addWidget(self.warning_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        video_layout.addStretch()
        video_layout.addWidget(self.ai_avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        video_layout.addStretch()
        
        # Bottom Controls
        controls_layout = QHBoxLayout()
        self.mute_btn = QPushButton("Mute Mic")
        self.end_call_btn = QPushButton("End Interview")
        self.end_call_btn.setStyleSheet("background-color: #d32f2f; border: none;")
        self.end_call_btn.clicked.connect(self.show_summary)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.mute_btn)
        controls_layout.addWidget(self.end_call_btn)
        controls_layout.addStretch()
        
        video_layout.addLayout(controls_layout)
        
        # --- Right: Transcript & Interaction ---
        sidebar = QWidget()
        sidebar.setFixedWidth(400)
        sidebar.setStyleSheet("background-color: #1e1e1e; border-left: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Header
        self.progress_label = QLabel("Question 1/5")
        self.difficulty_label = QLabel("Medium")
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.progress_label)
        header_layout.addStretch()
        header_layout.addWidget(self.difficulty_label)
        
        # Chat History (Transcript)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Interview transcript will appear here...")
        
        # Current Question (also spoken)
        self.current_q_label = QLabel("...")
        self.current_q_label.setWordWrap(True)
        self.current_q_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        
        # Answer Input (for corrections or coding)
        self.answer_input = QTextEdit()
        self.answer_input.setPlaceholderText("Speak your answer or type here...")
        self.answer_input.setFixedHeight(100)
        
        # Code Output Console (Hidden by default)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setPlaceholderText("Code output will appear here...")
        self.console_output.setStyleSheet("background-color: #000; color: #0f0; font-family: 'Courier New'; font-size: 12px;")
        self.console_output.setFixedHeight(100)
        self.console_output.hide()
        
        # Buttons Layout
        btn_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Run Code")
        self.run_btn.setStyleSheet("background-color: #2e7d32; border: none;")
        self.run_btn.clicked.connect(self.run_code)
        self.run_btn.hide()
        
        self.submit_btn = QPushButton("Submit Answer")
        self.submit_btn.clicked.connect(self.submit_answer)
        
        self.next_btn = QPushButton("Next Question")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.hide()
        
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.next_btn)
        
        sidebar_layout.addLayout(header_layout)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(QLabel("Current Question:"))
        sidebar_layout.addWidget(self.current_q_label)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(self.chat_history)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(self.answer_input)
        sidebar_layout.addWidget(self.console_output)
        sidebar_layout.addLayout(btn_layout)
        
        main_layout.addWidget(video_area)
        main_layout.addWidget(sidebar)
        
        self.interview_widget.setLayout(main_layout)
        self.central_widget.addWidget(self.interview_widget)

    def init_summary_screen(self):
        self.summary_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Interview Completed")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        
        self.score_label = QLabel("Score: 0/100")
        self.score_label.setFont(QFont("Segoe UI", 20))
        
        self.verdict_label = QLabel("Verdict: Passed")
        self.verdict_label.setFont(QFont("Segoe UI", 16))
        
        restart_btn = QPushButton("Back to Home")
        restart_btn.clicked.connect(self.reset_app)
        
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.score_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.verdict_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(restart_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.summary_widget.setLayout(layout)
        self.central_widget.addWidget(self.summary_widget)

    def start_interview(self):
        domain = self.domain_combo.currentText()
        self.current_question_count = 0
        
        # Start engine (pass resume path if selected)
        question = self.engine.start_interview(domain, self.resume_path)
        
        if question:
            self.update_question_ui(question)
        self.central_widget.setCurrentWidget(self.interview_widget)
        
        # Start Monitoring
        self.start_monitoring()
        
        # Start Listener
        self.listener_thread = ListenerThread()
        self.listener_thread.text_recognized.connect(self.on_speech_recognized)
        self.listener_thread.start()

    def start_monitoring(self):
        # Camera
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self.update_camera_feed)
        self.camera_thread.warning_signal.connect(self.update_warning)
        self.camera_thread.start()
        
        # Screen
        self.screen_thread = ScreenCaptureThread()
        self.screen_thread.start()

    def stop_monitoring(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        if self.screen_thread:
            self.screen_thread.stop()
            self.screen_thread = None
        if self.listener_thread:
            self.listener_thread.stop()
            self.listener_thread = None
        if self.tts_thread:
            self.tts_thread.stop()

    def update_camera_feed(self, image):
        self.camera_label.setPixmap(QPixmap.fromImage(image))

    def update_warning(self, message):
        if message:
            self.warning_label.setText(message)
            self.warning_label.show()
            self.camera_label.setStyleSheet("background-color: #222; border: 3px solid red; border-radius: 10px;")
        else:
            self.warning_label.hide()
            self.camera_label.setStyleSheet("background-color: #222; border: 2px solid #444; border-radius: 10px;")

    def on_speech_recognized(self, text, wpm, filler_count):
        current_text = self.answer_input.toPlainText()
        if current_text:
            new_text = current_text + " " + text
        else:
            new_text = text
        self.answer_input.setText(new_text)
        
        # Store metrics for submission
        self.last_wpm = wpm
        self.last_fillers = filler_count

    def speak_text(self, text):
        self.tts_thread.speak(text)

    def start_speaking_animation(self):
        self.is_speaking = True
        if self.listener_thread:
            self.listener_thread.pause()
        self.animate_mouth() # Start immediately

    def stop_speaking_animation(self):
        self.is_speaking = False
        self.animation_timer.stop()
        self.set_avatar_pixmap("neutral")
        if self.listener_thread:
            self.listener_thread.resume()

    def animate_mouth(self):
        if not self.is_speaking:
            return

        # Randomly select a mouth shape
        # higher weight for open shapes during speech
        shapes = ["open", "o", "wide", "neutral"]
        weights = [0.4, 0.3, 0.2, 0.1] 
        choice = random.choices(shapes, weights=weights, k=1)[0]
        
        self.set_avatar_pixmap(choice)
        
        # Random interval for next frame (fast for chatter effect)
        interval = random.randint(50, 120)
        self.animation_timer.start(interval)

    def set_avatar_pixmap(self, name):
        if name in self.avatar_images:
            self.ai_avatar.setPixmap(self.avatar_images[name])

    def update_question_ui(self, question):
        if not question:
            self.show_summary()
            return
            
        self.current_q_label.setText(question['text'])
        self.chat_history.append(f"<b>AI:</b> {question['text']}")
        self.speak_text(question['text'])
        
        self.answer_input.clear()
        self.console_output.clear()
        self.console_output.hide()
        
        self.next_btn.hide()
        self.submit_btn.show()
        self.submit_btn.setEnabled(True)
        self.answer_input.setReadOnly(False)
        
        # Show Run button only for coding questions
        if question.get('type') == 'coding':
            self.run_btn.show()
            self.console_output.show()
            self.answer_input.setPlaceholderText("Type your Python code here...")
            # Pre-fill function signature if available
            if 'function_name' in question:
                self.answer_input.setText(f"def {question['function_name']}(...):\n    pass")
        else:
            self.run_btn.hide()
            self.answer_input.setPlaceholderText("Speak your answer or type here...")
        
        self.progress_label.setText(f"Question {self.engine.questions_asked}/{self.engine.max_questions}")
        self.difficulty_label.setText(f"Difficulty: {self.engine.difficulty.capitalize()}")

    def run_code(self):
        code = self.answer_input.toPlainText()
        question = self.engine.current_question
        
        if not code.strip():
            return
            
        self.console_output.setText("Running...")
        QApplication.processEvents()
        
        function_name = question.get('function_name', 'solution')
        test_cases = question.get('test_cases', [])
        
        result = self.executor.run_code(code, function_name, test_cases)
        
        if result['success']:
            self.console_output.setText(f"Execution Successful:\n{result['output']}")
            self.console_output.setStyleSheet("background-color: #000; color: #0f0; font-family: 'Courier New'; font-size: 12px;")
        else:
            self.console_output.setText(f"Execution Failed:\n{result['errors']}\nOutput:\n{result['output']}")
            self.console_output.setStyleSheet("background-color: #000; color: #f00; font-family: 'Courier New'; font-size: 12px;")

    def submit_answer(self):
        answer = self.answer_input.toPlainText()
        if not answer.strip():
            QMessageBox.warning(self, "Warning", "Please enter an answer.")
            return
            
        self.chat_history.append(f"<b>You:</b> {answer}")
        
        # Get metrics
        wpm = getattr(self, 'last_wpm', 0)
        fillers = getattr(self, 'last_fillers', 0)
        
        result = self.engine.submit_answer(answer, wpm, fillers)
        
        # Feedback
        feedback_text = f"Score: {result.get('score', 'N/A')}. {result.get('feedback', '')}"
        self.chat_history.append(f"<i>AI Feedback: {feedback_text}</i>")
        self.speak_text(result.get('feedback', ''))
        
        if 'analysis' in result and result['analysis'].get('follow_ups'):
            follow_ups = "\n".join(["- " + f for f in result['analysis']['follow_ups'][:2]])
            self.chat_history.append(f"<i>Follow-ups:</i>\n{follow_ups}")
            
        self.submit_btn.hide()
        self.run_btn.hide()
        self.next_btn.show()
        self.answer_input.setReadOnly(True)

    def next_question(self):
        question = self.engine.get_next_question()
        self.update_question_ui(question)

    def show_summary(self):
        self.stop_monitoring()
        summary = self.engine.get_summary()
        self.score_label.setText(f"Total Score: {summary['total_score']} (Avg: {summary['average_score']:.1f})")
        self.verdict_label.setText(f"Verdict: {summary['verdict']}")
        self.central_widget.setCurrentWidget(self.summary_widget)

    def reset_app(self):
        self.stop_monitoring()
        self.central_widget.setCurrentWidget(self.welcome_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
