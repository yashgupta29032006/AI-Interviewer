import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

class LLMInterface:
    def __init__(self):
        load_dotenv()
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.api_key = None
        self.client = None
        self.model = None
        
        self._setup_client()

    def _setup_client(self):
        # Allow overriding model via env var
        self.model_name = os.getenv("LLM_MODEL")

        if self.provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
                # Default to a stronger model for better reasoning
                if not self.model_name:
                    self.model_name = 'gemini-2.0-flash' 
                self.model = genai.GenerativeModel(self.model_name)
        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
                if not self.model_name:
                    self.model_name = 'gpt-4o'

    def is_configured(self):
        return bool(self.api_key)

    def generate_question(self, history, domain, difficulty, resume_context=None):
        """
        Generates the next interview question based on history, domain, difficulty, and optional resume context.
        """
        if not self.is_configured():
            return None

        prompt = f"""
You are a Senior Staff Software Engineer conducting a rigorous technical interview.
Your goal is to accurately assess the candidate's depth of knowledge, problem-solving skills, and ability to handle complexity.
Do not ask surface-level definitions. Probe for understanding of trade-offs, internals, and best practices.

Current Domain: {domain}
Difficulty Level: {difficulty} (Adjust based on history: if they are doing well, push harder.)
"""
        if resume_context:
            prompt += f"\nCandidate Resume Context:\n{resume_context}\n"

        prompt += f"""
Previous Conversation History:
{history}

Task: Generate the next interview question.
Guidelines:
1. If Resume Context is available, prioritize questions about their specific projects or claimed skills. Challenge their design choices.
2. If the previous answer was weak, ask a fundamental question to check basics, but don't make it too easy.
3. If the previous answer was strong, ask a deep-dive follow-up (e.g., "How would this scale?", "What happens under memory pressure?", "Compare with X").
4. Keep the question concise but professional.
5. Output ONLY the question text. No preambles.
"""

        try:
            if self.provider == "gemini":
                response = self.model.generate_content(prompt)
                return response.text.strip()
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "system", "content": "You are a Senior Technical Interviewer."},
                              {"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            return None

    def evaluate_answer(self, question, answer):
        """
        Evaluates the user's answer and provides feedback.
        """
        if not self.is_configured():
            return None

        prompt = f"""
        Question: {question}
        Candidate's Answer: {answer}
        
        Act as a strict technical interviewer. Evaluate the answer critically.
        
        Output format:
        Score: <0-100>
        Feedback: <Concise, critical feedback. Mention what was wrong or missing. Be direct.>
        
        Example:
        Score: 65
        Feedback: You mentioned the basic concept but missed the thread-safety aspect. In a production environment, this would cause race conditions.
        """

        try:
            text_response = ""
            if self.provider == "gemini":
                response = self.model.generate_content(prompt)
                text_response = response.text.strip()
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "system", "content": "You are a strict technical interviewer."},
                              {"role": "user", "content": prompt}]
                )
                text_response = response.choices[0].message.content.strip()
            
            # Parse Score and Feedback
            import re
            score_match = re.search(r"Score:\s*(\d+)", text_response, re.IGNORECASE)
            feedback_match = re.search(r"Feedback:\s*(.*)", text_response, re.IGNORECASE | re.DOTALL)
            
            score = int(score_match.group(1)) if score_match else 50
            feedback = feedback_match.group(1).strip() if feedback_match else text_response
            
            return {"score": score, "feedback": feedback}
        except Exception as e:
            print(f"LLM Evaluation Error: {e}")
            return None
