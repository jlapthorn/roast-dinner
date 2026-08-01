"""Generate a printable PDF for a cooking plan."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from fpdf import FPDF

from roast_dinner.planner import PlanEvent, PlanStep, build_timeline


def _pdf_text(value: str) -> str:
    """Core Helvetica fonts are Latin-1; normalize common Unicode punctuation."""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b0": " deg",
        "\u2022": "*",
        "\u00a0": " ",
    }
    text = value
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


class PlanPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(31, 58, 42)
        self.cell(0, 10, "Roast Dinner", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(68, 82, 68)
        self.cell(0, 6, "Cooking plan", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def render_plan_pdf(
    serve_at: datetime,
    earliest: datetime,
    steps: list[PlanStep],
) -> bytes:
    events = build_timeline(serve_at, steps)
    pdf = PlanPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(28, 38, 28)
    pdf.multi_cell(
        0,
        6,
        _pdf_text(
            f"Serve at {serve_at.strftime('%A %d %B %Y, %H:%M')}\n"
            f"Start cooking from {earliest.strftime('%H:%M')}"
        ),
    )
    pdf.ln(4)

    for event in events:
        _write_event(pdf, event)
        pdf.ln(3)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def _write_event(pdf: PlanPDF, event: PlanEvent) -> None:
    if pdf.get_y() > 250:
        pdf.add_page()

    label = {
        "start": "START",
        "take_out": "TAKE OUT",
        "serve": "SERVE",
    }.get(event.action, event.action.upper())

    if event.action == "take_out":
        pdf.set_fill_color(255, 243, 232)
        pdf.set_text_color(143, 52, 18)
    elif event.action == "serve":
        pdf.set_fill_color(231, 239, 228)
        pdf.set_text_color(31, 58, 42)
    else:
        pdf.set_fill_color(255, 252, 247)
        pdf.set_text_color(31, 58, 42)

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 11)
    title = f"{event.at.strftime('%H:%M')}  [{label}]  {event.title}"
    if event.temperature_c is not None and event.action == "start":
        title += f"  ({event.temperature_c}C fan)"
    pdf.multi_cell(0, 8, _pdf_text(title), fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(68, 82, 68)
    pdf.multi_cell(0, 5, _pdf_text(event.detail), new_x="LMARGIN", new_y="NEXT")

    if event.notes and event.action == "start":
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, _pdf_text(event.notes), new_x="LMARGIN", new_y="NEXT")
