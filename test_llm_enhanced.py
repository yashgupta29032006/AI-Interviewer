from llm_interface import LLMInterface
import os

def test_llm():
    print("Initializing LLM Interface...")
    llm = LLMInterface()
    
    if not llm.is_configured():
        print("Error: LLM not configured. Check .env")
        return

    print(f"Provider: {llm.provider}")
    print(f"Model: {getattr(llm, 'model_name', 'Default')}")

    # Test Question Generation
    print("\n--- Testing Question Generation ---")
    history = "User: I have 3 years of experience in Python."
    domain = "Python"
    difficulty = "Hard"
    
    question = llm.generate_question(history, domain, difficulty)
    print(f"Generated Question:\n{question}")
    
    if not question:
        print("FAILED to generate question.")
    else:
        print("SUCCESS: Question generated.")

    # Test Evaluation
    print("\n--- Testing Answer Evaluation ---")
    test_q = "Explain the Global Interpreter Lock (GIL) in Python."
    test_a = "The GIL is a mutex that allows only one thread to hold the control of the Python interpreter."
    
    result = llm.evaluate_answer(test_q, test_a)
    print(f"Evaluation Result:\n{result}")
    
    if isinstance(result, dict) and 'score' in result and 'feedback' in result:
        print(f"SUCCESS: Parsed result correctly. Score: {result['score']}")
    else:
        print("FAILED to parse result.")

if __name__ == "__main__":
    test_llm()
