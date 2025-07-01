import os
import time
import requests
import PyPDF2

# ===== 1. Extract Text from PDFs =====
def extract_text_from_pdf(pdf_path):
    """Extract text using PyPDF2"""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# ===== 2. Chunk Text for Ollama =====
def chunk_text(text, chunk_size=700):
    """Split text into word-based chunks"""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

# ===== 3. Anecdote Detection via Ollama API =====
def detect_anecdote(text_chunk, debug=False):
    """Query Ollama's API for an anecdote"""
    prompt = f"""
    You are analyzing a real excerpt from a Berkshire Hathaway annual report.

    Your task is to find a **true, interesting anecdote** strictly based on the content of the text.

    If the text contains a real historical event or insight, such as:
    - Warren Buffett or Charlie Munger making a key investment decision
    - Commentary on a market crash, inflation, or interest rates
    - Acquisitions or divestitures of major subsidiaries (e.g. GEICO, BNSF, See’s Candies)
    - Lessons learned from mistakes or poor predictions
    - Berkshire’s philosophy on long-term investing or capital allocation
    - Notable quotes or humorous commentary with real historical relevance    

    ...then return a few sentences summarizing that anecdote.

    Do NOT invent facts.
    Do NOT copy any example below.
    Do NOT output anything if no event is found.
    If nothing clearly stands out, return just the digit: 0

    Examples (for format reference only — never reuse):
    - "In 1983, Buffett acquired Nebraska Furniture Mart after being impressed by Rose Blumkin's business acumen."
    - "During the 2008 financial crisis, Berkshire invested $5 billion in Goldman Sachs, securing a lucrative preferred stock deal."

    Remember: Your task is to find a **interesting anecdote**.
    Now process the following:

    Text: {text_chunk}
    """
    
    #- Succession planning or leadership changes
    #- Unusual shareholder meeting stories

    if debug:
        print(f"\n=== DEBUG PROMPT ===\n{prompt[:1000]}...\n==================")
        
    

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-r1:14b",
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        output = result.get("response", "").strip()

        if debug:
            print(f"=== RAW RESPONSE ===\n{output}\n==================")

        return output if output != "0" else None
    except Exception as e:
        print(f"Ollama API error: {e}")
        return None

# ===== 4. Scan PDFs and Extract Anecdotes =====
def scan_pdfs(pdf_folder="./berkshire_pdfs/", output_file="berkshire_anecdotes.txt"):
    """Process all PDFs and save found anecdotes"""
    for filename in os.listdir(pdf_folder):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(pdf_folder, filename)
        print(f"\n📄 Processing: {filename}")

        text = extract_text_from_pdf(pdf_path)
        if not text:
            print("  ⚠️ No text extracted")
            continue

        for i, chunk in enumerate(chunk_text(text)):
            print(f"  Chunk {i+1}: ", end="", flush=True)
            
            
            #anecdote = detect_anecdote(chunk, debug=True)  # Enable debug logging
            anecdote = detect_anecdote(chunk, debug=False)  # Enable debug logging
            
            
            if anecdote:
                print(f"✅ Found: {anecdote[:50]}...")
                with open(output_file, "a", encoding="utf-8") as f:
                    year = "".join(filter(str.isdigit, filename[:4]))
                    f.write(f"{year}: {anecdote}\n")
            else:
                print("❌ No anecdote")
            time.sleep(1)

# ===== RUN =====
if __name__ == "__main__":
    
    # ===== Delete output file if it exists =====
    output_file = "berkshire_anecdotes.txt"
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"🗑️ Removed old {output_file} to start fresh.")
    
    print("=== Starting scan (debug mode) ===")
    scan_pdfs()
    print("=== Done ===")
