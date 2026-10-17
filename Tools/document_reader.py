"""
F.R.I.D.A.Y // Document & PDF Reader Tool
Extracts and summarizes text from PDFs, Text files, Markdown, Code, and Docs.
Powered by PyMuPDF (fitz) for ultra-fast, high-accuracy document parsing.
"""

import os
import sys

# Ensure parent path in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from path import CONTENT_PATH


def read_pdf_or_document(filepath: str, max_pages: int = 10, max_chars: int = 6000) -> dict:
    """
    Extracts readable text from a PDF, TXT, MD, CSV, JSON, or code file.
    filepath: Absolute path or filename inside CONTENT_PATH.
    max_pages: Maximum number of pages to read from PDF (defaults to 10).
    max_chars: Maximum characters to return to keep context concise.
    """
    try:
        # Resolve path
        if not os.path.isabs(filepath):
            # Check CONTENT_PATH first, then current working dir
            candidate1 = os.path.join(CONTENT_PATH, filepath)
            candidate2 = os.path.abspath(filepath)
            filepath = candidate1 if os.path.exists(candidate1) else candidate2

        if not os.path.exists(filepath):
            return {
                "status": "error",
                "message": f"File not found: '{filepath}'. Please check the filename or path."
            }

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        # 1. PDF File Parsing using PyMuPDF (fitz)
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(filepath)
                total_pages = len(doc)
                pages_to_read = min(total_pages, max_pages)

                extracted_text = []
                for pno in range(pages_to_read):
                    page = doc.load_page(pno)
                    text = page.get_text("text").strip()
                    if text:
                        extracted_text.append(f"--- [Page {pno + 1}] ---\n{text}")

                full_content = "\n\n".join(extracted_text)
                doc.close()

                if len(full_content) > max_chars:
                    full_content = full_content[:max_chars] + f"\n... [Truncated for brevity. Document has {total_pages} total pages]"

                return {
                    "status": "success",
                    "file": filename,
                    "type": "pdf",
                    "total_pages": total_pages,
                    "pages_read": pages_to_read,
                    "content": full_content or "No extractable text found in this PDF (it might be scanned/image-only)."
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to extract PDF with PyMuPDF: {str(e)}"
                }

        # 2. Text / Markdown / Code / JSON / CSV files
        text_extensions = {".txt", ".md", ".py", ".json", ".csv", ".log", ".html", ".xml", ".ini", ".cfg", ".yaml", ".yml"}
        if ext in text_extensions or ext == "":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
                truncated = f.read(1) != ""

            if truncated:
                content += "\n... [Content truncated for length]"

            return {
                "status": "success",
                "file": filename,
                "type": ext.lstrip(".") or "text",
                "content": content
            }

        return {
            "status": "error",
            "message": f"Unsupported document format: '{ext}'. Supported formats: .pdf, .txt, .md, .py, .json, .csv, .log."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Document reader error: {str(e)}"
        }
