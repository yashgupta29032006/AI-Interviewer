import subprocess
import sys
import os
import tempfile
import json

class CodeExecutor:
    def run_code(self, user_code, function_name, test_cases):
        """
        Runs the user's code against the provided test cases.
        Returns a dict with 'success', 'output', 'errors'.
        """
        if not test_cases:
            return {"success": True, "output": "No test cases provided. Code structure looks okay.", "errors": ""}

        # Create a temporary script
        # We append a test runner to the user's code
        test_runner_code = self._generate_test_runner(function_name, test_cases)
        full_script = f"{user_code}\n\n{test_runner_code}"
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(full_script)
                tmp_path = tmp.name
            
            # Run the script
            # Timeout set to 5 seconds to prevent infinite loops
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Cleanup
            os.remove(tmp_path)
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout, "errors": ""}
            else:
                return {"success": False, "output": result.stdout, "errors": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "errors": "Execution Timed Out (Infinite Loop?)"}
        except Exception as e:
            return {"success": False, "output": "", "errors": str(e)}

    def _generate_test_runner(self, function_name, test_cases):
        """
        Generates Python code to run the function against test cases.
        """
        runner_code = """
if __name__ == "__main__":
    try:
        passed = 0
        total = 0
        test_cases = """ + json.dumps(test_cases) + """
        
        for case in test_cases:
            total += 1
            input_args = case['input']
            expected = case['output']
            
            # Call the function
            try:
                result = """ + function_name + """(*input_args)
                if result == expected:
                    print(f"Test Case {total}: PASSED")
                    passed += 1
                else:
                    print(f"Test Case {total}: FAILED. Expected {expected}, got {result}")
            except Exception as e:
                print(f"Test Case {total}: ERROR - {e}")
        
        print(f"\\nSummary: {passed}/{total} Test Cases Passed")
        if passed != total:
            exit(1) # Fail the process if not all passed
            
    except NameError:
        print(f"Error: Function '{""" + f"'{function_name}'" + """}' not found. Did you name it correctly?")
        exit(1)
    except Exception as e:
        print(f"System Error: {e}")
        exit(1)
"""
        return runner_code
