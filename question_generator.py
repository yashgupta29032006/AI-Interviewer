import random

class QuestionGenerator:
    def __init__(self):
        self.questions = {
            "Python": {
                "easy": [
                    {"id": "py_e_1", "text": "What is the difference between list and tuple?", "type": "theory"},
                    {"id": "py_e_2", "text": "Explain the use of 'self' in Python classes.", "type": "theory"},
                    {"id": "py_e_3", "text": "What are Python decorators?", "type": "theory"}
                ],
                "medium": [
                    {"id": "py_m_1", "text": "Explain the Global Interpreter Lock (GIL).", "type": "theory"},
                    {"id": "py_m_2", "text": "How does memory management work in Python?", "type": "theory"},
                    {"id": "py_m_3", "text": "What is the difference between __str__ and __repr__?", "type": "theory"}
                ],
                "hard": [
                    {"id": "py_h_1", "text": "Explain metaclasses in Python.", "type": "theory"},
                    {"id": "py_h_2", "text": "How would you implement a singleton pattern in Python?", "type": "theory"},
                    {"id": "py_h_3", "text": "Write a Python function 'factorial(n)' to calculate the factorial of a number using recursion.", "type": "coding", "function_name": "factorial", "test_cases": [{"input": [5], "output": 120}, {"input": [0], "output": 1}, {"input": [3], "output": 6}]},
                    {"id": "py_h_4", "text": "Implement a decorator 'time_logger' that logs the execution time of a function.", "type": "coding", "function_name": "time_logger", "test_cases": []} # Decorators are hard to test with simple I/O, skipping auto-test for this one
                ]
            },
            "DSA": {
                "easy": [
                    {"id": "dsa_e_1", "text": "What is the time complexity of binary search?", "type": "theory"},
                    {"id": "dsa_e_2", "text": "Explain the difference between stack and queue.", "type": "theory"}
                ],
                "medium": [
                    {"id": "dsa_m_1", "text": "Implement a function 'reverse_list(head)' to reverse a linked list. (Assume Node class exists)", "type": "coding", "function_name": "reverse_list", "test_cases": []}, # Complex input
                    {"id": "dsa_m_2", "text": "Find the missing number in an array of 1 to N. Function: find_missing(arr, n)", "type": "coding", "function_name": "find_missing", "test_cases": [{"input": [[1, 2, 4, 5], 5], "output": 3}, {"input": [[1, 3], 3], "output": 2}]},
                    {"id": "dsa_m_3", "text": "Check if a string is a palindrome using recursion. Function: is_palindrome(s)", "type": "coding", "function_name": "is_palindrome", "test_cases": [{"input": ["racecar"], "output": True}, {"input": ["hello"], "output": False}]}
                ],
                "hard": [
                    {"id": "dsa_h_1", "text": "Implement an LRU Cache.", "type": "coding"},
                    {"id": "dsa_h_2", "text": "Find the median of two sorted arrays.", "type": "coding"}
                ]
            },
            "OOP": {
                "easy": [
                    {"id": "oop_e_1", "text": "What are the 4 pillars of OOP?", "type": "theory"},
                    {"id": "oop_e_2", "text": "What is polymorphism?", "type": "theory"}
                ],
                "medium": [
                    {"id": "oop_m_1", "text": "Explain the difference between abstract class and interface.", "type": "theory"},
                    {"id": "oop_m_2", "text": "What is the diamond problem in inheritance?", "type": "theory"}
                ],
                "hard": [
                    {"id": "oop_h_1", "text": "Design a parking lot system using OOP principles.", "type": "coding"}
                ]
            },
             "DBMS": {
                "easy": [
                    {"id": "dbms_e_1", "text": "What is a primary key?", "type": "theory"},
                    {"id": "dbms_e_2", "text": "What is normalization?", "type": "theory"}
                ],
                "medium": [
                    {"id": "dbms_m_1", "text": "Explain ACID properties.", "type": "theory"},
                    {"id": "dbms_m_2", "text": "Difference between SQL and NoSQL.", "type": "theory"}
                ],
                "hard": [
                    {"id": "dbms_h_1", "text": "Explain database indexing and how B-Trees work.", "type": "theory"}
                ]
            },
            "OS": {
                "easy": [
                    {"id": "os_e_1", "text": "What is a process vs a thread?", "type": "theory"},
                    {"id": "os_e_2", "text": "What is a deadlock?", "type": "theory"}
                ],
                "medium": [
                    {"id": "os_m_1", "text": "Explain paging and segmentation.", "type": "theory"},
                    {"id": "os_m_2", "text": "What are the different scheduling algorithms?", "type": "theory"}
                ],
                "hard": [
                    {"id": "os_h_1", "text": "Explain the concept of virtual memory implementation.", "type": "theory"}
                ]
            },
            "HR": {
                "easy": [
                    {"id": "hr_e_1", "text": "Tell me about yourself.", "type": "theory"},
                    {"id": "hr_e_2", "text": "What are your strengths and weaknesses?", "type": "theory"}
                ],
                "medium": [
                    {"id": "hr_m_1", "text": "Describe a time you faced a conflict in a team.", "type": "theory"},
                    {"id": "hr_m_2", "text": "Where do you see yourself in 5 years?", "type": "theory"}
                ],
                "hard": [
                    {"id": "hr_h_1", "text": "Why should we hire you over other candidates?", "type": "theory"}
                ]
            }
        }

    def get_question(self, domain, difficulty, q_type=None):
        """Returns a random question based on domain and difficulty."""
        if domain not in self.questions:
            return None
        
        # Fallback logic if difficulty is empty (though our bank is populated)
        questions_list = self.questions[domain].get(difficulty, [])
        if not questions_list:
             # Try to find any question if specific difficulty is empty
             for diff in ["medium", "easy", "hard"]:
                 questions_list = self.questions[domain].get(diff, [])
                 if questions_list:
                     break
        
        if not questions_list:
            return None

        # Filter by type if specified
        if q_type:
            filtered_list = [q for q in questions_list if q['type'] == q_type]
            if filtered_list:
                return random.choice(filtered_list)
            # If no question of that type in that difficulty, try other difficulties
            for diff in ["medium", "easy", "hard"]:
                 questions_list = self.questions[domain].get(diff, [])
                 filtered_list = [q for q in questions_list if q['type'] == q_type]
                 if filtered_list:
                     return random.choice(filtered_list)

        return random.choice(questions_list)

if __name__ == "__main__":
    qg = QuestionGenerator()
    print(qg.get_question("Python", "medium"))
