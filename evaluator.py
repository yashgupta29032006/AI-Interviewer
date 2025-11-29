class Evaluator:
    def __init__(self):
        pass

    def evaluate_answer(self, question, user_answer):
        """
        Evaluates the user's answer based on keywords and length.
        Returns a score (0-100) and feedback.
        """
        if not user_answer or len(user_answer.strip()) < 5:
            return 0, "Answer is too short or empty."

        score = 0
        feedback = []

        # Simple keyword matching heuristic
        # In a real app, this would use NLP or embeddings
        keywords = self._get_keywords_for_question(question)
        
        matched_keywords = [kw for kw in keywords if kw.lower() in user_answer.lower()]
        match_ratio = len(matched_keywords) / len(keywords) if keywords else 1.0

        if match_ratio > 0.8:
            score = 100
            feedback.append("Excellent! You covered all key points.")
        elif match_ratio > 0.5:
            score = 75
            feedback.append("Good answer, but you missed some details.")
        elif match_ratio > 0.2:
            score = 40
            feedback.append("Fair attempt, but key concepts are missing.")
        else:
            score = 20
            feedback.append("Your answer doesn't seem to address the core concept.")

        return score, " ".join(feedback)

    def _get_keywords_for_question(self, question):
        """
        Returns expected keywords for a given question.
        This is a placeholder. In a real system, this would come from the DB.
        """
        text = question['text'].lower()
        if "list" in text and "tuple" in text:
            return ["mutable", "immutable", "syntax", "performance"]
        if "self" in text:
            return ["instance", "reference", "object", "method"]
        if "gil" in text:
            return ["thread", "lock", "memory", "cpython", "parallel"]
        if "complexity" in text:
            return ["big o", "log", "linear", "constant"]
        
        # Default generic keywords if specific ones aren't defined
        return ["concept", "logic", "implementation"]

if __name__ == "__main__":
    ev = Evaluator()
    q = {"text": "What is the difference between list and tuple?", "type": "theory"}
    ans = "Lists are mutable while tuples are immutable."
    print(ev.evaluate_answer(q, ans))
