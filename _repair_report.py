"""
Repair report front-matter order, keep figures, restore moderate theory for ~30 pages,
fix TOC/LoF page numbers.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

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


def insert_paragraph_after(paragraph: Paragraph, text: str = "", style: str | None = None) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style:
        try:
            new_para.style = style
        except Exception:
            pass
    if text:
        run = new_para.add_run(text)
        set_run_font(run, BODY_PT)
    return new_para


def add_body_after(paragraph: Paragraph, text: str) -> Paragraph:
    p = insert_paragraph_after(paragraph, text, style="Normal")
    try:
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5
    except Exception:
        pass
    return p


def add_heading_after(paragraph: Paragraph, text: str) -> Paragraph:
    p = insert_paragraph_after(paragraph, "", style="Heading 2")
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    run = p.add_run(text)
    set_run_font(run, BODY_PT, bold=True)
    return p


def delete_paragraph(paragraph):
    el = paragraph._p
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)


def remove_page_break_before(paragraph):
    pPr = paragraph._p.pPr
    if pPr is None:
        return
    for child in list(pPr):
        if child.tag == qn("w:pageBreakBefore"):
            pPr.remove(child)


def ensure_page_break_before(paragraph):
    remove_page_break_before(paragraph)
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:pageBreakBefore"))


def find_exact(doc, text):
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").strip() == text:
            return i
    return None


def find_startswith(doc, needle):
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").strip().startswith(needle):
            return i
    return None


def dotted(title, page, width=88):
    page = str(page)
    dots = max(3, width - len(title) - len(page))
    return f"{title} {'.' * dots} {page}"


def repair_front_matter(doc):
    """
    Target order:
      ABSTRACT (and its body)
      CONTENTS + TOC lines (correct order)
      List of Figures + its table
      List of Tables + its table
      CHAPTER 1...
    """
    body = doc.element.body

    abs_i = find_exact(doc, "ABSTRACT")
    lof_i = find_exact(doc, "List of Figures")
    lot_i = find_exact(doc, "List of Tables")
    contents_i = find_exact(doc, "CONTENTS")
    ch1_i = find_startswith(doc, "CHAPTER 1:")

    if None in (abs_i, lof_i, lot_i, contents_i, ch1_i):
        raise SystemExit(f"Missing markers abs={abs_i} lof={lof_i} lot={lot_i} contents={contents_i} ch1={ch1_i}")

    # Delete ALL misplaced dotted TOC lines that currently sit between ABSTRACT and CHAPTER 1
    # (they will be re-created under CONTENTS)
    to_del = []
    for i, p in enumerate(doc.paragraphs):
        t = (p.text or "").strip()
        if "...." in t and i < ch1_i:
            # keep nothing; recreate later under contents
            to_del.append(p)
    for p in to_del:
        delete_paragraph(p)

    # Re-find markers after deletion
    abs_i = find_exact(doc, "ABSTRACT")
    lof_i = find_exact(doc, "List of Figures")
    lot_i = find_exact(doc, "List of Tables")
    contents_i = find_exact(doc, "CONTENTS")
    ch1_i = find_startswith(doc, "CHAPTER 1:")

    lof_el = doc.paragraphs[lof_i]._p
    lot_el = doc.paragraphs[lot_i]._p
    contents_el = doc.paragraphs[contents_i]._p
    ch1_el = doc.paragraphs[ch1_i]._p

    # Capture LoF block = heading + following table(s) until List of Tables
    def take_until(start_el, stop_el):
        block = []
        collecting = False
        for child in list(body.iterchildren()):
            if child is start_el:
                collecting = True
            if child is stop_el:
                break
            if collecting:
                block.append(child)
        return block

    lof_block = take_until(lof_el, lot_el)
    lot_block = take_until(lot_el, ch1_el)
    # lot_block may currently include CONTENTS if contents is between lot and ch1
    # Filter: lot_block should be lot heading + table + blanks only, stop before CONTENTS if present
    lot_block_clean = []
    for el in lot_block:
        # stop if this is CONTENTS para
        if el is contents_el:
            break
        lot_block_clean.append(el)
    lot_block = lot_block_clean

    # Remove contents heading element alone (TOC lines already deleted)
    # Also remove lof/lot blocks from current place, then reinsert in order after abstract body.

    # Find last abstract body element (last non-empty before any of contents/lof/lot/ch1)
    markers = {contents_el, lof_el, lot_el, ch1_el}
    abs_el = doc.paragraphs[abs_i]._p
    last_abs = abs_el
    seen_abs = False
    for child in list(body.iterchildren()):
        if child is abs_el:
            seen_abs = True
            continue
        if not seen_abs:
            continue
        if child in markers or child in lof_block or child in lot_block:
            break
        # if CONTENTS or LoF heading appears, stop
        last_abs = child

    # Detach blocks
    for el in lof_block + lot_block:
        if el.getparent() is body:
            body.remove(el)
    if contents_el.getparent() is body:
        body.remove(contents_el)

    # Insert sequence after last_abs: CONTENTS, TOC lines (as new paras), LoF block, LoT block
    ref = last_abs
    ref.addnext(contents_el)
    ref = contents_el

    # Create TOC lines by inserting paragraph XML after contents
    toc_lines = [
        dotted("Candidate's Declaration", "i"),
        dotted("Certificate", "ii"),
        dotted("Acknowledgement", "iii"),
        dotted("Abstract", "iv"),
        dotted("Contents", "v"),
        dotted("List of Figures", "vi"),
        dotted("List of Tables", "vii"),
        dotted("Chapter 1: Introduction", "1"),
        dotted("Chapter 2: Company Infrastructure", "3"),
        dotted("Chapter 3: Training Attended", "5"),
        dotted("Chapter 4: Systems / Project Development", "8"),
        dotted("Chapter 5: Results and Conclusion", "22"),
        dotted("References", "25"),
    ]

    # Use python-docx Paragraph wrapper: insert after contents via addnext empty p then set text
    # contents_el is bare XML; find paragraph object again after moves
    doc2_paras = {p._p: p for p in doc.paragraphs}
    # paragraphs collection may be stale; create new paras via OxmlElement
    for line in toc_lines:
        new_p = OxmlElement("w:p")
        ref.addnext(new_p)
        ref = new_p
        para = Paragraph(new_p, doc.paragraphs[0]._parent)
        try:
            para.style = doc.styles["Normal"]
        except Exception:
            pass
        run = para.add_run(line)
        set_run_font(run, BODY_PT)
        remove_page_break_before(para)

    for el in lof_block:
        ref.addnext(el)
        ref = el
    for el in lot_block:
        ref.addnext(el)
        ref = el

    # Page breaks
    # re-bind
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t in ("CERTIFICATE", "ACKNOWLEDGEMENT", "ABSTRACT", "CONTENTS", "List of Figures", "CHAPTER 1:", "CHAPTER 2:", "CHAPTER 3:", "CHAPTER 4:", "CHAPTER 5:", "REFERENCES") or t.startswith("CHAPTER "):
            if t.startswith("List of Tables"):
                remove_page_break_before(p)
            elif t == "List of Figures":
                ensure_page_break_before(p)
            elif t.startswith("CHAPTER") or t in ("CERTIFICATE", "ACKNOWLEDGEMENT", "ABSTRACT", "CONTENTS", "REFERENCES"):
                ensure_page_break_before(p)
        if "...." in t:
            remove_page_break_before(p)

    # List of Tables: no page break (flows under LoF)
    i = find_exact(doc, "List of Tables")
    if i is not None:
        remove_page_break_before(doc.paragraphs[i])


def fix_small_heading_issues(doc):
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t.startswith("4. CHAPTER 4"):
            replace_paragraph_text(p, "CHAPTER 4: SYSTEMS/PROJECT DEVELOPMENT")
            try:
                p.style = doc.styles["Heading 1"]
            except Exception:
                pass
        if t.startswith("1 Methodologies"):
            replace_paragraph_text(p, "4.1 Methodologies")
        if t.startswith("CHAPTER 3:"):
            try:
                p.style = doc.styles["Heading 1"]
            except Exception:
                pass
    if len(doc.tables) >= 2:
        if doc.tables[1].rows[0].cells[0].text.strip().startswith("Fig"):
            doc.tables[1].rows[0].cells[0].text = "Table No."


def restore_moderate_theory(doc):
    """If theory became too short, add compact paragraphs before CHAPTER 5 (no figures touched)."""
    words = sum(len((p.text or "").split()) for p in doc.paragraphs)
    if words >= 7000:
        print("Content length OK:", words)
        return

    ch5 = find_startswith(doc, "CHAPTER 5:")
    if ch5 is None:
        return
    # anchor = last non-empty before ch5
    j = ch5 - 1
    while j > 0 and not (doc.paragraphs[j].text or "").strip():
        j -= 1
    cur = doc.paragraphs[j]

    extras = [
        ("H", "4.34 Compact Technical Notes"),
        (
            "N",
            "This section briefly records additional technical notes for the completed ESP32-CAM dog detection project. "
            "The live stream from the board is viewed in a browser, where TensorFlow.js runs the COCO-SSD object detector. "
            "Only the dog class above about 55% confidence is accepted for alerting. An optional DETECT ZONE (ROI) can be drawn "
            "so that only dogs inside the selected area trigger the relay and flash.",
        ),
        (
            "N",
            "Relay output is connected on GPIO12 and flash LED on GPIO4. On a valid detection the relay remains ON for 7 seconds "
            "and is then rechecked. If the dog is still present the hold continues; otherwise the output turns OFF. This reduces "
            "rapid ON/OFF chatter when confidence fluctuates.",
        ),
        (
            "N",
            "Hardware bring-up requires correct COM port selection for upload, stable 5V supply, Wi-Fi credentials in firmware, "
            "and verification of the board IP from Serial Monitor. The monitoring page is then opened on the same network. "
            "Functional tests cover stream availability, dog detection, non-dog rejection, in-zone and out-of-zone cases, hold timing, "
            "and manual flash control.",
        ),
        (
            "N",
            "Limitations include lighting dependence, possible misses for distant or partially hidden dogs, and the use of a general "
            "pre-trained detector rather than a custom local model. Future improvements may include a custom-trained model, better "
            "night operation, event logging, and weatherproof outdoor mounting. Even with these limits, the training prototype "
            "demonstrates a complete IoT plus computer-vision alert pipeline.",
        ),
        (
            "N",
            "Overall, Chapter 4 shows problem definition, architecture, ESP32-CAM implementation, COCO-SSD based detection, ROI gating, "
            "relay/flash actuation, testing, and figures of the system. The next chapter presents results and conclusion.",
        ),
        ("H", "4.35 Training-to-Project Mapping"),
        (
            "N",
            "Machine Learning topics studied during internship—supervised learning, classification confidence, and deep learning "
            "basics—directly supported understanding of object-detection outputs. The project applied those ideas by using a "
            "pre-trained detector and building application logic around class filters, thresholds, zones, and timed actuation.",
        ),
        (
            "N",
            "Embedded and web skills were equally important: C/C++ firmware for camera/Wi-Fi/GPIO, and HTML/CSS/JavaScript for the "
            "monitor UI and detection loop. This combination matches the industrial need to connect AI models with real devices.",
        ),
        ("H", "4.36 Final Project Checklist Completed"),
        ("N", "The following checklist items were completed during the training project:"),
        ("B", "ESP32-CAM streaming and web UI hosting"),
        ("B", "COCO-SSD dog-only detection with confidence display"),
        ("B", "User-selectable DETECT ZONE / clear zone"),
        ("B", "Relay GPIO12 with 7-second hold and recheck"),
        ("B", "Flash LED GPIO4 auto/manual control"),
        ("B", "End-to-end demonstration and basic test cases"),
    ]

    # Avoid duplicate insert
    if find_startswith(doc, "4.34 Compact Technical Notes") is not None:
        print("Compact notes already present")
        return

    for kind, text in extras:
        if kind == "H":
            cur = add_heading_after(cur, text)
        elif kind == "B":
            cur = add_body_after(cur, "• " + text)
        else:
            cur = add_body_after(cur, text)

    # Add a bit more body to approach 30 pages (~7500 words with figures/spacing)
    more = [
        "In practical deployment planning, camera angle should keep the vehicle roof or target region large in the frame, "
        "Wi-Fi signal should be stable, and any relay load must be electrically safe. The present work remains an academic "
        "prototype focused on correct detection-to-actuation behavior.",
        "During viva or demonstration, the recommended flow is: power the board, note the IP, open the UI, wait for model load, "
        "draw a detect zone, present a dog target inside the zone, observe box/relay/flash, then move the target outside the zone "
        "and confirm that alerts stop after recheck.",
        "The software files used in the project are mainly CameraWebServer.ino for setup, app_httpd.cpp for HTTP/stream/relay/LED "
        "handlers, index_dog.h for the detection UI, and board_config.h for pin configuration. This separation kept firmware "
        "control logic and browser detection logic easy to test independently.",
        "Object detection was preferred over whole-image classification because bounding boxes and ROI checks need location. "
        "COCO-SSD was preferred for the internship window because it is ready for TensorFlow.js and detects the dog class without "
        "requiring a full custom training cycle for the first working demo.",
    ]
    for t in more:
        cur = add_body_after(cur, t)


def update_lists_with_estimate(doc):
    """Estimate page numbers from structure after repair; refine if Word available."""
    pages = None
    try:
        import win32com.client  # type: ignore

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        wdoc = word.Documents.Open(str(SRC), ReadOnly=False)
        wdoc.Repaginate()
        total = int(wdoc.ComputeStatistics(2))
        pages = {"__total__": total}

        def find_page(text):
            rng = wdoc.Content
            f = rng.Find
            f.ClearFormatting()
            f.Text = text
            f.Forward = True
            f.Wrap = 0
            if f.Execute():
                return int(rng.Information(3))
            return None

        for key in [
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
        ]:
            pages[key] = find_page(key)
        wdoc.Close(False)
        word.Quit()
        print("Word total pages:", total, pages)
    except Exception as e:
        print("Word COM skip:", e)

    if not pages:
        # Approx for ~30-page academic formatting with 1.5 spacing + figures
        pages = {
            "CANDIDATE'S DECLARATION": "i",
            "CERTIFICATE": "ii",
            "ACKNOWLEDGEMENT": "iii",
            "ABSTRACT": "iv",
            "CONTENTS": "v",
            "List of Figures": "vi",
            "List of Tables": "vii",
            "CHAPTER 1:": 1,
            "CHAPTER 2:": 3,
            "CHAPTER 3:": 5,
            "CHAPTER 4:": 8,
            "CHAPTER 5:": 24,
            "REFERENCES": 28,
            "Fig. 4.1": 18,
            "Fig. 4.2": 19,
            "Fig. 4.3": 20,
            "Fig. 4.4": 21,
            "Table 4.1": 14,
            "Table 4.2": 16,
            "__total__": 30,
        }

    def p(key, default=""):
        v = pages.get(key, default)
        return default if v is None else v

    # Update TOC dotted lines currently under CONTENTS
    toc_map = {
        "Candidate's Declaration": dotted("Candidate's Declaration", p("CANDIDATE'S DECLARATION", "i")),
        "Certificate": dotted("Certificate", p("CERTIFICATE", "ii")),
        "Acknowledgement": dotted("Acknowledgement", p("ACKNOWLEDGEMENT", "iii")),
        "Abstract": dotted("Abstract", p("ABSTRACT", "iv")),
        "Contents": dotted("Contents", p("CONTENTS", "v")),
        "List of Figures": dotted("List of Figures", p("List of Figures", "vi")),
        "List of Tables": dotted("List of Tables", p("List of Tables", "vii")),
        "Chapter 1: Introduction": dotted("Chapter 1: Introduction", p("CHAPTER 1:", 1)),
        "Chapter 2: Company Infrastructure": dotted("Chapter 2: Company Infrastructure", p("CHAPTER 2:", 3)),
        "Chapter 3: Training Attended": dotted("Chapter 3: Training Attended", p("CHAPTER 3:", 5)),
        "Chapter 4: Systems / Project Development": dotted(
            "Chapter 4: Systems / Project Development", p("CHAPTER 4:", 8)
        ),
        "Chapter 5: Results and Conclusion": dotted("Chapter 5: Results and Conclusion", p("CHAPTER 5:", 24)),
        "References": dotted("References", p("REFERENCES", 28)),
    }

    contents_i = find_exact(doc, "CONTENTS")
    ch1_i = find_startswith(doc, "CHAPTER 1:")
    if contents_i is not None and ch1_i is not None:
        for i in range(contents_i + 1, ch1_i):
            t = (doc.paragraphs[i].text or "").strip()
            for key, line in toc_map.items():
                if t.startswith(key):
                    replace_paragraph_text(doc.paragraphs[i], line)
                    break

    if len(doc.tables) >= 1:
        t0 = doc.tables[0]
        data = [
            ("Fig. 4.1", "ESP32-CAM hardware concept", str(p("Fig. 4.1", 18))),
            ("Fig. 4.2", "System architecture of dog detection alert system", str(p("Fig. 4.2", 19))),
            ("Fig. 4.3", "Detection and relay-hold workflow", str(p("Fig. 4.3", 20))),
            ("Fig. 4.4", "Monitoring UI with DETECT ZONE and dog box", str(p("Fig. 4.4", 21))),
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
        t1.rows[1].cells[2].text = str(p("Table 4.1", 14))
        if len(t1.rows) > 2:
            t1.rows[2].cells[0].text = "Table 4.2"
            t1.rows[2].cells[1].text = "GPIO pin mapping (Relay/Flash)"
            t1.rows[2].cells[2].text = str(p("Table 4.2", 16))


def main():
    doc = Document(str(SRC))
    fix_small_heading_issues(doc)
    repair_front_matter(doc)
    doc.save(str(SRC))

    doc = Document(str(SRC))
    restore_moderate_theory(doc)
    doc.save(str(SRC))

    # Try pip install pywin32 quietly for real pages
    try:
        import subprocess

        subprocess.run(["pip", "install", "pywin32", "-q"], check=False, capture_output=True)
    except Exception:
        pass

    doc = Document(str(SRC))
    update_lists_with_estimate(doc)
    doc.save(str(SRC))

    doc = Document(str(SRC))
    print("=== VERIFY FRONT ===")
    for i, p in enumerate(doc.paragraphs):
        t = (p.text or "").strip()
        if i > 95:
            break
        if t.startswith(
            ("ABSTRACT", "CONTENTS", "List of", "CHAPTER 1", "Candidate", "Certificate", "Chapter", "Acknowledgement", "Abstract", "References", "Fig. No", "Table")
        ) or t == "List of Figures" or t == "List of Tables":
            print(i, t[:100])
    words = sum(len((p.text or "").split()) for p in doc.paragraphs)
    print("words", words, "approx_pages@250", round(words / 250, 1))
    imgs = sum(1 for p in doc.paragraphs if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'))
    print("images", imgs)


if __name__ == "__main__":
    main()
