# 🤖 AI Mock Interviewer

> **Your Personal AI-Powered Technical Interview Coach**

The **AI Mock Interviewer** is an advanced desktop application designed to simulate realistic technical interviews. It combines **Computer Vision**, **Speech Recognition**, and **Large Language Models (LLMs)** to provide a holistic interview experience. The system not only evaluates your technical correctness but also analyzes your behavioral cues, such as eye contact, speaking pace, and filler words.

## 🚀 Key Features

- **🧠 Intelligent Questioning**: Powered by **Google Gemini 1.5 Pro** (or GPT-4o), the AI acts as a "Senior Staff Engineer," asking rigorous, context-aware questions based on your resume and previous answers.
- **📄 Resume Parsing**: Upload your PDF resume, and the AI will tailor the interview to your specific skills and projects.
- **🗣️ Voice Interaction**:
  - **Text-to-Speech (TTS)**: The AI speaks questions with a synchronized animated avatar.
  - **Speech-to-Text (STT)**: Answer naturally with your voice. The system handles microphone feedback automatically.
- **👀 Behavioral Analysis**:
  - **Eye Contact Tracking**: Uses MediaPipe to warn you if you look away too often.
  - **Speech Metrics**: Tracks Words Per Minute (WPM) and filler words (e.g., "um", "uh").
- **💻 Live Coding Environment**: Integrated code editor to solve programming challenges. The code is executed safely, and the output is analyzed.
- **📊 Comprehensive Feedback**: Receive detailed, critical feedback on every answer, including a numeric score (0-100) and specific improvement tips.

## 🛠️ Tech Stack

- **GUI**: PyQt6 (Modern Dark Theme with Glassmorphism)
- **AI/LLM**: Google Gemini API / OpenAI API
- **Computer Vision**: OpenCV, MediaPipe (Face Mesh)
- **Audio**: SpeechRecognition, PyAudio, pyttsx3 / macOS `say` command
- **System**: MSS (Screen Capture), Subprocess (Code Execution)

## 📦 Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-interviewer.git
   cd ai-interviewer
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you encounter Qt plugin errors on macOS, ensure you have a compatible PyQt6 version:*
   ```bash
   pip install PyQt6==6.5.0
   ```

4. **Setup Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   # Choose Provider: 'gemini' or 'openai'
   LLM_PROVIDER=gemini
   
   # API Keys
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Override Model
   # LLM_MODEL=gemini-1.5-pro
   ```

## 🎮 Usage

1. **Run the Application**:
   ```bash
   python main.py
   ```
2. **Welcome Screen**:
   - Select a domain (Python, DSA, System Design, etc.).
   - (Optional) Upload your Resume (PDF) for a personalized session.
   - Click **Start Interview**.
3. **The Interview**:
   - The AI Avatar will ask a question.
   - **Speak** your answer or **Type** it in the box.
   - For coding questions, use the code editor and click **Run Code** to test your solution.
   - Click **Submit** to get immediate feedback.
4. **Summary**:
   - At the end, view your total score, verdict, and performance summary.

## 📂 Project Structure

- `main.py`: Application entry point.
- `gui.py`: Main GUI implementation (PyQt6), handling threads for Camera, Audio, and UI updates.
- `interview_engine.py`: Core logic managing the interview state machine.
- `llm_interface.py`: Interface for interacting with Gemini/OpenAI APIs.
- `resume_parser.py`: Extracts text from PDF resumes.
- `code_executor.py`: Safely executes user code and captures output.
- `evaluator.py`: Fallback logic for basic evaluation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
