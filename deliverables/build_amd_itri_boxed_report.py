#!/usr/bin/env python3
"""Build the AMD–ITRI boxed (पेटी) Project Review deck from the two source PDFs.

Template visual language: AMD–ITRI PROJECT REVIEW (LibreOffice Impress),
widescreen 16:9, navy field, cyan rules, rounded content boxes.

Source substance: AMD–ITRI Project Review slides + Final Comparison Report.
No invented metrics. Diagrams that existed only as images are embedded.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT_PDF = ROOT / "AMD-ITRI-MDA-TARI_MI300X-RAG_Boxed-Project-Review.pdf"

W, H = 960.0, 540.0
BG = HexColor("#0B1E3A")
BOX = HexColor("#122B4F")
CYAN = HexColor("#1EC8ED")
CYAN_DK = HexColor("#00A8D0")
MUTED = HexColor("#9BB4C9")
LINE = HexColor("#1A3A5C")
FOOT = HexColor("#7A93A8")
WARN = HexColor("#0E2744")

FOOTER = "MI300X Enterprise Document RAG Project Report  |  Dr. Ammar Amjad, NYCU"


def _register_fonts() -> tuple[str, str]:
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont("Body", regular))
            pdfmetrics.registerFont(TTFont("Body-Bold", bold))
            return "Body", "Body-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONTB = _register_fonts()


def rrect(c: canvas.Canvas, x, y, w, h, radius=12, fill=BOX, stroke=CYAN, sw=1.2):
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(sw)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)
    c.restoreState()


def wrap(c: canvas.Canvas, text: str, font: str, size: float, max_w: float) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else f"{cur} {w}"
        if c.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def draw_wrapped(c, text, x, y, font, size, max_w, leading=None, color=white, align="left"):
    leading = leading or size + 4
    c.setFillColor(color)
    c.setFont(font, size)
    lines = wrap(c, text, font, size, max_w)
    for i, line in enumerate(lines):
        xx = x
        if align == "center":
            xx = x + (max_w - c.stringWidth(line, font, size)) / 2
        c.drawString(xx, y - i * leading, line)
    return len(lines) * leading


def bullets(c, items, x, y, font, size, max_w, leading=None, color=white, bullet_color=CYAN):
    leading = leading or size + 6
    yy = y
    for item in items:
        c.setFillColor(bullet_color)
        c.circle(x + 4, yy + 3, 2.4, fill=1, stroke=0)
        h = draw_wrapped(c, item, x + 14, yy, font, size, max_w - 14, leading, color)
        yy -= max(h, leading)
    return yy


def header_bar(c, title: str, page_no: int, total: int):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(36, H - 52, 6, 28, fill=1, stroke=0)
    draw_wrapped(c, title, 52, H - 42, FONTB, 20, 860, 24, white)
    c.setFillColor(LINE)
    c.rect(36, 36, W - 72, 0.8, fill=1, stroke=0)
    c.setFillColor(FOOT)
    c.setFont(FONT, 9)
    c.drawString(36, 22, FOOTER)
    c.drawRightString(W - 36, 22, str(page_no))


def arrow(c, x1, y1, x2, y2):
    c.setStrokeColor(CYAN)
    c.setFillColor(CYAN)
    c.setLineWidth(2)
    c.line(x1, y1, x2 - 8, y2)
    path = c.beginPath()
    path.moveTo(x2, y2)
    path.lineTo(x2 - 10, y2 + 4.5)
    path.lineTo(x2 - 10, y2 - 4.5)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def finish(c):
    c.showPage()


def slide_control(c, total):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, H - 8, W, 8, fill=1, stroke=0)
    c.setFont(FONT, 11)
    c.setFillColor(CYAN)
    c.drawString(48, H - 56, "AMD – ITRI PROJECT REVIEW  ·  DOCUMENT CONTROL")
    draw_wrapped(c, "MI300X Enterprise Document RAG — boxed template conversion", 48, H - 88, FONTB, 22, 860, 26, white)

    rrect(c, 48, 70, 864, 330, 14)
    rows = [
        ("Document title", "AMD-ITRI Project Review: MI300X Enterprise Document RAG (boxed / peti format)"),
        ("Template followed", "AMD–ITRI PROJECT REVIEW boxed slide template (widescreen navy + cyan boxes)"),
        ("Version", "1.0  ·  Finalized 2026-09-11"),
        ("Classification", "Project review  ·  Technical report  ·  Not an SEC MD&A filing"),
        ("Author (source)", "Dr. Ammar Amjad  ·  National Yang Ming Chiao Tung University (NYCU)"),
        ("Platform", "AMD Instinct MI300X  ·  PyTorch 2.3  ·  ROCm 6.2"),
        ("Prepared from", "AMD-ITRI-Project-Review-TEMPLATE.pdf  +  AMD-ITRI-MI300X-Final-Comparison-Report-SOURCE.pdf"),
        ("Conversion", "All transferable text, metrics, and section boxes mapped onto the template. Source diagrams embedded."),
        ("Attestation", "Prepared/generated as a document-control conversion. Not a handwritten, cryptographic, or legal personal signature."),
        ("Page count", f"{total} pages including this control sheet"),
    ]
    y = 370
    for k, v in rows:
        c.setFont(FONTB, 9)
        c.setFillColor(CYAN)
        c.drawString(68, y, k.upper())
        draw_wrapped(c, v, 220, y, FONT, 10, 660, 13, white)
        y -= 30

    c.setFillColor(FOOT)
    c.setFont(FONT, 9)
    c.drawString(48, 28, "Generated 2026-09-11  ·  Attestation block only  ·  No official signature forged")
    finish(c)


def slide_cover(c):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # left panel network motif
    c.setFillColor(HexColor("#081628"))
    c.rect(0, 0, 300, H, fill=1, stroke=0)
    nodes = [(70, 430), (160, 390), (90, 300), (200, 250), (60, 180), (170, 120), (80, 70)]
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.4)
    for a, b in zip(nodes, nodes[1:]):
        c.line(*a, *b)
    c.line(nodes[0][0], nodes[0][1], nodes[2][0], nodes[2][1])
    c.line(nodes[1][0], nodes[1][1], nodes[3][0], nodes[3][1])
    for i, (x, y) in enumerate(nodes):
        c.setFillColor(white if i % 2 == 0 else CYAN)
        c.circle(x, y, 6, fill=1, stroke=0)

    c.setFillColor(CYAN)
    c.setFont(FONT, 11)
    c.drawString(348, 430, "AMD – ITRI PROJECT REVIEW")
    c.setFillColor(white)
    c.setFont(FONTB, 32)
    c.drawString(348, 370, "MI300X Enterprise Document")
    c.drawString(348, 332, "RAG Project Report")
    c.setStrokeColor(CYAN)
    c.setLineWidth(2.2)
    c.line(348, 300, 520, 300)
    draw_wrapped(
        c,
        "Enterprise document retrieval and source-grounded Chinese answer generation",
        348,
        270,
        FONT,
        13,
        560,
        18,
        MUTED,
    )
    c.setFillColor(white)
    c.setFont(FONTB, 16)
    c.drawString(348, 200, "Dr. Ammar Amjad")
    c.setFont(FONT, 12)
    c.setFillColor(MUTED)
    c.drawString(348, 178, "National Yang Ming Chiao Tung University")
    c.setFillColor(CYAN)
    c.setFont(FONT, 10)
    c.drawString(348, 130, "AMD Instinct MI300X  •  PyTorch 2.3 / ROCm 6.2  •  Implemented RAG prototype")
    c.setFillColor(FOOT)
    c.setFont(FONT, 9)
    c.drawString(348, 70, "Also titled in the comparison source: AMD–ITRI High-Performance Computing Platform")
    c.drawString(348, 54, "Boxed conversion of the Final Comparison Report onto this Project Review template")
    finish(c)


def slide_problem(c, n, total):
    header_bar(c, "RAG turns scattered PDF and Excel content into grounded answers", n, total)
    rrect(c, 36, 300, 430, 160)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(56, 432, "BUSINESS PROBLEM")
    draw_wrapped(
        c,
        "Enterprise knowledge is spread across PDF reports and Excel sheets. Finding the right information manually is slow, and answers often lack a traceable source.",
        56,
        400,
        FONT,
        11,
        390,
        16,
        white,
    )
    rrect(c, 494, 300, 430, 160)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(514, 432, "IMPLEMENTED SOLUTION")
    draw_wrapped(
        c,
        "Retrieval-Augmented Generation (RAG): the system first retrieves the most relevant document chunks, then Qwen2.5-7B-Instruct generates a Traditional Chinese answer grounded in them.",
        514,
        400,
        FONT,
        11,
        390,
        16,
        white,
    )

    boxes = [
        (36, "1  Data Preparation", "PDF + Excel → text extraction → 500-char chunks → BGE embeddings → vector index"),
        (344, "2  Retrieval", "User question → query embedding → dot-product similarity → Top-3 chunks"),
        (652, "3  Generation", "Retrieved context + sources → Qwen2.5-7B-Instruct → Traditional Chinese answer with filenames"),
    ]
    for x, title, body in boxes:
        rrect(c, x, 80, 272, 190)
        c.setFillColor(CYAN)
        c.setFont(FONTB, 13)
        c.drawString(x + 18, 236, title)
        draw_wrapped(c, body, x + 18, 200, FONT, 11, 236, 16, white)
    arrow(c, 308, 175, 344, 175)
    arrow(c, 616, 175, 652, 175)
    finish(c)


def slide_objective(c, n, total):
    header_bar(c, "Objective: a searchable knowledge base that answers with sources", n, total)
    rrect(c, 36, 80, 420, 380)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 12)
    c.drawString(56, 428, "PROBLEM ADDRESSED")
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    c.line(56, 418, 200, 418)
    bullets(
        c,
        [
            "Information distributed across PDF and Excel files",
            "Manual search is time-consuming",
            "Answers may lack document sources",
            "Answers need traceable document sources (comparison source wording)",
        ],
        56,
        380,
        FONT,
        12,
        380,
        28,
    )
    rrect(c, 504, 80, 420, 380, stroke=CYAN)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 12)
    c.drawString(524, 428, "IMPLEMENTED OBJECTIVE")
    c.setStrokeColor(CYAN)
    c.line(524, 418, 700, 418)
    bullets(
        c,
        [
            "Build a searchable document knowledge base / Chinese document knowledge index",
            "Retrieve relevant chunks for a question",
            "Generate source-grounded Traditional Chinese answers with Qwen",
        ],
        524,
        380,
        FONT,
        12,
        380,
        32,
    )
    arrow(c, 456, 270, 504, 270)
    finish(c)


def slide_index(c, n, total):
    header_bar(c, "Documents become a persistent vector index in five steps", n, total)
    steps = [
        ("PDF + Excel", "Enterprise source documents"),
        ("Text extraction", "pypdf (PDF)  ·  openpyxl (Excel rows / sheets)"),
        ("Chunking", "500-character chunks  ·  100-character overlap  ·  clean text"),
        ("BGE embeddings", "BAAI/bge-small-zh-v1.5  ·  normalized on MI300X"),
        ("Vector index", "gama_embeddings.npy  ·  gama_chunks.json  ·  index_summary.json"),
    ]
    bw = 160
    gap = 18
    x0 = 36
    for i, (t, b) in enumerate(steps):
        x = x0 + i * (bw + gap)
        rrect(c, x, 330, bw, 120)
        c.setFillColor(CYAN)
        c.setFont(FONTB, 10)
        c.drawString(x + 10, 424, t)
        draw_wrapped(c, b, x + 10, 400, FONT, 9, 140, 13, white)
        if i < 4:
            arrow(c, x + bw, 390, x + bw + gap, 390)

    # bar chart box
    rrect(c, 36, 70, 500, 230)
    c.setFillColor(white)
    c.setFont(FONTB, 11)
    c.drawCentredString(286, 274, "Verified index results")
    # axes
    c.setStrokeColor(white)
    c.setLineWidth(1)
    c.line(90, 100, 500, 100)
    max_v = 30
    for val, label, x in [(25, "Document sections extracted", 180), (17, "Searchable chunks created", 360)]:
        bh = (val / max_v) * 140
        c.setFillColor(CYAN)
        c.rect(x - 28, 100, 56, bh, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FONTB, 12)
        c.drawCentredString(x, 100 + bh + 8, str(val))
        c.setFont(FONT, 8)
        c.setFillColor(MUTED)
        c.drawCentredString(x, 82, label)

    rrect(c, 554, 70, 370, 230)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 12)
    c.drawString(574, 270, "INDEX FACTS")
    bullets(
        c,
        [
            "25 document sections extracted",
            "17 searchable text chunks created",
            "Embeddings normalized for dot-product similarity",
            "Index persisted to disk for reuse across queries",
            "Saved files: gama_embeddings.npy, gama_chunks.json, index_summary.json",
        ],
        574,
        240,
        FONT,
        10,
        330,
        26,
    )
    finish(c)


def slide_architecture(c, n, total):
    header_bar(c, "The architecture links document evidence to the generated answer", n, total)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 10)
    c.drawString(36, 456, "OFFLINE  ·  INDEX CONSTRUCTION")
    off = [
        (36, "Enterprise documents", "PDF · Excel"),
        (250, "Text extraction & chunking", "pypdf · openpyxl · 500/100"),
        (464, "BGE embeddings", "bge-small-zh-v1.5 · MI300X"),
        (678, "Vector index", ".npy + .json"),
    ]
    for i, (x, t, b) in enumerate(off):
        rrect(c, x, 360, 196, 80)
        c.setFillColor(white)
        c.setFont(FONTB, 10)
        c.drawString(x + 10, 412, t)
        c.setFillColor(MUTED)
        c.setFont(FONT, 9)
        c.drawString(x + 10, 392, b)
        if i < 3:
            arrow(c, x + 196, 400, x + 214, 400)

    c.setFillColor(CYAN)
    c.setFont(FONTB, 10)
    c.drawString(36, 330, "ONLINE  ·  QUESTION ANSWERING")
    on = [
        (36, "User question", "Traditional Chinese query"),
        (250, "Top-3 retrieval", "normalized · dot-product"),
        (464, "Qwen2.5-7B-Instruct", "bfloat16 · device_map=auto"),
        (678, "Grounded answer", "Traditional Chinese + filenames"),
    ]
    for i, (x, t, b) in enumerate(on):
        rrect(c, x, 234, 196, 80)
        c.setFillColor(white)
        c.setFont(FONTB, 10)
        c.drawString(x + 10, 286, t)
        c.setFillColor(MUTED)
        c.setFont(FONT, 9)
        c.drawString(x + 10, 266, b)
        if i < 3:
            arrow(c, x + 196, 274, x + 214, 274)

    c.setStrokeColor(CYAN)
    c.setDash(3, 3)
    c.line(776, 360, 776, 314)
    c.setDash()
    c.setFillColor(MUTED)
    c.setFont(FONT, 8)
    c.drawCentredString(776, 318, "evidence chunks")

    rrect(c, 36, 70, 888, 140)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 10)
    c.drawString(56, 186, "COMPARISON-SOURCE IMPLEMENTATION FACTS (from the architecture diagram)")
    bullets(
        c,
        [
            "Embedding path uses BAAI/bge-small-zh-v1.5 via Sentence Transformers; batch size 32; normalized vector embeddings.",
            "Index stores source + page + sheet + row metadata with gama_embeddings.npy and gama_chunks.json.",
            "Similarity: score(q, d) = qᵀd on normalized vectors (cosine). Retrieval returns Top-3 relevant chunks.",
            "Generation: Qwen2.5-7B-Instruct, bfloat16, device_map=auto, max_new_tokens = 300, on AMD Instinct MI300X / PyTorch / ROCm.",
            "Observed LLM generation time recorded on the diagram: 2.55 seconds (single-query observation).",
        ],
        56,
        164,
        FONT,
        9,
        850,
        18,
    )
    finish(c)


def slide_flow_image(c, n, total):
    header_bar(c, "Implemented flow (source diagram placed in the template box)", n, total)
    rrect(c, 36, 56, 888, 400, 12, HexColor("#081628"), CYAN)
    img = ASSETS / "implemented-flow-source.png"
    # fit image inside box
    iw, ih = 888 - 24, 400 - 24
    c.drawImage(str(img), 48, 68, width=iw, height=ih, preserveAspectRatio=True, anchor="c", mask="auto")
    finish(c)


def slide_models(c, n, total):
    header_bar(c, "Two models, two roles: retrieval and generation", n, total)
    rrect(c, 36, 150, 430, 300)
    c.saveState()
    p = c.beginPath()
    p.roundRect(36, 150, 430, 300, 12)
    c.clipPath(p, stroke=0)
    c.setFillColor(CYAN)
    c.rect(36, 404, 430, 46, fill=1, stroke=0)
    c.restoreState()
    c.setFillColor(BG)
    c.setFont(FONTB, 13)
    c.drawCentredString(251, 420, "BAAI/bge-small-zh-v1.5")
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(56, 370, "Role: Embedding and retrieval")
    bullets(
        c,
        [
            "Converts document chunks and user queries into semantic / comparable vectors",
            "Supports normalized vector search and Top-3 retrieval by dot-product similarity",
            "Chinese semantic embeddings (comparison source)",
        ],
        56,
        330,
        FONT,
        11,
        390,
        28,
    )

    rrect(c, 494, 150, 430, 300)
    c.saveState()
    p = c.beginPath()
    p.roundRect(494, 150, 430, 300, 12)
    c.clipPath(p, stroke=0)
    c.setFillColor(CYAN)
    c.rect(494, 404, 430, 46, fill=1, stroke=0)
    c.restoreState()
    c.setFillColor(BG)
    c.setFont(FONTB, 13)
    c.drawCentredString(709, 420, "Qwen2.5-7B-Instruct")
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(514, 370, "Role: Answer generation")
    bullets(
        c,
        [
            "Uses retrieved context and system instructions",
            "Generates source-grounded Traditional Chinese answers",
            "Produces source filenames with the answer",
            "bfloat16 inference on MI300X",
        ],
        514,
        330,
        FONT,
        11,
        390,
        26,
    )
    c.setFillColor(CYAN)
    c.setFont(FONTB, 22)
    c.drawCentredString(480, 290, "+")

    rrect(c, 36, 70, 888, 60)
    c.setFillColor(white)
    c.setFont(FONT, 12)
    c.drawCentredString(480, 94, "No model training or fine-tuning is claimed in this project.")
    finish(c)


def slide_results(c, n, total):
    header_bar(c, "Verified results on AMD Instinct MI300X", n, total)
    kpis = [
        ("25", "document sections extracted"),
        ("17", "searchable chunks created"),
        ("2.55 s", "observed Qwen response-generation time"),
        ("Top-3", "retrieved chunks per query"),
    ]
    for i, (v, lab) in enumerate(kpis):
        x = 36 + i * 228
        rrect(c, x, 360, 216, 96)
        c.setFillColor(CYAN)
        c.setFont(FONTB, 22)
        c.drawCentredString(x + 108, 416, v)
        draw_wrapped(c, lab, x + 12, 388, FONT, 9, 192, 12, MUTED, "center")

    rrect(c, 36, 70, 430, 270)
    c.setFillColor(white)
    c.setFont(FONTB, 11)
    c.drawCentredString(251, 314, "Response time comparison (seconds)")
    c.setFont(FONT, 8)
    c.setFillColor(MUTED)
    c.drawCentredString(251, 298, "From the Final Comparison Report chart — not a general GPU benchmark")
    # bars
    data = [("Qwen2.5-7B", 2.55, CYAN), ("Llama 3.1 8B Instruct", 3.1, HexColor("#7AA4C4")), ("Mistral 7B Instruct", 2.9, HexColor("#5B87A8"))]
    base_y = 110
    max_v = 4.0
    for i, (name, val, col) in enumerate(data):
        x = 90 + i * 120
        bh = (val / max_v) * 160
        c.setFillColor(col)
        c.rect(x, base_y, 70, bh, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FONTB, 10)
        c.drawCentredString(x + 35, base_y + bh + 8, str(val))
        c.setFont(FONT, 7)
        c.setFillColor(MUTED)
        draw_wrapped(c, name, x - 10, base_y - 16, FONT, 7, 90, 9, MUTED, "center")
    c.setStrokeColor(white)
    c.line(70, base_y, 420, base_y)

    rrect(c, 484, 70, 440, 270)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 12)
    c.drawString(504, 310, "OBSERVATIONS")
    bullets(
        c,
        [
            "Qwen2.5-7B-Instruct loaded and executed successfully on MI300X (bfloat16, device_map=auto).",
            "The answer used the retrieved documents and stated “insufficient information” instead of inventing a third source.",
            "Execution environment: AMD Instinct MI300X • PyTorch 2.3 • ROCm 6.2.",
            "Note: 2.55 seconds is an observed single-query generation time, not a general GPU benchmark.",
        ],
        504,
        280,
        FONT,
        10,
        400,
        28,
    )
    finish(c)


def slide_deploy(c, n, total):
    header_bar(c, "Proposed deployment model for enterprise RAG", n, total)
    c.setFillColor(CYAN)
    c.roundRect(36, 448, 280, 22, 8, fill=1, stroke=0)
    c.setFillColor(BG)
    c.setFont(FONTB, 8)
    c.drawCentredString(176, 455, "PROPOSED  ·  NOT YET IMPLEMENTED")

    steps = [
        ("1", "Controlled upload", "Authorized users upload PDF / Excel documents"),
        ("2", "Versioning & indexing", "Track document versions; re-embed and update the index"),
        ("3", "Source-grounded Q&A", "Retrieve evidence, then generate the answer with Qwen"),
        ("4", "Citations & feedback", "Show source filenames; collect user ratings to improve quality"),
    ]
    for i, (num, t, b) in enumerate(steps):
        x = 36 + i * 228
        rrect(c, x, 250, 216, 180)
        c.setFillColor(CYAN)
        c.circle(x + 108, 400, 14, fill=1, stroke=0)
        c.setFillColor(BG)
        c.setFont(FONTB, 11)
        c.drawCentredString(x + 108, 396, num)
        c.setFillColor(white)
        c.setFont(FONTB, 11)
        c.drawCentredString(x + 108, 360, t)
        draw_wrapped(c, b, x + 14, 332, FONT, 9, 188, 13, MUTED, "center")
        if i < 3:
            arrow(c, x + 216, 340, x + 228, 340)

    rrect(c, 36, 70, 888, 160)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 10)
    c.drawString(56, 208, "FUTURE-STATE INTERFACE (CONCEPT)  ·  FINAL PRODUCT FUNCTIONS FROM COMPARISON SOURCE")
    rrect(c, 56, 90, 400, 100, 10, WARN, LINE)
    draw_wrapped(c, "Q:  Ask a question about your enterprise documents…", 72, 154, FONT, 11, 370, 14, white)
    rrect(c, 476, 90, 428, 100, 10, WARN, LINE)
    draw_wrapped(
        c,
        "A:  Grounded answer  ·  Sources: report.pdf, data.xlsx  ·  Was this helpful?  Yes / No",
        492,
        154,
        FONT,
        11,
        396,
        14,
        white,
    )
    finish(c)


def slide_deploy_image(c, n, total):
    header_bar(c, "Proposed enterprise flow (source diagram in the template box)", n, total)
    c.setFillColor(MUTED)
    c.setFont(FONT, 8)
    c.drawString(36, 456, "Visual from the Final Comparison Report. Labels transcribed on the next page. Proposed / not claimed as implemented.")
    rrect(c, 36, 56, 888, 390, 12, HexColor("#F4F8FB"), CYAN)
    img = ASSETS / "proposed-deployment-source.png"
    c.drawImage(str(img), 48, 68, width=864, height=366, preserveAspectRatio=True, anchor="c", mask="auto")
    finish(c)


def slide_deploy_transcribe(c, n, total):
    header_bar(c, "Proposed enterprise flow — boxed transcription of the source diagram", n, total)
    items = [
        ("1. Enterprise data sources", "PDF documents; Excel spreadsheets; internal reports; databases (SharePoint, etc.); policies & guidelines."),
        ("2. Secure upload & validation", "File validation; access control (RBAC); virus/malware scan; document versioning; metadata capture."),
        ("3. Document processing", "PDF/Excel parsing; text extraction (OCR noted on diagram); content cleaning; semantic chunking; metadata tagging."),
        ("4. Embedding & indexing", "Generate vector embeddings; store in vector database; build searchable index; maintain metadata."),
        ("5. Vector database", "PostgreSQL + pgvector, Weaviate, Qdrant, etc. Document ingestion periodically or on new documents."),
        ("6. User query", "Enterprise web interface; SSO / authentication; role-based access; multi-language support."),
        ("7. Retrieval layer", "Query embedding; similarity search (Top-K); metadata filtering; optional re-ranking; retrieve relevant chunks."),
        ("8. RAG orchestration", "Combine query + retrieved context; instruction / system prompt; token-limit context management; safety and guardrails."),
        ("9. LLM inference (MI300X)", "Run LLM on AMD MI300X (ROCm); high-throughput inference; optimized for enterprise workloads; scalable and secure deployment."),
        ("10. Grounded response", "Source-grounded answer; citations and document links; reduced hallucinations; show relevant excerpts."),
        ("11. Enterprise application", "Q&A chat interface; document preview; conversation history; user feedback (thumbs up/down)."),
        ("12. Monitoring & improvement", "Usage analytics/KPIs; latency and throughput; GPU utilization (MI300X / ROCm); retrieval quality; ratings; index updates; security, compliance, and audit logs."),
    ]
    for i, (t, b) in enumerate(items):
        col = i % 3
        row = i // 3
        x = 36 + col * 308
        y = 348 - row * 96
        rrect(c, x, y, 296, 88, 10)
        c.setFillColor(CYAN)
        c.setFont(FONTB, 8)
        c.drawString(x + 10, y + 70, t.upper())
        draw_wrapped(c, b, x + 10, y + 54, FONT, 7.5, 276, 10, white)
    finish(c)


def slide_next(c, n, total):
    header_bar(c, "Request for renewed MI300X access", n, total)
    rrect(c, 36, 70, 430, 390)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(56, 430, "WHAT THE INITIAL ALLOCATION ACHIEVED")
    draw_wrapped(
        c,
        "The first MI300X allocation validated the technical feasibility of the full workflow on AMD hardware with PyTorch 2.3 / ROCm 6.2:",
        56,
        400,
        FONT,
        10,
        390,
        14,
        white,
    )
    bullets(
        c,
        [
            "Document indexing (PDF + Excel → 17 chunks)",
            "Normalized Top-3 semantic retrieval",
            "Qwen2.5-7B-Instruct inference (bfloat16)",
            "Source-grounded Traditional Chinese answers",
        ],
        56,
        330,
        FONT,
        11,
        390,
        28,
    )

    rrect(c, 494, 70, 430, 390)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 11)
    c.drawString(514, 430, "PLANNED NEXT STEPS WITH RENEWED ACCESS")
    steps = [
        "Expand official product and service documents",
        "Create a 50–100 question evaluation set",
        "Measure retrieval quality and inference performance reproducibly / systematically",
        "Build the proposed enterprise knowledge interface",
    ]
    y = 390
    for i, s in enumerate(steps, 1):
        c.setFillColor(CYAN)
        c.circle(532, y + 4, 10, fill=1, stroke=0)
        c.setFillColor(BG)
        c.setFont(FONTB, 9)
        c.drawCentredString(532, y + 1, str(i))
        draw_wrapped(c, s, 552, y, FONT, 11, 350, 14, white)
        y -= 44

    finish(c)


def slide_deliverables(c, n, total):
    header_bar(c, "Expected deliverables and closing", n, total)
    rrect(c, 36, 220, 888, 230)
    c.setFillColor(CYAN)
    c.setFont(FONTB, 12)
    c.drawString(56, 420, "EXPECTED DELIVERABLES (comparison source)")
    bullets(
        c,
        [
            "Reproducible MI300X benchmark report",
            "Validated source-grounded RAG results",
            "A proposed interface for enterprise knowledge support",
        ],
        56,
        380,
        FONT,
        13,
        840,
        32,
    )
    rrect(c, 36, 70, 888, 130)
    c.setFillColor(white)
    c.setFont(FONTB, 16)
    c.drawCentredString(480, 145, "Thank you to AMD and ITRI for enabling this work.")
    c.setFont(FONT, 10)
    c.setFillColor(MUTED)
    c.drawCentredString(480, 118, "Prepared/generated conversion  ·  2026-09-11  ·  Document-control attestation only")
    c.drawCentredString(480, 100, "Not a legal, cryptographic, or handwritten personal signature of any official")
    finish(c)


def main():
    total = 14
    c = canvas.Canvas(str(OUT_PDF), pagesize=(W, H))
    c.setTitle("AMD–ITRI Project Review — MI300X RAG (boxed template)")
    c.setAuthor("Prepared/generated from source reports — Dr. Ammar Amjad (source attribution)")
    c.setSubject("Boxed conversion of MI300X RAG comparison content onto the AMD–ITRI Project Review template")
    c.setCreator("AMD-ITRI boxed template conversion 2026-09-11")

    slide_control(c, total)
    slide_cover(c)
    slide_problem(c, 3, total)
    slide_objective(c, 4, total)
    slide_index(c, 5, total)
    slide_architecture(c, 6, total)
    slide_flow_image(c, 7, total)
    slide_models(c, 8, total)
    slide_results(c, 9, total)
    slide_deploy(c, 10, total)
    slide_deploy_image(c, 11, total)
    slide_deploy_transcribe(c, 12, total)
    slide_next(c, 13, total)
    slide_deliverables(c, 14, total)
    c.save()
    print("Wrote", OUT_PDF)


if __name__ == "__main__":
    main()
