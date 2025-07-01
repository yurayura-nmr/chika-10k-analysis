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
def chunk_text(text, chunk_size=1000):
    """Split text into word-based chunks"""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i : i + chunk_size])


# ===== 3. Anecdote Detection via Ollama API =====
# def detect_anecdote(text_chunk, debug=False):
#    """Query Ollama's API for an anecdote"""
#    prompt = f"""
#    You are analyzing a real excerpt from a historical Coca-Cola annual report.
#
#    Your task is to find a **true, interesting anecdote** strictly based on the content of the text.
#
#    If the text contains a real historical event, such as:
#    - Expansions to new countries
#    - Recipe changes
#    - Disputes with bottlers
#    - War-time decisions
#    - Notable marketing campaigns
#    - Shifts in production or sourcing
#    - Specific leadership changes with impact
#
#    ...then return exactly one or two sentences summarizing that anecdote.
#
#    Do NOT invent facts.
#    Do NOT copy any example below.
#    Do NOT output anything if no event is found.
#    If nothing clearly stands out, return just the digit: 0
#
#    Examples (for format reference only — never reuse):
#    - "In 1929, Coke expanded to Egypt despite the Great Depression."
#    - "During WWII, sugar rationing forced a recipe change."
#
#    Now process the following:
#
#    Text: {text_chunk}
#    """


def detect_anecdote(text_chunk, debug=False):
    """Query Ollama's Deepseek model for a *specific anecdote only*"""
    prompt = f"""
You are parsing real historical Coca-Cola annual report text.

Your only goal is to extract a **true historical anecdote**, such as:
- Expansion to a new country
- Recipe or packaging change
- Bottler dispute or reorganization
- War-time production changes
- Major ad campaigns or slogans
- Leadership changes with impact
- Sourcing or distribution shift

Rules:
- Do **NOT** summarize performance, profits, sales, or divisions.
- Do **NOT** describe overall strategy or market trends.
- Do **NOT** include conclusions or commentary.
- Return **one or two sentences only** if a clear historical event is present.
- Return **just the digit 0** if no real event/anecdote is found.

Examples (for formatting only):
- "In 1993, Coca-Cola introduced a 96-ounce plastic bottle to target large households."
- "During the Gulf War, Coke rerouted syrup shipments through Turkey to reach troops."

Now evaluate:

Text: {text_chunk}
    """

    if debug:
        print(f"\n=== DEBUG PROMPT ===\n{prompt[:1000]}...\n==================")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "deepseek-r1:14b", "prompt": prompt, "stream": False},
            timeout=300,
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
def scan_pdfs(pdf_folder="./coke_pdfs/", output_file="coke_anecdotes.txt"):
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

            # anecdote = detect_anecdote(chunk, debug=True)  # Enable debug logging
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
    output_file = "coke_anecdotes.txt"
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"🗑️ Removed old {output_file} to start fresh.")

    print("=== Starting scan (debug mode) ===")
    scan_pdfs()
    print("=== Done ===")
