import os
import json
import subprocess

# ---------------------------
# 🔍 Detect Project Type
# ---------------------------
def detect_project_type(path):
    files = os.listdir(path)

    if "package.json" in files:
        return "node"

    if "requirements.txt" in files or any(f.endswith(".py") for f in files):
        return "python"

    if "pom.xml" in files:
        return "java"

    if any(f.endswith(".cpp") for f in files):
        return "cpp"

    return "unknown"


# ---------------------------
# 🎯 Detect Entry Point
# ---------------------------
def find_entry_point(path, project_type):

    if project_type == "python":
        for f in ["main.py", "app.py"]:
            if os.path.exists(os.path.join(path, f)):
                return f

        # fallback: first .py file
        for f in os.listdir(path):
            if f.endswith(".py"):
                return f

    if project_type == "node":
        pkg_path = os.path.join(path, "package.json")
        if os.path.exists(pkg_path):
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            if "scripts" in pkg and "start" in pkg["scripts"]:
                return "npm start"

        for f in ["index.js", "server.js"]:
            if os.path.exists(os.path.join(path, f)):
                return f

    if project_type == "java":
        return "mvn spring-boot:run"

    if project_type == "cpp":
        for f in os.listdir(path):
            if f.endswith(".cpp"):
                return f

    return None


# ---------------------------
# ▶️ Build Run Command
# ---------------------------
def build_run_command(project_type, entry):

    if project_type == "python":
        return ["python", entry]

    if project_type == "node":
        if entry == "npm start":
            return ["npm", "start"]
        return ["node", entry]

    if project_type == "java":
        return ["mvn", "spring-boot:run"]

    if project_type == "cpp":
        exe = "a.exe" if os.name == "nt" else "a.out"
        return ["g++", entry, "-o", exe], [f"./{exe}"]

    return None


# ---------------------------
# 🚀 Run Project
# ---------------------------
def run_project(path):

    project_type = detect_project_type(path)
    entry = find_entry_point(path, project_type)

    if not entry:
        return False, "❌ Entry point not found"

    cmd = build_run_command(project_type, entry)

    try:
        if project_type == "cpp":
            compile_cmd, run_cmd = cmd

            subprocess.run(compile_cmd, cwd=path, capture_output=True, text=True)
            result = subprocess.run(run_cmd, cwd=path, capture_output=True, text=True)

        else:
            result = subprocess.run(cmd, cwd=path, capture_output=True, text=True)

        output = result.stdout + result.stderr

        if result.returncode != 0:
            return False, output

        return True, output

    except Exception as e:
        return False, str(e)


# ---------------------------
# 🧪 Test
# ---------------------------
if __name__ == "__main__":
    path = input("Enter project path: ").strip()
    ok, out = run_project(path)

    if ok:
        print("✅ Project ran successfully\n")
    else:
        print("🐞 Error found\n")

    print(out)
