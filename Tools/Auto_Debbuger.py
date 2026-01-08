import os
import re
import shutil
from auto_runner import run_project
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Friday ka same LLM client use hoga
from Brain import client   # ⚠️ jahan Brain() likha hai us file ka naam daalna


# ---------------- ERROR PARSER ---------------- #

def extract_error_info(error_text):
    match = re.search(r'File "(.+?)", line (\d+)', error_text)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


# ---------------- FILE OPS ---------------- #

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def backup_file(file_path):
    shutil.copy(file_path, file_path + ".bak")


def write_fixed_code(file_path, new_code):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


# ---------------- CLEAN LLM OUTPUT ---------------- #

def clean_code(text):
    text = re.sub(r"```.*?\n", "", text)
    text = text.replace("```", "")
    return text.strip()


# ---------------- LLM FIX CALL ---------------- #

def ask_friday_llm_to_fix(error, code):

    prompt = f"""
You are a senior software debugger.
Fix the bug and return ONLY the full corrected file code.

ERROR:
{error}

CODE:
{code}
"""

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "Return only fixed code, no explanation."},
            {"role": "user", "content": prompt}
        ]
    )

    text = response.choices[0].message.content
    return clean_code(text)


# ---------------- SAFETY ---------------- #

def is_safe_path(project_path, file_path):
    return os.path.commonpath([project_path]) == os.path.commonpath([project_path, file_path])


# ---------------- AUTO DEBUG TOOL ---------------- #

def auto_debug_project(project_path: str):

    max_tries = 3

    for i in range(max_tries):
        print(f"\n🧠 Debug Attempt {i+1}")

        ok, output = run_project(project_path)

        if ok:
            return "✅ Project fixed and running successfully!"

        file_path, line = extract_error_info(output)

        if not file_path or not os.path.exists(file_path):
            return f"❌ Could not locate error file.\n\n{output}"

        if not is_safe_path(project_path, file_path):
            return "❌ Unsafe file edit blocked."

        code = read_file(file_path)
        backup_file(file_path)

        fixed_code = ask_friday_llm_to_fix(output, code)

        if not fixed_code:
            return "❌ LLM could not fix the code."

        write_fixed_code(file_path, fixed_code)

        print("🛠 Fix applied, re-running...")

    return "❌ Could not fix after multiple attempts."


print(auto_debug_project(r"C:\Users\j\OneDrive\Desktop\shubham studio\Skills Learning\New folder"))