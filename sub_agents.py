import os
import sys

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure path setup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Tools.browser import google_search
from Tools.browser_autopilot import extract_webpage_content
from Tools.File_manger import read_file
from openai import OpenAI
from config_driver import Check_Keys

LLM_KEY = Check_Keys("KEYS", "LLM_KEY")
BASE_URL = Check_Keys("LLM", "LLM_SERVICE_PROVIDER_URL")
MODEL = Check_Keys("LLM", "MODEL")

client = OpenAI(base_url=BASE_URL, api_key=LLM_KEY)


def deep_research_agent(topic: str):
    """
    Sub-Agent specialized in deep multi-source web research.
    Performs search, page extraction, and structured synthesis.
    """
    try:
        # Step 1: Initial Search
        search_res = google_search(topic, max_results=3)
        results = search_res.get("results", []) if isinstance(search_res, dict) else []

        gathered_notes = []
        for r in results:
            url = r.get("url")
            if url:
                extracted = extract_webpage_content(url, max_chars=1500)
                if extracted.get("status") == "success":
                    gathered_notes.append(f"Source ({url}):\n{extracted.get('content')}")

        combined_notes = "\n\n".join(gathered_notes) if gathered_notes else str(search_res)

        # Step 2: Synthesis via LLM
        prompt = f"""You are F.R.I.D.A.Y Deep Research Agent.
Topic: {topic}

Raw Information Collected from Web Sources:
{combined_notes}

Task: Write a comprehensive, well-structured research report summarizing key findings, bullet points, and conclusions for Shubham sir."""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Deep Research Agent Error: {str(e)}"


def code_reviewer_agent(code_or_filename: str):
    """
    Sub-Agent specialized in static code analysis, bug finding, and optimization.
    Can accept raw code string or filename in CONTENT_PATH.
    """
    try:
        code_content = code_or_filename
        if os.path.exists(code_or_filename) or "." in code_or_filename and not "\n" in code_or_filename:
            file_res = read_file(code_or_filename)
            if isinstance(file_res, dict) and file_res.get("status") == "success":
                code_content = file_res.get("content", code_or_filename)

        prompt = f"""You are F.R.I.D.A.Y Expert Code Reviewer Agent.
Analyze the following code snippet/file carefully:

```python
{code_content}
```

Provide a structured review covering:
1. 🐛 Potential Bugs & Edge Cases
2. ⚡ Performance & Efficiency Suggestions
3. 🔒 Security & Best Practices
4. ✨ Refactored / Improved Code Snippet"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Code Reviewer Agent Error: {str(e)}"


if __name__ == "__main__":
    print("🤖 Testing Sub-Agents...")
    print(code_reviewer_agent("def add(a, b): return a + b"))
