"""
Shorten theory to ~30 pages, keep figures, fix TOC/LoF page numbers from Word walk.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Pt

SRC = Path(r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx")
BODY_PT = 14


def set_run_font(run, size_pt=BODY_PT, bold=None):
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


def replace_paragraph_text(paragraph, text):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
        set_run_font(paragraph.runs[0], BODY_PT)
    else:
        run = paragraph.add_run(text)
        set_run_font(run, BODY_PT)


def delete_paragraph(paragraph):
    el = paragraph._p
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)


def find_startswith(doc, needle):
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").strip().startswith(needle):
            return i
    return None


def find_exact(doc, text):
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").strip() == text:
            return i
    return None


def dotted(title, page, width=88):
    page = str(page)
    dots = max(3, width - len(title) - len(page))
    return f"{title} {'.' * dots} {page}"


def shorten_theory(doc):
    """
    Keep core project work 4.1-4.17 (+ figures).
    Keep one short compact notes section.
    Remove 4.18-4.41 heavy theory except a small compact block.
    """
    # Delete from 4.18 through just before CHAPTER 5, then add one short section back
    start = find_startswith(doc, "4.18")
    end = find_startswith(doc, "CHAPTER 5:")
    if start is not None and end is not None and start < end:
        for i in range(end - 1, start - 1, -1):
            p = doc.paragraphs[i]
            if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
                continue
            delete_paragraph(p)

    # Also remove 4.14-4.16 if still long? Keep 4.14-4.17 as useful but shorten bodies of 4.14-4.16 to 1 para each
    for head in ("4.14 ", "4.15 ", "4.16 "):
        idx = find_startswith(doc, head)
        if idx is None:
            continue
        bodies = []
        j = idx + 1
        while j < len(doc.paragraphs):
            p = doc.paragraphs[j]
            t = (p.text or "").strip()
            st = p.style.name if p.style else ""
            if st.startswith("Heading") or t.startswith("CHAPTER"):
                break
            if t and not p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
                bodies.append(j)
            j += 1
        for bi in reversed(bodies[1:]):
            delete_paragraph(doc.paragraphs[bi])

    # Insert short closing notes before CHAPTER 5 if missing
    if find_startswith(doc, "4.18 Project Notes") is None:
        ch5 = find_startswith(doc, "CHAPTER 5:")
        j = ch5 - 1
        while j > 0 and not (doc.paragraphs[j].text or "").strip():
            j -= 1
        # insert via XML
        from docx.oxml import OxmlElement
        from docx.text.paragraph import Paragraph

        def add_after(paragraph, text, style="Normal", bold=False):
            new_p = OxmlElement("w:p")
            paragraph._p.addnext(new_p)
            para = Paragraph(new_p, paragraph._parent)
            try:
                para.style = doc.styles[style]
            except Exception:
                pass
            run = para.add_run(text)
            set_run_font(run, BODY_PT, bold=bold)
            try:
                para.paragraph_format.line_spacing = 1.5
                para.paragraph_format.space_after = Pt(8)
            except Exception:
                pass
            return para

        cur = doc.paragraphs[j]
        cur = add_after(cur, "4.18 Project Notes", style="Heading 2", bold=True)
        cur = add_after(
            cur,
            "The ESP32-CAM streams live video to a browser where TensorFlow.js COCO-SSD detects objects. "
            "Only dog detections above about 55% confidence are used. An optional DETECT ZONE restricts alerts to a selected area. "
            "Valid detection turns relay (GPIO12) and flash (GPIO4) ON for 7 seconds, then rechecks. "
            "This completes the training project pipeline from camera sensing to alert actuation.",
        )
        cur = add_after(
            cur,
            "Testing covered live stream, dog-only filtering, in-zone/out-of-zone behavior, hold timing, and manual flash control. "
            "Limitations include lighting dependence and general-model accuracy. Future work may use a custom model and outdoor enclosure.",
        )


def apply_pages(doc, pages: dict):
    def p(key, default):
        v = pages.get(key)
        return default if v in (None, "None", "") else v

    # Roman for front if page numbers are arabic from Word start - convert roughly:
    # Word counted from doc start including cover. Use values as returned.
    toc = [
        ("Candidate's Declaration", p("CANDIDATE'S DECLARATION", "i")),
        ("Certificate", p("CERTIFICATE", "ii")),
        ("Acknowledgement", p("ACKNOWLEDGEMENT", "iii")),
        ("Abstract", p("ABSTRACT", "iv")),
        ("Contents", p("CONTENTS", "v")),
        ("List of Figures", p("List of Figures", "vi")),
        ("List of Tables", p("List of Tables", "vii")),
        ("Chapter 1: Introduction", p("CHAPTER 1: INTRODUCTION", "1")),
        ("Chapter 2: Company Infrastructure", p("CHAPTER 2: COMPANY INFRASTRUCTURE", "3")),
        ("Chapter 3: Training Attended", p("CHAPTER 3: TRAINING ATTENDED", "5")),
        ("Chapter 4: Systems / Project Development", p("CHAPTER 4: SYSTEMS/PROJECT DEVELOPMENT", "8")),
        ("Chapter 5: Results and Conclusion", p("CHAPTER 5: RESULTS AND CONCLUSION", "22")),
        ("References", p("REFERENCES", "27")),
    ]

    contents = find_exact(doc, "CONTENTS")
    lof = find_exact(doc, "List of Figures")
    if contents is not None and lof is not None and contents < lof:
        # update dotted lines only in this range
        for i in range(contents + 1, lof):
            t = (doc.paragraphs[i].text or "").strip()
            if "...." not in t and "..." not in t:
                continue
            for title, page in toc:
                if t.startswith(title):
                    replace_paragraph_text(doc.paragraphs[i], dotted(title, page))
                    break

    if len(doc.tables) >= 1:
        t0 = doc.tables[0]
        figs = [
            ("Fig. 4.1", "ESP32-CAM hardware concept", str(p("Fig. 4.1", "15"))),
            ("Fig. 4.2", "System architecture of dog detection alert system", str(p("Fig. 4.2", "16"))),
            ("Fig. 4.3", "Detection and relay-hold workflow", str(p("Fig. 4.3", "17"))),
            ("Fig. 4.4", "Monitoring UI with DETECT ZONE and dog box", str(p("Fig. 4.4", "18"))),
        ]
        while len(t0.rows) < 5:
            t0.add_row()
        for i, (a, b, c) in enumerate(figs, start=1):
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
        t1.rows[1].cells[2].text = str(p("Table 4.1", "12"))
        t1.rows[2].cells[0].text = "Table 4.2"
        t1.rows[2].cells[1].text = "GPIO pin mapping (Relay/Flash)"
        t1.rows[2].cells[2].text = str(p("Table 4.2", "14"))


def get_word_pages():
    ps1 = Path(r"c:\Users\umesh\OneDrive\Documents\Arduino\CameraWebServer\_word_pages2.ps1")
    r = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        capture_output=True,
        text=True,
    )
    pages = {}
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            pages[k] = v
    print("Word output:", r.stdout)
    if r.stderr:
        print("Word stderr:", r.stderr[:500])
    return pages


def main():
    doc = Document(str(SRC))
    shorten_theory(doc)
    doc.save(str(SRC))

    pages = get_word_pages()
    total = int(pages.get("TOTAL_PAGES", "0") or 0)
    print("total pages after shorten:", total)

    # If still > 32, trim more from chapter 3/4 long bodies carefully - skip figures
    if total > 32:
        doc = Document(str(SRC))
        # shorten 4.11 bullet list? keep
        # Remove 4.14-4.17 bodies extras already done
        # Trim acknowledgement? no
        # Remove compact 4.18 second para only if needed
        pass

    # Convert Word absolute pages into TOC-friendly numbers.
    # If document has cover pages, chapters may start at page 6+. For TOC chapter pages,
    # use actual Word page numbers as printed (common for simple reports).
    doc = Document(str(SRC))
    apply_pages(doc, pages)
    doc.save(str(SRC))

    # Re-measure
    pages2 = get_word_pages()
    print("Final TOTAL:", pages2.get("TOTAL_PAGES"))
    print("Final chapter pages:", {k: pages2.get(k) for k in pages2 if k.startswith("CHAPTER") or k in ("List of Figures", "REFERENCES", "Fig. 4.1", "TOTAL_PAGES")})

    doc = Document(str(SRC))
    print("words", sum(len((p.text or "").split()) for p in doc.paragraphs))
    print("has figures section", find_startswith(doc, "4.13") is not None)
    print("lof exact", find_exact(doc, "List of Figures"))
    imgs = sum(1 for p in doc.paragraphs if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'))
    print("images", imgs)


if __name__ == "__main__":
    main()
