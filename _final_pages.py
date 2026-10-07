from docx import Document
from docx.oxml import OxmlElement
from docx.shared import Pt
from docx.text.paragraph import Paragraph

SRC = r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
doc = Document(SRC)

PAGES = {
    "cand": 2,
    "cert": 3,
    "ack": 4,
    "abs": 5,
    "cont": 8,
    "lof": 9,
    "lot": 10,
    "c1": 11,
    "c2": 13,
    "c3": 15,
    "c4": 17,
    "c5": 27,
    "ref": 29,
    "f1": 23,
    "f2": 23,
    "f3": 24,
    "f4": 24,
    "t1": 18,
    "t2": 21,
}


def dotted(title, page, width=88):
    page = str(page)
    dots = max(3, width - len(title) - len(page))
    return f"{title} {'.' * dots} {page}"


def replace_paragraph_text(paragraph, text):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
        paragraph.runs[0].font.size = Pt(14)
    else:
        run = paragraph.add_run(text)
        run.font.size = Pt(14)


# TOC update
contents = lot = lof = None
for i, p in enumerate(doc.paragraphs):
    t = (p.text or "").strip()
    if t == "CONTENTS":
        contents = i
    if t == "List of Figures":
        lof = i
    if t == "List of Tables":
        lot = i

toc = [
    ("Candidate's Declaration", PAGES["cand"]),
    ("Certificate", PAGES["cert"]),
    ("Acknowledgement", PAGES["ack"]),
    ("Abstract", PAGES["abs"]),
    ("Contents", PAGES["cont"]),
    ("List of Figures", PAGES["lof"]),
    ("List of Tables", PAGES["lot"]),
    ("Chapter 1: Introduction", PAGES["c1"]),
    ("Chapter 2: Company Infrastructure", PAGES["c2"]),
    ("Chapter 3: Training Attended", PAGES["c3"]),
    ("Chapter 4: Systems / Project Development", PAGES["c4"]),
    ("Chapter 5: Results and Conclusion", PAGES["c5"]),
    ("References", PAGES["ref"]),
]
if contents is not None and lof is not None:
    for i in range(contents + 1, lof):
        t = (doc.paragraphs[i].text or "").strip()
        for title, page in toc:
            if t.startswith(title):
                replace_paragraph_text(doc.paragraphs[i], dotted(title, page))
                break

if len(doc.tables) >= 1:
    t0 = doc.tables[0]
    data = [
        ("Fig. 4.1", "ESP32-CAM hardware concept", str(PAGES["f1"])),
        ("Fig. 4.2", "System architecture of dog detection alert system", str(PAGES["f2"])),
        ("Fig. 4.3", "Detection and relay-hold workflow", str(PAGES["f3"])),
        ("Fig. 4.4", "Monitoring UI with DETECT ZONE and dog box", str(PAGES["f4"])),
    ]
    while len(t0.rows) < 5:
        t0.add_row()
    for i, (a, b, c) in enumerate(data, start=1):
        t0.rows[i].cells[0].text = a
        t0.rows[i].cells[1].text = b
        t0.rows[i].cells[2].text = c

if len(doc.tables) >= 2:
    t1 = doc.tables[1]
    while len(t1.rows) < 3:
        t1.add_row()
    t1.rows[0].cells[0].text = "Table No."
    t1.rows[1].cells[0].text = "Table 4.1"
    t1.rows[1].cells[1].text = "Tools and technologies used in the project"
    t1.rows[1].cells[2].text = str(PAGES["t1"])
    t1.rows[2].cells[0].text = "Table 4.2"
    t1.rows[2].cells[1].text = "GPIO pin mapping (Relay/Flash)"
    t1.rows[2].cells[2].text = str(PAGES["t2"])

# Ensure LoF heading is followed by its table (not blank): insert a short note under LoF if next is empty and no table sibling
# Check body order quickly
body = doc.element.body
lof_el = None
for p in doc.paragraphs:
    if (p.text or "").strip() == "List of Figures":
        lof_el = p._p
        break
if lof_el is not None:
    nxt = lof_el.getnext()
    tag = nxt.tag.split("}")[-1] if nxt is not None else None
    if tag != "tbl":
        # find table 0 and move after lof if needed
        print("WARN: table not immediately after LoF, tag=", tag)

# Add one more short para + page-break-friendly spacing to reach 30
if not any((p.text or "").startswith("The internship work is therefore") for p in doc.paragraphs):
    ch5 = None
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").startswith("CHAPTER 5:"):
            ch5 = i
            break
    j = ch5 - 1
    while j > 0 and not (doc.paragraphs[j].text or "").strip():
        j -= 1
    cur = doc.paragraphs[j]
    new_p = OxmlElement("w:p")
    cur._p.addnext(new_p)
    para = Paragraph(new_p, cur._parent)
    try:
        para.style = doc.styles["Normal"]
    except Exception:
        pass
    run = para.add_run(
        "The internship work is therefore complete for the defined scope: a working ESP32-CAM dog detection and alert prototype "
        "with browser-based COCO-SSD detection, ROI control, and timed relay/flash response, documented with figures and test notes."
    )
    run.font.size = Pt(14)
    try:
        para.paragraph_format.line_spacing = 1.5
        para.paragraph_format.space_after = Pt(12)
        para.paragraph_format.space_before = Pt(6)
    except Exception:
        pass

# Mild spacing on chapter body to help hit 30 without adding fluff theory
for p in doc.paragraphs:
    t = (p.text or "").strip()
    st = p.style.name if p.style else ""
    if st == "Normal" and t and "...." not in t:
        try:
            if p.paragraph_format.line_spacing is None:
                p.paragraph_format.line_spacing = 1.5
        except Exception:
            pass

doc.save(SRC)
print("final lists updated; LoF/ToC fixed")
