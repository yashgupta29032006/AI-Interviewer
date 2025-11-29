import unittest
from question_generator import QuestionGenerator
from code_analyzer import CodeAnalyzer
from evaluator import Evaluator
from interview_engine import InterviewEngine

class TestAIInterview(unittest.TestCase):
    def setUp(self):
        self.q_gen = QuestionGenerator()
        self.analyzer = CodeAnalyzer()
        self.evaluator = Evaluator()
        self.engine = InterviewEngine()

    def test_question_generation(self):
        q = self.q_gen.get_question("Python", "medium")
        self.assertIsNotNone(q)
        self.assertIn("text", q)
        self.assertIn("type", q)

    def test_code_analysis_recursion(self):
        code = """
def factorial(n):
    if n == 0: return 1
    return n * factorial(n-1)
"""
        result = self.analyzer.analyze_code(code)
        self.assertTrue(result['valid'])
        self.assertTrue(any("recursion" in s for s in result['observations']))

    def test_evaluator(self):
        q = {"text": "What is a list?", "type": "theory"}
        score, feedback = self.evaluator.evaluate_answer(q, "A list is a mutable sequence.")
        self.assertTrue(score > 0)

    def test_engine_flow(self):
        self.engine.start_interview("Python")
        self.assertEqual(self.engine.state, "ask_theory_question")
        
        # Answer 3 theory questions
        for _ in range(3):
            self.engine.submit_answer("Some valid answer")
            self.engine.get_next_question()
            
        # Should be coding now (or close to it, depending on logic)
        # Our logic: 3 theory -> 1 coding. 
        # questions_asked starts at 0. 
        # 0 (theory) -> submit -> 1
        # 1 (theory) -> submit -> 2
        # 2 (theory) -> submit -> 3
        # get_next_question sees 3 -> sets coding
        
        self.assertEqual(self.engine.state, "ask_coding_question")

if __name__ == '__main__':
    unittest.main()
