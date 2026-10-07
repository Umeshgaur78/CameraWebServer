"""
Expand report toward ~30 pages without changing fonts/colors/format.
Also fix abstract if still outdated.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

SRC = Path(r"c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx")
FIG_DIR = Path(r"c:\Users\umesh\OneDrive\Desktop\report_figures_umesh")
BODY_PT = 14


def set_run_font(run, size_pt=BODY_PT, bold=None):
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


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


def add_heading_after(paragraph: Paragraph, text: str, style: str) -> Paragraph:
    p = insert_paragraph_after(paragraph, "", style=style)
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    run = p.add_run(text)
    set_run_font(run, BODY_PT, bold=True)
    return p


def replace_paragraph_text(paragraph: Paragraph, text: str):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for r in paragraph.runs[1:]:
            r.text = ""
        set_run_font(paragraph.runs[0], BODY_PT)
    else:
        run = paragraph.add_run(text)
        set_run_font(run, BODY_PT)


def find_contains(doc: Document, needle: str) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        if needle in (p.text or ""):
            return i
    return None


def find_startswith(doc: Document, needle: str) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        if (p.text or "").strip().startswith(needle):
            return i
    return None


def add_picture_with_caption(after_para: Paragraph, img_path: Path, caption: str, width_in=5.4) -> Paragraph:
    p_img = insert_paragraph_after(after_para, "", style="Normal")
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Inches(width_in))
    p_cap = insert_paragraph_after(p_img, caption, style="Normal")
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p_cap.runs:
        set_run_font(p_cap.runs[0], BODY_PT, bold=True)
    return p_cap


def long_paras():
    """Return many Normal paragraphs (~18–20 pages worth at ~350 w/page)."""
    blocks = []

    def H(t):
        blocks.append(("H", t))

    def N(t):
        blocks.append(("N", t))

    def B(t):
        blocks.append(("B", t))

    H("4.18 Detailed Problem Analysis")
    N(
        "Stray animals near parked vehicles create repeated inconvenience for vehicle owners. Dogs often climb onto car roofs "
        "or sit on the bonnet in residential parking areas. Manual watching is not practical for long durations, especially "
        "during office hours or at night. A camera-based intelligent monitoring system can continuously observe the scene and "
        "raise an alert only when a dog is present in the critical region. This reduces false effort and provides a repeatable "
        "technical solution for a common local problem."
    )
    N(
        "The problem can be split into sensing, understanding, and acting. Sensing is performed by the ESP32-CAM video stream. "
        "Understanding is performed by object detection that identifies a dog and its location in the frame. Acting is performed "
        "by turning a relay and flash LED so that a deterrent or warning action can be started. The training project implemented "
        "all three stages in one connected pipeline."
    )
    N(
        "Important constraints of the problem are low cost, easy deployment, wireless monitoring, and immediate visual confirmation. "
        "ESP32-CAM satisfies the low-cost and wireless requirements. Browser-based TensorFlow.js satisfies easy monitoring without "
        "installing special desktop software on every viewing device. GPIO relay control satisfies the action requirement."
    )

    H("4.19 Requirement Specification")
    N("Functional requirements of the completed system are listed below:")
    B("The system shall stream live camera video from ESP32-CAM over Wi-Fi.")
    B("The system shall run object detection on the live stream using COCO-SSD in the browser.")
    B("The system shall accept only the dog class for alert decisions.")
    B("The system shall display a green bounding box and confidence percentage for accepted detections.")
    B("The system shall allow the user to draw a rectangular DETECT ZONE (ROI).")
    B("The system shall ignore dogs whose center point lies outside the selected zone.")
    B("The system shall turn the relay ON for 7 seconds on valid detection and then recheck.")
    B("The system shall support flash LED control automatically with alert and manually from UI.")
    N("Non-functional requirements considered during implementation include responsiveness of the stream, simplicity of UI operation, "
      "stable GPIO signaling, and maintainable separation between firmware and browser detection logic.")

    H("4.20 System Design Approach")
    N(
        "A hybrid design was selected. Heavy neural network inference runs on the client browser, while the ESP32 focuses on "
        "reliable streaming and pin control. This design avoids overloading the microcontroller with deep learning inference and "
        "keeps the embedded firmware simpler and more stable. The browser already has sufficient processing power on a laptop or "
        "desktop for COCO-SSD inference at useful frame rates for a prototype."
    )
    N(
        "Communication between browser and board uses ordinary HTTP requests. The UI calls /relay to set relay state and /led to "
        "control flash intensity/state. The stream is obtained from the camera server port. This REST-like style is easy to debug "
        "with ordinary browser developer tools and Serial Monitor logs."
    )
    N(
        "The design also supports future extension. For example, a custom model could replace COCO-SSD in the browser, or a TinyML "
        "model could later be explored on-device. The relay interface can drive different deterrent hardware as long as electrical "
        "safety is respected."
    )

    H("4.21 Hardware Setup Procedure")
    N(
        "The hardware setup used during training included an ESP32-CAM board, USB-TTL programmer (CH340 based), 5V power supply "
        "suitable for the board, jumper wires, and a relay module connected to GPIO12. The onboard flash LED on GPIO4 was used "
        "without external LED hardware. The camera was positioned with a clear view of the monitored area."
    )
    N(
        "During firmware upload, the correct COM port must be selected in Arduino IDE. In the development setup, COM8 "
        "(USB-SERIAL CH340) was the working port. After successful upload, the board connects to configured Wi-Fi and prints "
        "the assigned IP address on the Serial Monitor. The monitoring page is then opened in a browser using that IP."
    )
    N(
        "Relay wiring must follow the relay module documentation. The ESP32 GPIO provides the control signal, while the relay "
        "coil/load side uses an appropriate supply. For demonstration, the control signal correctness (HIGH/LOW behavior and hold "
        "timing) was verified as the primary training outcome."
    )

    H("4.22 Firmware Organization")
    N(
        "CameraWebServer.ino initializes Wi-Fi, camera configuration, relay pin mode, and flash LED setup. It starts the HTTP "
        "server so that stream and control endpoints become available. Care is taken to initialize flash through LEDC rather than "
        "a plain digitalWrite, because the ESP32-CAM flash LED expects PWM/LEDC style control."
    )
    N(
        "app_httpd.cpp contains handlers for the root page, stream, relay API, and LED API. The root page serves the custom dog "
        "detection UI from index_dog.h. This ensures that opening the board IP directly loads the project interface instead of a "
        "generic camera demo page."
    )
    N(
        "board_config.h stores board-specific constants such as RELAY_GPIO_NUM. Keeping pin definitions centralized reduces mistakes "
        "when hardware wiring changes. index_dog.h contains HTML/CSS/JavaScript for streaming display, model loading, detection loop, "
        "ROI drawing, and alert timing."
    )

    H("4.23 Browser Detection Pipeline in Detail")
    N(
        "When the page loads, scripts for TensorFlow.js and the COCO-SSD model are fetched. After the model is ready, a continuous "
        "asynchronous loop captures the current camera frame from the stream image element and runs model.detect(). Each returned "
        "prediction includes class name, score, and bounding box coordinates."
    )
    N(
        "The filtering stage keeps only predictions where class is dog and score is at least about 0.55. If a DETECT ZONE exists, "
        "the center of the dog box is tested against the zone rectangle. Only in-zone dogs are marked valid. Valid dogs are drawn "
        "with a green rectangle and a label showing class and percentage accuracy."
    )
    N(
        "If at least one valid dog exists, the alert state becomes active. The UI records the alert start time and requests relay ON. "
        "Flash may also be turned ON. While the 7-second hold has not expired, the relay remains ON even if a few frames temporarily "
        "miss the dog. After hold expiry, the code checks current valid detections again. Presence continues the hold; absence turns "
        "relay/flash OFF."
    )

    H("4.24 Why Object Detection Was Chosen")
    N(
        "Object detection was chosen instead of whole-image classification because the project needs location awareness. The operator "
        "must see where the dog is, and the ROI logic must know whether the dog center is inside a selected rectangle. Classification "
        "alone cannot support bounding boxes or zone gating."
    )
    N(
        "COCO-SSD was selected because it is widely available for TensorFlow.js, requires no local training for a first working "
        "prototype, and can detect the dog class directly. This allowed the training period to focus on system integration—hardware, "
        "streaming, UI, ROI, and actuation—rather than only dataset collection."
    )
    N(
        "Custom YOLO training was also studied as an optional advanced path during the learning phase. However, the final live "
        "system used browser COCO-SSD because it provided stable real-time demonstration for the internship evaluation scope."
    )

    H("4.25 GPIO Pin Mapping and Control Semantics")
    N(
        "GPIO12 is configured as relay control output. A HIGH signal is used to turn the relay ON for alert/deterrent action, and "
        "LOW turns it OFF. GPIO4 controls the onboard flash LED through LEDC. The web UI can request LED on/off (and intensity where "
        "supported by the firmware endpoint)."
    )
    N(
        "Control semantics are intentionally simple so that debugging remains easy. The browser is the decision maker for when an "
        "alert should start or stop, while the ESP32 is the actuator executor. This split matches the selected hybrid architecture."
    )
    N(
        "Debounce/hold behavior is implemented in software timing rather than only hardware debounce. The 7-second software hold "
        "prevents rapid relay toggling when detection confidence fluctuates around the threshold."
    )

    H("4.26 User Interface Design Summary")
    N(
        "The monitoring interface presents a live camera view, detection overlays, and control actions. The visual style uses a dark "
        "security-monitor look so that overlays remain readable. The camera preview is kept practical for continuous observation. "
        "Controls include starting/using detection, drawing/clearing the detect zone, and toggling flash LED."
    )
    N(
        "Bounding boxes are drawn only for accepted dog detections to avoid clutter from unrelated COCO classes. Showing accuracy "
        "percentage helps the operator understand how confident the model is for each detection. The DETECT ZONE rectangle is shown "
        "distinctly so the monitored area is always visible."
    )
    N(
        "Because the UI is a normal web page hosted by the ESP32, any device on the same network with a modern browser can open the "
        "monitor. This is useful for demonstration and for checking the scene from indoors while the camera remains outdoors/near parking."
    )

    H("4.27 Step-by-Step Implementation Chronology")
    N("The implementation progressed in the following order during training:")
    B("Step 1: Establish ESP32-CAM Wi-Fi connectivity and verify Serial Monitor IP output.")
    B("Step 2: Verify live MJPEG stream in browser.")
    B("Step 3: Serve custom monitoring page from the board.")
    B("Step 4: Integrate TensorFlow.js and load COCO-SSD.")
    B("Step 5: Draw all detections, then restrict to dog-only class.")
    B("Step 6: Add confidence threshold and green box labeling.")
    B("Step 7: Implement /relay API and connect GPIO12 hardware.")
    B("Step 8: Add 7-second hold and recheck logic.")
    B("Step 9: Implement flash LED endpoint and UI button.")
    B("Step 10: Implement user-drawn DETECT ZONE and clear-zone behavior.")
    B("Step 11: Perform end-to-end tests with dog in/out of zone and non-dog objects.")
    N(
        "This chronology shows that the project was built incrementally. Each step produced a testable milestone, which is an important "
        "engineering practice learned during industrial training."
    )

    H("4.28 Test Cases and Expected Results")
    N("Representative test cases used for validation are described below.")
    N(
        "Test Case 1 – Stream availability: Power on the board, connect to Wi-Fi, open IP in browser. Expected result: live video is visible."
    )
    N(
        "Test Case 2 – Dog detection: Present a dog (or clear dog image/video) in camera view. Expected result: green box and confidence label appear."
    )
    N(
        "Test Case 3 – Non-dog rejection: Present person/car without dog. Expected result: no relay alert from those classes."
    )
    N(
        "Test Case 4 – ROI accept: Draw zone and place dog center inside zone. Expected result: relay/flash activate according to hold logic."
    )
    N(
        "Test Case 5 – ROI reject: Keep dog outside zone. Expected result: no alert actuation."
    )
    N(
        "Test Case 6 – Hold timing: Trigger alert then briefly hide dog within 7 seconds. Expected result: relay remains ON until hold completes and recheck decides."
    )
    N(
        "Test Case 7 – Manual flash: Press Flash LED button. Expected result: onboard flash responds independently for illumination/testing."
    )

    H("4.29 Observations, Limitations and Mitigations")
    N(
        "Lighting strongly affects detection. Low light can reduce confidence below threshold. Using flash or better placement mitigates this. "
        "Very small/distant dogs may be missed; mounting distance should keep the subject large enough in the frame. Occlusion by pillars or "
        "other cars can hide the animal; camera angle should minimize occlusion of the critical roof/bonnet region."
    )
    N(
        "Because COCO-SSD is general-purpose, some false positives/negatives are possible in unusual scenes. The ROI feature and confidence "
        "threshold reduce practical false alerts. For production deployment, a custom dataset from the actual parking location would further "
        "improve robustness."
    )
    N(
        "Network conditions also matter. The viewing device needs access to model scripts (CDN) unless assets are fully embedded. Wi-Fi "
        "strength affects stream smoothness. These are normal IoT deployment considerations and were noted during testing."
    )

    H("4.30 Learning Outcomes Mapped to AI/ML Syllabus")
    N(
        "From a Machine Learning perspective, the project reinforced the difference between training-time learning and inference-time use of "
        "a model. The team used a pre-trained detector and concentrated on inference integration. Confidence scores were treated as decision "
        "evidence with a threshold, which is a standard applied-ML practice."
    )
    N(
        "From a Deep Learning perspective, the project demonstrated that convolutional detectors can localize objects. From an IoT perspective, "
        "it demonstrated sensor-to-actuator closed-loop behavior. From a software perspective, it demonstrated full-stack thinking across "
        "firmware, networking, and front-end logic."
    )
    N(
        "These outcomes align with industrial training goals: not only studying algorithms on paper, but completing a working system that can "
        "be demonstrated to mentors and evaluators."
    )

    H("4.31 Comparison with Alternative Approaches")
    N(
        "Alternative 1 – PIR motion sensor only: cheaper but cannot distinguish dog from human/vehicle motion. Vision was preferred for class awareness."
    )
    N(
        "Alternative 2 – PC Python OpenCV/YOLO only: powerful, but requires a continuously running computer near the camera. The ESP32 + browser "
        "approach is more portable for a low-cost node."
    )
    N(
        "Alternative 3 – On-device TinyML detection: attractive for standalone operation, but more complex to train/deploy within the training window. "
        "It remains a strong future enhancement."
    )
    N(
        "The chosen hybrid approach balanced complexity, cost, and demonstrability for the internship duration while still using genuine ML-based "
        "object detection rather than naive motion heuristics."
    )

    H("4.32 Ethical and Safety Notes")
    N(
        "Any deterrent connected to the relay must remain legally and ethically appropriate. The training prototype focuses on detection and "
        "signaling. Camera placement should respect privacy of neighbors and public spaces. Power supplies and relay loads must be handled with "
        "basic electrical safety precautions."
    )
    N(
        "These considerations are part of responsible engineering practice and were kept in mind while designing the alert pathway."
    )

    H("4.33 Future Scope in Detail")
    N(
        "Future work can include custom dataset collection of local street dogs and vehicles, training a compact detector, night-vision capable "
        "camera options, mobile push notifications, multi-camera support, and optional on-device inference. Logging of detection events with "
        "timestamps can help analyze peak nuisance hours. A weatherproof enclosure would support longer outdoor deployment."
    )
    N(
        "Even without these extensions, the present system already provides a complete base platform on which such improvements can be added "
        "module by module."
    )

    H("4.34 Chapter Expansion Summary")
    N(
        "This extended discussion documented problem analysis, requirements, design rationale, hardware/firmware/UI details, detection pipeline, "
        "GPIO semantics, test cases, limitations, syllabus mapping, alternatives, safety notes, and future scope. Together with the earlier "
        "implementation sections and figures, it presents a full academic account of the ESP32-CAM dog detection project completed during training."
    )

    # Chapter 5 expansion
    H("5.6 Skills Developed During Internship")
    N(
        "Technical skills developed include embedded C/C++ for ESP32, basic electronics integration with relay modules, web technologies "
        "(HTML/CSS/JavaScript), applied use of TensorFlow.js, and practical understanding of object detection outputs. Soft skills include "
        "iterative debugging, documenting progress, and converting a real nuisance problem into an engineering specification."
    )
    N(
        "The internship also improved confidence in reading datasheets/pinouts, using Serial logs, isolating software versus hardware faults, "
        "and validating features with explicit test cases rather than assumption."
    )

    H("5.7 Contribution Summary")
    N(
        "The contribution of this training project is a working end-to-end prototype that detects dogs in a live ESP32-CAM stream, optionally "
        "limits detection to a user-selected frame region, and drives relay/flash outputs with timed hold behavior. The system is suitable for "
        "demonstration, further research, and as a foundation for a field-deployable deterrent product."
    )

    H("5.8 Final Remarks")
    N(
        "Industrial training at Evontra Solutions LLP provided exposure to AI/ML fundamentals and a chance to apply them on real hardware. "
        "Completing the ESP32-CAM based dog detection and alert system fulfilled the practical objective of the training. The experience will "
        "support future academic projects and industry problem-solving in IoT and computer vision domains."
    )

    return blocks


def main():
    doc = Document(str(SRC))

    # Fix abstract paragraphs that still look incomplete
    abs_i = find_startswith(doc, "ABSTRACT")
    if abs_i is None:
        abs_i = find_contains(doc, "ABSTRACT")
    if abs_i is not None:
        new_abs = [
            "This report presents the work carried out during the Industrial Training / Internship undertaken at Evontra Solutions LLP under the guidance of the company supervisor. The training focused on Artificial Intelligence and Machine Learning concepts and their practical application in a real-time embedded vision problem.",
            "During the training, foundational Machine Learning topics such as supervised learning, regression, classification, association rule mining, and Deep Learning basics were studied and practiced. Building on this foundation, a complete real-time dog detection and alert system was designed and implemented using an ESP32-CAM module.",
            "The final system streams live video from the ESP32-CAM to a web browser. Object detection is performed using TensorFlow.js with the COCO-SSD model. Only the dog class is accepted. An optional user-selected detection zone (ROI) restricts detection to a chosen camera area. On detection, the system turns ON a relay (GPIO12) and camera flash LED for a 7-second hold period, then rechecks and continues or turns OFF accordingly.",
            "Overall, the training strengthened theoretical understanding of Machine Learning and provided hands-on experience in IoT hardware integration, computer vision based object detection, web-based monitoring UI, and actuator control for a practical use case of deterring stray dogs near parked vehicles.",
        ]
        # replace next non-empty paras until List of Figures / heading
        targets = []
        i = abs_i + 1
        while i < len(doc.paragraphs):
            t = (doc.paragraphs[i].text or "").strip()
            st = doc.paragraphs[i].style.name if doc.paragraphs[i].style else ""
            if t.startswith("List of Figures") or (st.startswith("Heading") and "List of" in t):
                break
            if t:
                targets.append(i)
            i += 1
        last = doc.paragraphs[abs_i]
        for j, text in enumerate(new_abs):
            if j < len(targets):
                replace_paragraph_text(doc.paragraphs[targets[j]], text)
                last = doc.paragraphs[targets[j]]
            else:
                last = add_body_after(last, text)
        for j in range(len(new_abs), len(targets)):
            # clear leftovers that may say "in progress"
            replace_paragraph_text(doc.paragraphs[targets[j]], "")

    # Avoid duplicate expansion
    if find_contains(doc, "4.18 Detailed Problem Analysis") is not None:
        print("Expansion already present; only abstract/page fixes may apply.")
    else:
        # Insert before CHAPTER 5 if possible, else before 4.17 / References
        anchor_i = find_startswith(doc, "4.17 Summary of Chapter 4")
        if anchor_i is None:
            anchor_i = find_startswith(doc, "CHAPTER 5:")
            if anchor_i is None:
                raise SystemExit("Could not find insertion point")
            # insert before chapter 5: use previous non-empty
            j = anchor_i - 1
            while j > 0 and not (doc.paragraphs[j].text or "").strip():
                j -= 1
            cur = doc.paragraphs[j]
        else:
            cur = doc.paragraphs[anchor_i]

        # If we found 4.17, insert AFTER it (before ch5)
        if find_startswith(doc, "4.17 Summary of Chapter 4") is not None:
            # move to end of 4.17 body: next paras until CHAPTER 5
            i = anchor_i + 1
            last = cur
            while i < len(doc.paragraphs):
                t = (doc.paragraphs[i].text or "").strip()
                if t.startswith("CHAPTER 5:"):
                    break
                if t:
                    last = doc.paragraphs[i]
                i += 1
            cur = last

        blocks = long_paras()
        # Split: 4.x before ch5, 5.x after chapter 5 future/conclusion area
        ch5_blocks = [b for b in blocks if b[1].startswith("5.")]
        ch4_blocks = [b for b in blocks if not b[1].startswith("5.")]

        for kind, text in ch4_blocks:
            if kind == "H":
                cur = add_heading_after(cur, text, "Heading 2")
            elif kind == "B":
                cur = add_body_after(cur, "• " + text)
            else:
                cur = add_body_after(cur, text)

        # chapter 5 extras after Final Remarks insertion point near conclusion
        c5 = find_startswith(doc, "5.5 Conclusion")
        if c5 is None:
            c5 = find_startswith(doc, "CHAPTER 5:")
        if c5 is not None:
            # find last paragraph before REFERENCES
            ref = find_startswith(doc, "REFERENCES")
            if ref is None:
                ref = find_startswith(doc, "References")
            if ref is not None:
                j = ref - 1
                while j > 0 and not (doc.paragraphs[j].text or "").strip():
                    j -= 1
                cur = doc.paragraphs[j]
            else:
                cur = doc.paragraphs[c5]
            for kind, text in ch5_blocks:
                if kind == "H":
                    # only headings starting with 5.
                    if text.startswith("5."):
                        cur = add_heading_after(cur, text, "Heading 2")
                    else:
                        cur = add_heading_after(cur, text, "Heading 2")
                elif kind == "B":
                    cur = add_body_after(cur, "• " + text)
                else:
                    cur = add_body_after(cur, text)

    # Add tools/pin tables as plain formatted text blocks if missing (preserve style)
    if find_contains(doc, "Table 4.1 Tools and Technologies") is None:
        tools_i = find_startswith(doc, "4.4 Tools and Technologies Used")
        if tools_i is not None:
            cur = doc.paragraphs[tools_i]
            # skip to after first bodies
            i = tools_i + 1
            while i < len(doc.paragraphs):
                t = (doc.paragraphs[i].text or "").strip()
                st = doc.paragraphs[i].style.name if doc.paragraphs[i].style else ""
                if st.startswith("Heading") and t.startswith("4.5"):
                    break
                if t:
                    cur = doc.paragraphs[i]
                i += 1
            cur = add_body_after(cur, "Table 4.1 Tools and Technologies Used")
            if cur.runs:
                set_run_font(cur.runs[0], BODY_PT, bold=True)
            rows = [
                "1. ESP32-CAM (AI-Thinker) – Camera capture, Wi-Fi, GPIO control",
                "2. Arduino IDE + ESP32 core – Firmware development (C/C++)",
                "3. HTML/CSS/JavaScript – Monitoring web interface",
                "4. TensorFlow.js – Browser-side ML runtime",
                "5. COCO-SSD – Pre-trained object detection model",
                "6. Relay module – Alert/deterrent actuation on GPIO12",
                "7. Onboard Flash LED – Illumination/alert on GPIO4",
            ]
            for r in rows:
                cur = add_body_after(cur, r)

    if find_contains(doc, "Table 4.2 GPIO Pin Mapping") is None:
        gpio_i = find_startswith(doc, "4.10 Flash LED and Relay Control")
        if gpio_i is not None:
            cur = doc.paragraphs[gpio_i]
            i = gpio_i + 1
            while i < len(doc.paragraphs):
                t = (doc.paragraphs[i].text or "").strip()
                st = doc.paragraphs[i].style.name if doc.paragraphs[i].style else ""
                if st.startswith("Heading") and t.startswith("4.11"):
                    break
                if t:
                    cur = doc.paragraphs[i]
                i += 1
            cur = add_body_after(cur, "Table 4.2 GPIO Pin Mapping (Relay / Flash)")
            if cur.runs:
                set_run_font(cur.runs[0], BODY_PT, bold=True)
            cur = add_body_after(cur, "GPIO12 – Relay control output (HIGH = ON, LOW = OFF)")
            cur = add_body_after(cur, "GPIO4 – Onboard flash LED via LEDC/PWM control")
            cur = add_body_after(cur, "Wi-Fi – HTTP UI on port 80, MJPEG stream on port 81")

    # Re-ensure figures exist / captions present; if missing images, re-add before 4.14
    if find_contains(doc, "Fig. 4.1") is None:
        fig_h = find_startswith(doc, "4.13 Figures Related to the Project")
        if fig_h is not None:
            cur = doc.paragraphs[fig_h]
            figs = [
                (FIG_DIR / "fig_esp32_cam.png", "Fig. 4.1 ESP32-CAM hardware concept used in the project"),
                (FIG_DIR / "fig_architecture.png", "Fig. 4.2 System architecture of the dog detection and alert system"),
                (FIG_DIR / "fig_workflow.png", "Fig. 4.3 Detection and relay-hold workflow"),
                (FIG_DIR / "fig_ui_zone.png", "Fig. 4.4 Monitoring UI concept with DETECT ZONE and dog bounding box"),
            ]
            for path, cap in figs:
                if path.exists():
                    cur = add_picture_with_caption(cur, path, cap)

    # Update LoF / LoT page numbers roughly for ~30 page doc
    if len(doc.tables) >= 1:
        t0 = doc.tables[0]
        while len(t0.rows) < 5:
            t0.add_row()
        data = [
            ("Fig. 4.1", "ESP32-CAM hardware concept", "18"),
            ("Fig. 4.2", "System architecture of dog detection alert system", "19"),
            ("Fig. 4.3", "Detection and relay-hold workflow", "20"),
            ("Fig. 4.4", "Monitoring UI with DETECT ZONE and dog box", "21"),
        ]
        for i, (a, b, c) in enumerate(data, start=1):
            t0.rows[i].cells[0].text = a
            t0.rows[i].cells[1].text = b
            t0.rows[i].cells[2].text = c
    if len(doc.tables) >= 2:
        t1 = doc.tables[1]
        while len(t1.rows) < 3:
            t1.add_row()
        t1.rows[1].cells[0].text = "Table 4.1"
        t1.rows[1].cells[1].text = "Tools and technologies used in the project"
        t1.rows[1].cells[2].text = "17"
        if len(t1.rows) > 2:
            t1.rows[2].cells[0].text = "Table 4.2"
            t1.rows[2].cells[1].text = "GPIO pin mapping (Relay/Flash)"
            t1.rows[2].cells[2].text = "22"

    # Update chapter TOC page numbers for expanded report
    toc_updates = {
        "Chapter 1: Introduction": "Chapter 1: Introduction ............................................................................................................. 1",
        "Chapter 2: Company Infrastructure": "Chapter 2: Company Infrastructure ............................................................................................. 4",
        "Chapter 3: Training Attended": "Chapter 3: Training Attended ...................................................................................................... 7",
        "Chapter 4: Systems / Project Development": "Chapter 4: Systems / Project Development ................................................................................. 12",
        "Chapter 5: Results and Conclusion": "Chapter 5: Results and Conclusion ............................................................................................. 27",
        "References": "References ................................................................................................................................. 30",
    }
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        for key, val in toc_updates.items():
            if t.startswith(key):
                replace_paragraph_text(p, val)
                break

    doc.save(str(SRC))

    # stats
    words = sum(len((p.text or "").split()) for p in doc.paragraphs)
    imgs = 0
    for p in doc.paragraphs:
        if p._p.xpath('.//*[local-name()="drawing" or local-name()="pict"]'):
            imgs += 1
    print("Saved", SRC)
    print("words", words)
    print("approx_pages", round(words / 300, 1))
    print("images", imgs)
    print("has_4.18", find_contains(doc, "4.18 Detailed Problem Analysis") is not None)
    print("abstract_ok", any("successfully developed" in (p.text or "") or "complete real-time dog detection" in (p.text or "") for p in doc.paragraphs))


if __name__ == "__main__":
    main()
