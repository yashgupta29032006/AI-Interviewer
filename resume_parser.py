from pdfminer.high_level import extract_text
import os

class ResumeParser:
    def __init__(self):
        pass

    def extract_text(self, pdf_path):
        """
        Extracts text from a PDF file.
        Returns the text content or None if extraction fails.
        """
        if not os.path.exists(pdf_path):
            print(f"Error: File not found at {pdf_path}")
            return None
        
        try:
            text = extract_text(pdf_path)
            return text.strip()
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None

    def extract_skills(self, text):
        """
        Simple keyword extraction for skills (optional helper).
        For now, we will rely on the LLM to parse the full text.
        """
        # Placeholder for potential future regex-based extraction
        return []
