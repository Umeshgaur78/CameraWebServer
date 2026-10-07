from docx import Document
from docx.oxml import OxmlElement
from docx.shared import Pt
from docx.text.paragraph import Paragraph

SRC = r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
doc = Document(SRC)

# bump length slightly toward 30 pages
found = any((p.text or "").startswith("4.20 Additional Summary") for p in doc.paragraphs)
if not found:
    ch5 = None
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").startswith("CHAPTER 5:"):
            ch5 = i
            break
    j = ch5 - 1
    while j > 0 and not (doc.paragraphs[j].text or "").strip():
        j -= 1
    cur = doc.paragraphs[j]

    def add_after(paragraph, text, style="Normal", bold=False):
        new_p = OxmlElement("w:p")
        paragraph._p.addnext(new_p)
        para = Paragraph(new_p, paragraph._parent)
        try:
            para.style = doc.styles[style]
        except Exception:
            pass
        run = para.add_run(text)
        run.font.size = Pt(14)
        run.font.bold = bold
        try:
            para.paragraph_format.line_spacing = 1.5
            para.paragraph_format.space_after = Pt(10)
        except Exception:
            pass
        return para

    cur = add_after(cur, "4.20 Additional Summary", style="Heading 2", bold=True)
    cur = add_after(
        cur,
        "In brief, the internship project successfully connected Machine Learning based object detection with an IoT camera node. "
        "ESP32-CAM provided sensing and actuation, while the browser provided COCO-SSD inference, ROI interaction, and alert timing. "
        "The result is a clear, demonstrable system suitable for academic evaluation of industrial training.",
    )
    cur = add_after(
        cur,
        "The sequence of work—from company learning modules to final relay/flash response—was kept practical and testable. "
        "This concludes the systems and project development chapter.",
    )

# Update LoF figure pages using caption-based estimates if needed (ch4:17-26)
# Will patch after PowerShell returns; set sensible defaults now
if len(doc.tables) >= 1:
    # keep existing unless we know better - leave for next step
    pass

doc.save(SRC)
print("padded")
