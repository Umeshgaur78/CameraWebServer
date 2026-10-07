"""Inspect report structure for sequencing / LoF / TOC issues."""
from docx import Document
from docx.oxml.ns import qn

p = r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
d = Document(p)

print("=== ALL HEADINGS / KEY PARAS ===")
for i, para in enumerate(d.paragraphs):
    t = (para.text or "").strip()
    if not t:
        # check image
        has = bool(para._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'))
        if has:
            print(f"{i:3d} [IMAGE]")
        continue
    st = para.style.name if para.style else ""
    show = False
    if st.startswith("Heading") or t.startswith(("CHAPTER", "Chapter", "List of", "CONTENTS", "ABSTRACT", "CERTIFICATE", "ACKNOWLEDGEMENT", "REFERENCES", "Fig.", "Table 4.", "4.", "5.", "Candidate")):
        show = True
    if show:
        print(f"{i:3d} [{st}] {t[:110]}")

print("\n=== TABLES ===")
for ti, table in enumerate(d.tables):
    print(f"Table {ti}: {len(table.rows)} rows x {len(table.columns)} cols")
    for ri, row in enumerate(table.rows[:8]):
        cells = [c.text.strip().replace("\n", " ")[:40] for c in row.cells]
        print(f"  r{ri}: {cells}")

print("\n=== CONTENTS AREA (first 80 non-empty after CONTENTS) ===")
for i, para in enumerate(d.paragraphs):
    if (para.text or "").strip().startswith("CONTENTS"):
        for j in range(i, min(i + 40, len(d.paragraphs))):
            t = (d.paragraphs[j].text or "").strip()
            if t:
                print(f"{j}: {t[:120]}")
        break

print("\n=== AROUND LIST OF FIGURES ===")
for i, para in enumerate(d.paragraphs):
    t = (para.text or "").strip()
    if "List of Figures" in t or "List of Tables" in t:
        for j in range(max(0, i - 2), min(len(d.paragraphs), i + 15)):
            tt = (d.paragraphs[j].text or "").strip()
            has = bool(d.paragraphs[j]._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'))
            st = d.paragraphs[j].style.name if d.paragraphs[j].style else ""
            print(f"{j}: [{st}] {repr(tt[:90])} {'IMG' if has else ''}")
        print("---")
