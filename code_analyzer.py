import ast

class CodeAnalyzer:
    def __init__(self):
        pass

    def analyze_code(self, code_snippet):
        """
        Parses the code snippet and returns a list of observations and potential follow-up questions.
        """
        observations = []
        follow_ups = []
        
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "observations": ["Code has syntax errors."],
                "follow_ups": ["Can you fix the syntax error in your code?"]
            }

        # Analyze AST
        analyzer = ASTVisitor()
        analyzer.visit(tree)
        
        observations = analyzer.stats
        
        # Generate heuristics-based follow-ups
        if analyzer.has_recursion:
            follow_ups.append("I see you used recursion. What is the base case here?")
            follow_ups.append("What happens if the recursion depth becomes too large? How would you handle StackOverflow?")
        
        if analyzer.has_nested_loops:
            follow_ups.append("You used nested loops. What is the time complexity of this approach?")
            follow_ups.append("Can this be optimized to O(n) or O(n log n)?")
            
        if analyzer.has_list_comp:
            follow_ups.append("Nice use of list comprehensions. Is this more memory efficient than a standard loop?")
            
        if analyzer.has_class:
            follow_ups.append("You defined a class. How would you ensure encapsulation here?")
            
        if not follow_ups:
            follow_ups.append("What is the time and space complexity of your solution?")
            follow_ups.append("Can you explain your logic step-by-step?")
            follow_ups.append("Are there any edge cases (like empty input) that might break this?")
            
        return {
            "valid": True,
            "observations": observations,
            "follow_ups": follow_ups
        }

class ASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stats = []
        self.has_recursion = False
        self.has_nested_loops = False
        self.loop_depth = 0
        self.has_list_comp = False
        self.has_class = False
        self.functions = []

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        # Check for recursion (simplistic check: function calls itself)
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == node.name:
                    self.has_recursion = True
                    self.stats.append(f"Detected recursion in function '{node.name}'.")
        self.generic_visit(node)

    def visit_For(self, node):
        self.loop_depth += 1
        if self.loop_depth > 1:
            self.has_nested_loops = True
            if "Detected nested loops." not in self.stats:
                self.stats.append("Detected nested loops.")
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node):
        self.loop_depth += 1
        if self.loop_depth > 1:
            self.has_nested_loops = True
            if "Detected nested loops." not in self.stats:
                self.stats.append("Detected nested loops.")
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_ListComp(self, node):
        self.has_list_comp = True
        self.stats.append("Detected list comprehension.")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.has_class = True
        self.stats.append(f"Detected class definition '{node.name}'.")
        self.generic_visit(node)

if __name__ == "__main__":
    sample_code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
    """
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_code(sample_code)
    print(result)
