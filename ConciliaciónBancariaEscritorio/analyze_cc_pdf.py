
import pdfplumber
import re

pdf_path = r"f:\1. Cloud\4. AI\1. Antigravity\Gastos SLB Vo\MovimientosPendientes\MovimientosTusTarjetasBancolombia28Dic2025 (3).pdf"

def analyze_pdf(path):
    print(f"Analyzing: {path}")
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                print(f"--- Page {i+1} ---")
                print(text[:1000]) # First 1000 chars
                print("...")
                # Try to find lines with currency
                lines = text.split('\n')
                for line in lines:
                    if 'USD' in line or 'COP' in line:
                        print(f"Found currency line: {line.strip()}")
                if i >= 1: break # Only check first 2 pages
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_pdf(pdf_path)
