from pathlib import Path
import fitz  # PyMuPDF

FILES = [
    r"c:\Users\OMEN\Downloads\codewars.pdf",
    r"c:\Users\OMEN\Downloads\codewars overview.pdf",
    r"c:\Users\OMEN\Downloads\code wars documentation.pdf",
]

OUTDIR = Path(r"c:\Users\OMEN\CodeWarsV6\.tmp_docs\pages")
OUTDIR.mkdir(parents=True, exist_ok=True)

ZOOM = 2.0  # ~144 DPI for readable text
MATRIX = fitz.Matrix(ZOOM, ZOOM)

for file_path in FILES:
    doc = fitz.open(file_path)
    stem = Path(file_path).stem.replace(" ", "_")
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=MATRIX, alpha=False)
        outpath = OUTDIR / f"{stem}_p{i:02d}.png"
        pix.save(outpath)
        print(f"Wrote {outpath}")
    doc.close()
