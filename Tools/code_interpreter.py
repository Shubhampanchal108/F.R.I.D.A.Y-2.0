import sys
import os
import subprocess
import tempfile
import time

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def clean_code_string(code: str) -> str:
    """Strip markdown code fence backticks if present."""
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def run_python_code(code: str, timeout: int = 15):
    """
    Executes Python code safely in an isolated subprocess.
    Captures stdout, stderr, execution time, and return code.
    Useful for calculations, data analysis, file manipulation, and automation.
    """
    code = clean_code_string(code)
    if not code:
        return {"status": "error", "message": "Empty code provided."}

    # Create temporary script
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        start_time = time.time()
        process = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        elapsed = round(time.time() - start_time, 3)

        # Cleanup temp file
        try:
            os.remove(temp_file_path)
        except Exception:
            pass

        return {
            "status": "success" if process.returncode == 0 else "error",
            "exit_code": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "execution_time_sec": elapsed
        }

    except subprocess.TimeoutExpired:
        try:
            os.remove(temp_file_path)
        except Exception:
            pass
        return {"status": "error", "message": f"Execution timed out after {timeout} seconds."}

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("🐍 Testing Code Interpreter...")
    test_code = "import math\nprint('Factorial of 10:', math.factorial(10))"
    res = run_python_code(test_code)
    print(res)
