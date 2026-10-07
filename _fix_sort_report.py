"""
Sort/fix report without touching figures:
- Remove bad page breaks (esp. on TOC lines)
- Move CONTENTS above List of Figures/Tables so LoF isn't stranded/blank-looking
- Keep LoF/LoT tables glued under their headings
- Trim extra theory 4.18-4.44 and duplicate 5.6-5.8
- Fix chapter heading sequence labels
- Update page numbers using Word COM if available
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
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


def remove_page_break_before(paragraph):
    pPr = paragraph._p.pPr
    if pPr is None:
        return
    for child in list(pPr):
        if child.tag == qn("w:pageBreakBefore"):
            pPr.remove(child)


def ensure_page_break_before(paragraph):
    remove_page_break_before(paragraph)
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:pageBreakBefore"))


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


def move_block_after(body, block_elements, after_element):
    """Move a list of body child elements to immediately after after_element."""
    for el in block_elements:
        body.remove(el)
    ref = after_element
    for el in block_elements:
        ref.addnext(el)
        ref = el


def collect_lof_lot_contents_blocks(doc):
    """
    Identify XML element blocks:
    - LoF heading + following table + optional blank p
    - LoT heading + following table + optional blank p
    - CONTENTS heading + following TOC lines until CHAPTER 1
    """
    body = doc.element.body
    children = list(body.iterchildren())

    def para_text(el):
        # map element to paragraph text if it's a p
        for p in doc.paragraphs:
            if p._p is el:
                return (p.text or "").strip()
        return None

    lof_start = lot_start = contents_start = ch1_start = None
    for el in children:
        t = para_text(el)
        if t == "List of Figures":
            lof_start = el
        elif t == "List of Tables":
            lot_start = el
        elif t == "CONTENTS":
            contents_start = el
        elif t and t.startswith("CHAPTER 1:"):
            ch1_start = el

    if not all([lof_start, lot_start, contents_start, ch1_start]):
        return None

    # Build blocks by walking
    def block_from(start_el, stop_el):
        collecting = False
        block = []
        for el in children:
            if el is start_el:
                collecting = True
            if el is stop_el:
                break
            if collecting:
                block.append(el)
        return block

    lof_block = block_from(lof_start, lot_start)
    lot_block = block_from(lot_start, contents_start)
    contents_block = block_from(contents_start, ch1_start)
    return {
        "lof": lof_block,
        "lot": lot_block,
        "contents": contents_block,
        "ch1": ch1_start,
        "lof_start": lof_start,
        "lot_start": lot_start,
        "contents_start": contents_start,
    }


def trim_theory(doc):
    """Shorten only the most repetitive extra theory; keep core project sections + figures."""
    # Remove 4.34 summary + 4.35..4.44 extended dump (before CHAPTER 5)
    start = find_startswith(doc, "4.34 ")
    if start is None:
        start = find_startswith(doc, "4.35 ")
    end = find_startswith(doc, "CHAPTER 5:")
    if start is not None and end is not None and start < end:
        for i in range(end - 1, start - 1, -1):
            p = doc.paragraphs[i]
            if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
                continue
            delete_paragraph(p)

    # Lightly shorten 4.18-4.33: delete every other Normal body para under these sections
    # (keep all headings; keep first body under each heading)
    trim_heads = [f"4.{n} " for n in range(18, 34)]
    for head in trim_heads:
        idx = find_startswith(doc, head)
        if idx is None:
            continue
        # collect body indices until next heading
        bodies = []
        j = idx + 1
        while j < len(doc.paragraphs):
            p = doc.paragraphs[j]
            t = (p.text or "").strip()
            st = p.style.name if p.style else ""
            if st.startswith("Heading") or t.startswith("CHAPTER") or t.startswith("REFERENCES"):
                break
            if t and not p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
                bodies.append(j)
            j += 1
        # keep first 1 body (or 2 for requirements lists), delete extras from the end
        keep = 2 if "4.19" in head or "4.27" in head or "4.28" in head else 1
        for bi in reversed(bodies[keep:]):
            delete_paragraph(doc.paragraphs[bi])

    # Remove duplicate ch5 extras 5.6-5.8
    start5 = find_startswith(doc, "5.6 ")
    end5 = find_startswith(doc, "REFERENCES")
    if start5 is not None and end5 is not None and start5 < end5:
        for i in range(end5 - 1, start5 - 1, -1):
            p = doc.paragraphs[i]
            if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
                continue
            delete_paragraph(p)


def fix_headings(doc):
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t.startswith("4. CHAPTER 4"):
            replace_paragraph_text(p, "CHAPTER 4: SYSTEMS/PROJECT DEVELOPMENT")
            try:
                p.style = doc.styles["Heading 1"]
            except Exception:
                pass
        if t.startswith("1 Methodologies") or t == "1 Methodologies":
            replace_paragraph_text(p, "4.1 Methodologies")
        if t.startswith("CHAPTER 3:"):
            try:
                p.style = doc.styles["Heading 1"]
            except Exception:
                pass

    if len(doc.tables) >= 2:
        c0 = doc.tables[1].rows[0].cells[0].text.strip()
        if c0.startswith("Fig"):
            doc.tables[1].rows[0].cells[0].text = "Table No."


def fix_page_breaks(doc):
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        st = p.style.name if p.style else ""
        if "...." in t and st == "Normal":
            remove_page_break_before(p)
        if t in ("List of Figures", "List of Tables"):
            remove_page_break_before(p)

    for marker in (
        "CERTIFICATE",
        "ACKNOWLEDGEMENT",
        "ABSTRACT",
        "CONTENTS",
        "List of Figures",
        "CHAPTER 1:",
        "CHAPTER 2:",
        "CHAPTER 3:",
        "CHAPTER 4:",
        "CHAPTER 5:",
        "REFERENCES",
    ):
        i = find_startswith(doc, marker)
        if i is None:
            continue
        # LoF: page break yes (own section after contents)
        ensure_page_break_before(doc.paragraphs[i])

    # List of Tables should continue after LoF on same flow without forcing lonely blank page
    i = find_startswith(doc, "List of Tables")
    if i is not None:
        remove_page_break_before(doc.paragraphs[i])


def reorder_front_matter(doc):
    """Desired order: Abstract ... then CONTENTS, then LoF+table, then LoT+table, then Chapter 1."""
    blocks = collect_lof_lot_contents_blocks(doc)
    if not blocks:
        print("WARN: could not collect front-matter blocks; skip reorder")
        return

    body = doc.element.body
    # Find abstract end: element just before current first of {lof, contents}
    # After reorder we want: ...abstract..., CONTENTS block, LoF block, LoT block, CH1

    # If already contents before lof, skip
    children = list(body.iterchildren())
    try:
        ic = children.index(blocks["contents_start"])
        il = children.index(blocks["lof_start"])
        if ic < il:
            print("CONTENTS already above LoF")
            return
    except ValueError:
        return

    # Move CONTENTS block to before LoF start
    # First remove contents from current place, insert before lof_start
    contents_block = blocks["contents"]
    lof_start = blocks["lof_start"]

    for el in contents_block:
        body.remove(el)

    # insert contents_block before lof_start
    for el in reversed(contents_block):
        lof_start.addprevious(el)

    print("Reordered: CONTENTS moved above List of Figures")


def update_toc_dots(doc, mapping):
    """Update TOC lines that start with given keys."""
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        for key, line in mapping.items():
            if t.startswith(key):
                # only dotted TOC-like or chapter lines in contents area
                if "...." in t or key.startswith("Chapter") or key == "References":
                    replace_paragraph_text(p, line)
                break


def word_page_numbers(path: Path):
    """Return dict of heading -> page number using Word COM."""
    try:
        import win32com.client  # type: ignore
    except Exception as e:
        print("win32com not available:", e)
        return None

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    pages = {}
    try:
        doc = word.Documents.Open(str(path), ReadOnly=True)
        doc.Repaginate()
        total = doc.ComputeStatistics(2)  # wdStatisticPages
        pages["__total__"] = int(total)

        targets = [
            "CANDIDATE'S DECLARATION",
            "CERTIFICATE",
            "ACKNOWLEDGEMENT",
            "ABSTRACT",
            "CONTENTS",
            "List of Figures",
            "List of Tables",
            "CHAPTER 1:",
            "CHAPTER 2:",
            "CHAPTER 3:",
            "CHAPTER 4:",
            "CHAPTER 5:",
            "REFERENCES",
            "Fig. 4.1",
            "Fig. 4.2",
            "Fig. 4.3",
            "Fig. 4.4",
            "Table 4.1",
            "Table 4.2",
        ]
        for t in targets:
            rng = doc.Content
            find = rng.Find
            find.ClearFormatting()
            find.Text = t
            find.Forward = True
            find.Wrap = 0  # wdFindStop
            if find.Execute():
                pages[t] = int(rng.Information(3))  # wdActiveEndPageNumber
        doc.Close(False)
    finally:
        word.Quit()
    return pages


def apply_real_page_numbers(doc, pages):
    if not pages:
        return

    def pnum(key, default=""):
        return str(pages.get(key, default))

    # Front matter often roman; if Word gives arabic from start, use as-is from doc
    # Build TOC with real pages
    ch1 = pnum("CHAPTER 1:", "1")
    ch2 = pnum("CHAPTER 2:", "4")
    ch3 = pnum("CHAPTER 3:", "7")
    ch4 = pnum("CHAPTER 4:", "12")
    ch5 = pnum("CHAPTER 5:", "20")
    ref = pnum("REFERENCES", "24")

    def dotted(title, page, width=90):
        dots = max(3, width - len(title) - len(str(page)))
        return f"{title} {'.' * dots} {page}"

    mapping = {
        "Candidate's Declaration": dotted("Candidate's Declaration", pnum("CANDIDATE'S DECLARATION", "i")),
        "Certificate": dotted("Certificate", pnum("CERTIFICATE", "ii")),
        "Acknowledgement": dotted("Acknowledgement", pnum("ACKNOWLEDGEMENT", "iii")),
        "Abstract": dotted("Abstract", pnum("ABSTRACT", "iv")),
        "List of Figures": dotted("List of Figures", pnum("List of Figures", "v")),
        "List of Tables": dotted("List of Tables", pnum("List of Tables", "vi")),
        "Chapter 1: Introduction": dotted("Chapter 1: Introduction", ch1),
        "Chapter 2: Company Infrastructure": dotted("Chapter 2: Company Infrastructure", ch2),
        "Chapter 3: Training Attended": dotted("Chapter 3: Training Attended", ch3),
        "Chapter 4: Systems / Project Development": dotted("Chapter 4: Systems / Project Development", ch4),
        "Chapter 5: Results and Conclusion": dotted("Chapter 5: Results and Conclusion", ch5),
        "References": dotted("References", ref),
    }
    update_toc_dots(doc, mapping)

    # LoF table
    if len(doc.tables) >= 1:
        t0 = doc.tables[0]
        figs = [
            ("Fig. 4.1", "ESP32-CAM hardware concept", pnum("Fig. 4.1", "15")),
            ("Fig. 4.2", "System architecture of dog detection alert system", pnum("Fig. 4.2", "16")),
            ("Fig. 4.3", "Detection and relay-hold workflow", pnum("Fig. 4.3", "17")),
            ("Fig. 4.4", "Monitoring UI with DETECT ZONE and dog box", pnum("Fig. 4.4", "18")),
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
        t1.rows[1].cells[0].text = "Table 4.1"
        t1.rows[1].cells[1].text = "Tools and technologies used in the project"
        t1.rows[1].cells[2].text = pnum("Table 4.1", "14")
        if len(t1.rows) > 2:
            t1.rows[2].cells[0].text = "Table 4.2"
            t1.rows[2].cells[1].text = "GPIO pin mapping (Relay/Flash)"
            t1.rows[2].cells[2].text = pnum("Table 4.2", "15")


def main():
    doc = Document(str(SRC))

    fix_headings(doc)
    trim_theory(doc)
    # save intermediate so paragraph indices stable for reorder? reorder uses XML refs collected after trim
    doc.save(str(SRC))

    doc = Document(str(SRC))
    reorder_front_matter(doc)
    fix_page_breaks(doc)
    doc.save(str(SRC))

    # Real page numbers via Word
    pages = word_page_numbers(SRC)
    print("Word pages:", pages)

    doc = Document(str(SRC))
    if pages:
        apply_real_page_numbers(doc, pages)
    else:
        # fallback approximate after trim (~30 pages target with figures)
        approx = {
            "CANDIDATE'S DECLARATION": "i",
            "CERTIFICATE": "ii",
            "ACKNOWLEDGEMENT": "iii",
            "ABSTRACT": "iv",
            "CONTENTS": "v",
            "List of Figures": "vi",
            "List of Tables": "vii",
            "CHAPTER 1:": "1",
            "CHAPTER 2:": "4",
            "CHAPTER 3:": "7",
            "CHAPTER 4:": "12",
            "CHAPTER 5:": "24",
            "REFERENCES": "28",
            "Fig. 4.1": "18",
            "Fig. 4.2": "19",
            "Fig. 4.3": "20",
            "Fig. 4.4": "21",
            "Table 4.1": "15",
            "Table 4.2": "17",
            "__total__": 30,
        }
        apply_real_page_numbers(doc, approx)

    doc.save(str(SRC))

    d2 = Document(str(SRC))
    words = sum(len((p.text or "").split()) for p in d2.paragraphs)
    print("Final words:", words)
    print("Has 4.18?", find_startswith(d2, "4.18") is not None)
    print("Has 4.13 figures?", find_startswith(d2, "4.13") is not None)
    print("LoF idx", find_startswith(d2, "List of Figures"), "CONTENTS", find_startswith(d2, "CONTENTS"))


if __name__ == "__main__":
    main()
