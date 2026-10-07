"""Locate tables in document body order vs paragraphs."""
from docx import Document
from docx.oxml.ns import qn

doc = Document(r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx")
body = doc.element.body

para_map = {p._p: (i, (p.text or "")[:60]) for i, p in enumerate(doc.paragraphs)}
table_map = {t._tbl: ti for ti, t in enumerate(doc.tables)}

print("BODY ORDER (paragraphs + tables):")
idx = 0
for child in body.iterchildren():
    tag = child.tag.split("}")[-1]
    if tag == "p":
        i, t = para_map.get(child, (-1, "?"))
        tt = (t or "").strip()
        if tt or True:
            # show only meaningful
            if tt.startswith(("List of", "CONTENTS", "CHAPTER", "ABSTRACT", "CERTIFICATE", "ACKNOWLEDGEMENT", "REFERENCES", "CANDIDATE", "4.", "Fig.", "Table")) or i in (63, 64, 65, 66, 67):
                print(f"P[{i}] {tt[:80]}")
    elif tag == "tbl":
        ti = table_map.get(child, -1)
        print(f"*** TABLE[{ti}] here ***")
        # show first cell
        rows = doc.tables[ti].rows
        print(f"    first row: {[c.text[:30] for c in rows[0].cells]}")
        if len(rows) > 1:
            print(f"    second: {[c.text[:30] for c in rows[1].cells]}")

# pageBreakBefore flags
print("\nPAGE BREAK BEFORE:")
for i, p in enumerate(doc.paragraphs):
    pPr = p._p.pPr
    if pPr is not None:
        for child in pPr:
            if child.tag == qn("w:pageBreakBefore"):
                print(i, (p.text or "")[:70])

# Check empty paras after LoF
print("\nWords:", sum(len((p.text or "").split()) for p in doc.paragraphs))
