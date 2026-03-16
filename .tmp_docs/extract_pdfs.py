from pathlib import Path
import fitz  # PyMuPDF

FILES = [
    r"c:\Users\OMEN\Downloads\codewars.pdf",
    r"c:\Users\OMEN\Downloads\codewars overview.pdf",
    r"c:\Users\OMEN\Downloads\code wars documentation.pdf",
]

OUTDIR = Path(r"c:\Users\OMEN\CodeWarsV6\.tmp_docs")
OUTDIR.mkdir(exist_ok=True)

for file_path in FILES:
    text = []
    doc = fitz.open(file_path)
    for i, page in enumerate(doc):
        page_text = page.get_text("text") or ""
        text.append(f"\n\n--- Page {i + 1} ---\n\n{page_text}")
    doc.close()
    outpath = OUTDIR / (Path(file_path).stem.replace(" ", "_") + ".txt")
    outpath.write_text("".join(text), encoding="utf-8")
    print(f"Wrote {outpath}")
