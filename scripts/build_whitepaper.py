#!/usr/bin/env python3
"""Render the Markdown white paper as a polished, self-contained PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = HexColor("#071A2F")
INK = HexColor("#132238")
TEAL = HexColor("#087F7A")
MINT = HexColor("#44D3C3")
GOLD = HexColor("#F2B84B")
SLATE = HexColor("#60748A")
PALE = HexColor("#EEF5F7")
LINE = HexColor("#D7E2E8")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("docs/whitepaper.md"))
    parser.add_argument(
        "--output", type=Path, default=Path("output/pdf/agent-sentinel-whitepaper.pdf")
    )
    return parser.parse_args()


def ascii_safe(value: str) -> str:
    substitutions = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2192": "->",
        "\u00a0": " ",
    }
    for original, replacement in substitutions.items():
        value = value.replace(original, replacement)
    return value


def inline(value: str) -> str:
    value = html.escape(ascii_safe(value.strip()))
    value = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#087F7A"><u>\1</u></link>',
        value,
    )
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier" color="#0B6D68">\1</font>', value)
    return value


def styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=31,
            leading=34,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=7 * mm,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=16,
            leading=22,
            textColor=HexColor("#BFD1E1"),
            spaceAfter=7 * mm,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            textColor=MINT,
            spaceAfter=8 * mm,
        ),
        "h1": ParagraphStyle(
            "Section",
            parent=sample["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            textColor=NAVY,
            spaceBefore=8 * mm,
            spaceAfter=3.5 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Subsection",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=TEAL,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=14.2,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=3.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "BulletBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.5,
            textColor=INK,
            leftIndent=2 * mm,
            spaceAfter=1.3 * mm,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=sample["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9.4,
            leading=14.5,
            textColor=HexColor("#23445A"),
            backColor=PALE,
            borderColor=MINT,
            borderWidth=0.8,
            borderPadding=10,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            spaceBefore=2 * mm,
            spaceAfter=5 * mm,
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=7.8,
            leading=11,
            textColor=HexColor("#EAF4F7"),
            backColor=NAVY,
            borderPadding=9,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=10,
            textColor=SLATE,
            alignment=TA_CENTER,
        ),
        "reference": ParagraphStyle(
            "Reference",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=12,
            textColor=INK,
            leftIndent=6 * mm,
            firstLineIndent=-6 * mm,
            spaceAfter=2.5 * mm,
        ),
    }


def architecture_drawing() -> Drawing:
    drawing = Drawing(170 * mm, 55 * mm)
    box_width = 36 * mm
    box_height = 29 * mm
    gap = 7 * mm
    y = 12 * mm
    items = (
        ("1", "AI AGENT", "declared intent"),
        ("2", "K8S POD", "runtime effects"),
        ("3", "eBPF", "kernel evidence"),
        ("4", "SENTINEL", "bounded response"),
    )
    for index, (number, title, subtitle) in enumerate(items):
        x = index * (box_width + gap)
        color = TEAL if index < 3 else HexColor("#C78616")
        drawing.add(
            Rect(x, y, box_width, box_height, 4, 4, fillColor=colors.white, strokeColor=color)
        )
        drawing.add(
            Rect(x, y + box_height - 6 * mm, box_width, 6 * mm, fillColor=color, strokeColor=color)
        )
        drawing.add(
            String(
                x + 3 * mm,
                y + box_height - 4.3 * mm,
                number,
                fontName="Helvetica-Bold",
                fontSize=8,
                fillColor=colors.white,
            )
        )
        drawing.add(
            String(
                x + 4 * mm,
                y + 14 * mm,
                title,
                fontName="Helvetica-Bold",
                fontSize=8.3,
                fillColor=NAVY,
            )
        )
        drawing.add(
            String(
                x + 4 * mm,
                y + 8 * mm,
                subtitle,
                fontName="Helvetica",
                fontSize=6.8,
                fillColor=SLATE,
            )
        )
        if index < len(items) - 1:
            start = x + box_width
            end = start + gap - 1.5 * mm
            drawing.add(
                Line(
                    start,
                    y + box_height / 2,
                    end,
                    y + box_height / 2,
                    strokeColor=MINT,
                    strokeWidth=2,
                )
            )
            drawing.add(
                Line(
                    end,
                    y + box_height / 2,
                    end - 2 * mm,
                    y + box_height / 2 + 1.5 * mm,
                    strokeColor=MINT,
                    strokeWidth=2,
                )
            )
            drawing.add(
                Line(
                    end,
                    y + box_height / 2,
                    end - 2 * mm,
                    y + box_height / 2 - 1.5 * mm,
                    strokeColor=MINT,
                    strokeWidth=2,
                )
            )
    drawing.add(
        String(
            0,
            2 * mm,
            "Authorize the action. Verify its effects. Contain deviations.",
            fontName="Helvetica-Bold",
            fontSize=8,
            fillColor=MINT,
        )
    )
    return drawing


def cover(st: dict[str, ParagraphStyle]) -> list[object]:
    return [
        Spacer(1, 23 * mm),
        Paragraph("AGENT SENTINEL", st["cover_title"]),
        Paragraph(
            "Intent-Aware Runtime Detection and Adaptive Containment of Compromised AI Agents "
            "in Kubernetes Using eBPF",
            st["cover_subtitle"],
        ),
        Paragraph(
            "SHIVAM KUMAR &nbsp;&nbsp;|&nbsp;&nbsp; RESEARCH WHITE PAPER 0.1 "
            "&nbsp;&nbsp;|&nbsp;&nbsp; 25 AUGUST 2026",
            st["cover_meta"],
        ),
        architecture_drawing(),
        Spacer(1, 11 * mm),
        Paragraph(
            "Architecture proposal + executable research MVP. Quantitative comparative claims "
            "remain to be evaluated.",
            ParagraphStyle(
                "CoverStatus",
                parent=st["cover_subtitle"],
                fontSize=10.5,
                leading=15,
                textColor=HexColor("#D8E5EF"),
                borderColor=GOLD,
                borderWidth=0.8,
                borderPadding=9,
            ),
        ),
        PageBreak(),
    ]


def parse_table(rows: list[str], st: dict[str, ParagraphStyle]) -> Table:
    data: list[list[Paragraph]] = []
    for index, row in enumerate(rows):
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if index == 1 and all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        data.append([Paragraph(inline(cell), st["bullet"]) for cell in cells])
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def markdown_flowables(source: str, st: dict[str, ParagraphStyle]) -> list[object]:
    lines = source.splitlines()
    start = next((index for index, line in enumerate(lines) if line == "## Abstract"), 0)
    lines = lines[start:]
    output: list[object] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    code: list[str] = []
    in_code = False
    in_references = False
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            output.append(Paragraph(inline(" ".join(paragraph)), st["body"]))
            paragraph.clear()

    def flush_bullets() -> None:
        if bullets:
            items = [ListItem(Paragraph(inline(item), st["bullet"])) for item in bullets]
            output.append(ListFlowable(items, bulletType="bullet", bulletColor=TEAL, leftIndent=14))
            output.append(Spacer(1, 2 * mm))
            bullets.clear()

    while index < len(lines):
        line = ascii_safe(lines[index].rstrip())
        if line.startswith("```"):
            flush_paragraph()
            flush_bullets()
            if in_code:
                output.append(Preformatted("\n".join(code), st["code"]))
                code.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code.append(line)
            index += 1
            continue
        if line.startswith("| "):
            flush_paragraph()
            flush_bullets()
            rows: list[str] = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                rows.append(ascii_safe(lines[index]))
                index += 1
            output.append(KeepTogether([parse_table(rows, st), Spacer(1, 4 * mm)]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            heading = line[3:]
            if heading.startswith("9. ") or heading == "References":
                output.append(PageBreak())
            in_references = heading == "References"
            output.append(Paragraph(inline(heading), st["h1"]))
        elif line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            output.append(Paragraph(inline(line[4:]), st["h2"]))
        elif line.startswith("- "):
            flush_paragraph()
            bullets.append(line[2:])
        elif in_references and re.match(r"^\d+\. ", line):
            flush_paragraph()
            flush_bullets()
            reference = [line]
            while index + 1 < len(lines):
                candidate = ascii_safe(lines[index + 1].rstrip())
                if not candidate or re.match(r"^\d+\. ", candidate) or candidate.startswith("##"):
                    break
                index += 1
                reference.append(candidate.strip())
            output.append(Paragraph(inline(" ".join(reference)), st["reference"]))
        elif re.match(r"^\d+\. ", line):
            flush_paragraph()
            bullets.append(re.sub(r"^\d+\. ", "", line))
        elif line.startswith("> "):
            flush_paragraph()
            flush_bullets()
            quote = [line[2:]]
            while index + 1 < len(lines) and lines[index + 1].startswith(">"):
                index += 1
                quote.append(lines[index].lstrip("> "))
            output.append(Paragraph(inline(" ".join(quote)), st["quote"]))
        elif not line:
            flush_paragraph()
            flush_bullets()
        elif line == "---":
            flush_paragraph()
            flush_bullets()
            output.append(Spacer(1, 2 * mm))
        else:
            paragraph.append(line)
        index += 1
    flush_paragraph()
    flush_bullets()
    return output


def first_page(canvas: object, document: object) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 8 * mm, width, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 0, 9 * mm, height, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#93A9BD"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(
        width - 18 * mm, 13 * mm, "github.com/shivam2003-dev/agent-sentinel-ebpf"
    )
    canvas.restoreState()


def later_pages(canvas: object, document: object) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(1)
    canvas.line(19 * mm, height - 15 * mm, width - 19 * mm, height - 15 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(19 * mm, height - 11 * mm, "AGENT SENTINEL  /  RESEARCH WHITE PAPER 0.1")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(width - 19 * mm, 12 * mm, f"{document.page}")
    canvas.drawString(19 * mm, 12 * mm, "25 AUGUST 2026  |  APACHE-2.0 RESEARCH ARTIFACT")
    canvas.setStrokeColor(LINE)
    canvas.line(19 * mm, 17 * mm, width - 19 * mm, 17 * mm)
    canvas.restoreState()


def main() -> int:
    args = arguments()
    source = args.source.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    st = styles()
    document = SimpleDocTemplate(
        str(args.output),
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=22 * mm,
        bottomMargin=23 * mm,
        title="Agent Sentinel: Intent-Aware Runtime Detection and Adaptive Containment",
        author="Shivam Kumar",
        subject="AI agent runtime security using Kubernetes, eBPF, and Tetragon",
        creator="Agent Sentinel white paper build",
    )
    document.build(
        cover(st) + markdown_flowables(source, st), onFirstPage=first_page, onLaterPages=later_pages
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
