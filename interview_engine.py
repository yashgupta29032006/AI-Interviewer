from question_generator import QuestionGenerator
from code_analyzer import CodeAnalyzer
from evaluator import Evaluator
from llm_interface import LLMInterface
from resume_parser import ResumeParser
import random

class InterviewEngine:
    def __init__(self):
        self.q_gen = QuestionGenerator()
        self.analyzer = CodeAnalyzer()
        self.evaluator = Evaluator()
        self.evaluator = Evaluator()
        self.llm = LLMInterface()
        self.resume_parser = ResumeParser()
        
        self.state = "select_domain"
        self.domain = None
        self.resume_text = None
        self.difficulty = "medium"
        self.current_question = None
        self.history = [] # List of {"role": "ai"/"user", "content": "..."}
        self.score_log = []
        
        self.questions_asked = 0
        self.max_questions = 5 
        self.use_llm = self.llm.is_configured()

    def start_interview(self, domain, resume_path=None):
        self.domain = domain
        self.state = "ask_theory_question"
        self.questions_asked = 0
        self.history = []
        self.score_log = []
        self.resume_text = None
        
        if resume_path:
            self.resume_text = self.resume_parser.extract_text(resume_path)
            
        # Re-check LLM config in case it changed (e.g. key added)
        self.llm._setup_client() 
        self.use_llm = self.llm.is_configured()
        return self.get_next_question()

    def get_next_question(self):
        if self.questions_asked >= self.max_questions:
            self.state = "summary"
            return None

        self.questions_asked += 1
        
        # Determine Question Type
        # For simplicity: 3 theory, 1 coding, 1 theory
        if self.questions_asked == 3:
            q_type = "coding"
            self.state = "ask_coding_question"
        else:
            q_type = "theory"
            self.state = "ask_theory_question"

        # Try LLM first if configured and not a coding question (for now)
        # (We can add LLM coding questions later, but let's stick to static for safety on coding first)
        if self.use_llm and q_type == "theory":
            history_text = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in self.history])
            llm_question_text = self.llm.generate_question(history_text, self.domain, self.difficulty, self.resume_text)
            
            if llm_question_text:
                self.current_question = {
                    "text": llm_question_text,
                    "type": "conceptual",
                    "difficulty": self.difficulty,
                    "domain": self.domain
                }
                self.history.append({"role": "ai", "content": llm_question_text})
                return self.current_question

        # Fallback to Static Generator
        question = self.q_gen.get_question(self.domain, self.difficulty, q_type)
        
        # If we couldn't get the requested type, fallback to whatever we got
        if question:
            if question['type'] == 'coding':
                self.state = "ask_coding_question"
            else:
                self.state = "ask_theory_question"
            
            self.current_question = question
            self.history.append({"role": "ai", "content": question['text']})
            return question
            
        return None

    def submit_answer(self, answer, wpm=0, fillers=0):
        """
        Processes the answer with behavioral metrics.
        """
        self.history.append({"role": "user", "content": answer})
        result = {}
        
        # Sentiment Analysis
        from textblob import TextBlob
        blob = TextBlob(answer)
        sentiment_score = blob.sentiment.polarity # -1 to 1
        
        # Adjust score based on confidence/sentiment
        confidence_bonus = 5 if sentiment_score > 0.3 else 0
        
        feedback = ""
        score = 0
        
        if self.state == "ask_coding_question":
            # Analyze code
            analysis = self.analyzer.analyze_code(answer)
            result['analysis'] = analysis
            
            # Simple scoring for code (validity check)
            score = 100 if analysis['valid'] else 0
            feedback = "Code looks good!" if analysis['valid'] else f"Error: {analysis.get('error')}"
            
            # Store follow-ups for the GUI to display
            self.current_follow_ups = analysis.get('follow_ups', [])
            self.state = "ask_code_followup_question"
            
        else:
            # Evaluate theory
            # Try LLM Evaluation first
            if self.use_llm:
                llm_result = self.llm.evaluate_answer(self.current_question['text'], answer)
                if llm_result and isinstance(llm_result, dict):
                    feedback = llm_result.get('feedback', '')
                    score = llm_result.get('score', 0)
                else:
                    # Fallback if LLM fails or returns None
                     score, feedback = self.evaluator.evaluate_answer(self.current_question, answer)
            else:
                score, feedback = self.evaluator.evaluate_answer(self.current_question, answer)
            
            score += confidence_bonus
            score = min(100, score)
            
            # Add behavioral feedback and penalty
            if wpm > 160:
                feedback += " You are speaking a bit too fast."
                score -= 5
            elif wpm < 100 and wpm > 0:
                feedback += " You are speaking a bit slowly."
                score -= 5
                
            if fillers > 2:
                feedback += f" Try to reduce filler words (detected {fillers})."
                score -= min(10, fillers * 2) # Deduct 2 points per filler, max 10
            
            score = max(0, score) # Ensure score doesn't go negative
            
            self.state = "ask_theory_question" # Ready for next
        
        # Update difficulty
        if score > 80:
            self.difficulty = "hard"
        elif score < 40:
            self.difficulty = "easy"
        else:
            self.difficulty = "medium"
            
        self.score_log.append(score)
        
        # Update history with full details
        self.history[-1]['score'] = score
        self.history[-1]['feedback'] = feedback
        self.history[-1]['wpm'] = wpm
        self.history[-1]['fillers'] = fillers
        
        result['score'] = score
        result['feedback'] = feedback
        return result

    def get_summary(self):
        total_score = sum(self.score_log)
        avg_score = total_score / len(self.score_log) if self.score_log else 0
        
        return {
            "total_score": total_score,
            "average_score": avg_score,
            "questions_answered": len(self.score_log),
            "verdict": "Passed" if avg_score > 70 else "Needs Improvement"
        }
