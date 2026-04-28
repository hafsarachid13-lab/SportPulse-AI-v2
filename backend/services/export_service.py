"""
Export Service — Person 5 Module (Upgraded)
Multi-format export system:
  • PDF — professional report with cover page, sections, charts placeholder
  • Excel — multi-sheet workbook with styled headers
  • CSV — flat tabular export
  • JSON — full structured data
  • ZIP — all formats bundled
  • Export history tracking
"""

import os
import logging
import csv
import json
import uuid
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# PDF CLASS
# ──────────────────────────────────────────────────────────

class ReviewPDF(FPDF):
    """Custom PDF with branded header and footer."""

    def header(self):
        self.set_font("DejaVu", "", 16)
        self.set_text_color(20, 50, 100)
        self.cell(
            0, 12, "Daily Sports Press Review",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(150, 150, 150)
        self.set_draw_color(200, 200, 200)
        self.line(15, self.get_y() - 2, 195, self.get_y() - 2)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# ──────────────────────────────────────────────────────────
# EXPORT SERVICE
# ──────────────────────────────────────────────────────────

class ExportService:
    """Reusable multi-format export service with history tracking."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, output_dir: str = "static_exports"):
        if self._initialized:
            return
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Font path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.font_path = os.path.abspath(
            os.path.join(self.base_dir, "..", "fonts", "DejaVuSans.ttf")
        )

        # Export history
        self._export_history: List[Dict[str, Any]] = []
        self._initialized = True

    # ── Path helpers ──────────────────────────────────────

    def _get_filepath(self, filename: str) -> str:
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(f"Invalid filename: {filename}")
        return os.path.join(self.output_dir, filename)

    def get_export_path(self, filename: str) -> str:
        return self._get_filepath(filename)

    def _track_export(self, fmt: str, filename: str) -> Dict[str, Any]:
        """Track export in history and return record."""
        filepath = self._get_filepath(filename)
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        record = {
            "id": str(uuid.uuid4()),
            "format": fmt,
            "filename": filename,
            "generated_at": datetime.now().isoformat(),
            "file_size": file_size,
        }
        self._export_history.insert(0, record)
        # Keep last 100 export records
        self._export_history = self._export_history[:100]
        return record

    # ── Export History ─────────────────────────────────────

    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get export history records."""
        return self._export_history

    def get_export_stats(self) -> Dict[str, Any]:
        """Get export usage statistics."""
        from collections import Counter
        fmt_count = Counter(e["format"] for e in self._export_history)
        return {
            "total_exports": len(self._export_history),
            "by_format": dict(fmt_count),
            "recent_exports": self._export_history[:5],
        }

    def list_available_files(self) -> List[Dict[str, Any]]:
        """List all files in the export directory."""
        files = []
        if os.path.exists(self.output_dir):
            for fname in os.listdir(self.output_dir):
                fpath = os.path.join(self.output_dir, fname)
                if os.path.isfile(fpath):
                    files.append({
                        "filename": fname,
                        "size": os.path.getsize(fpath),
                        "modified_at": datetime.fromtimestamp(
                            os.path.getmtime(fpath)
                        ).isoformat(),
                    })
        return sorted(files, key=lambda x: x["modified_at"], reverse=True)

    # ──────────────────────────────────────────────────────
    # PDF EXPORT
    # ──────────────────────────────────────────────────────

    def generate_pdf(self, review_data: dict, filename: str = "review.pdf") -> str:
        """Generate a professionally formatted PDF report."""
        pdf = ReviewPDF()

        # Load font
        try:
            pdf.add_font("DejaVu", "", self.font_path, uni=True)
            font_family = "DejaVu"
        except Exception as e:
            logger.warning(f"Could not load DejaVu font, falling back to default: {e}")
            font_family = "Helvetica"

        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── COVER PAGE ──
        pdf.set_font(font_family, "", 24)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(20)
        pdf.cell(
            0, 12,
            review_data.get("title", "Sports Press Review"),
            new_x="LMARGIN", new_y="NEXT", align="C",
        )

        pdf.set_font(font_family, "", 12)
        pdf.set_text_color(100, 100, 100)
        date_str = review_data.get("generated_at", review_data.get("date", ""))[:10]
        pdf.cell(0, 8, f"Generated: {date_str}", new_x="LMARGIN", new_y="NEXT", align="C")

        # Statistics bar
        metadata = review_data.get("metadata", {})
        pdf.ln(10)
        pdf.set_font(font_family, "", 11)
        pdf.set_text_color(60, 60, 60)
        stats_line = (
            f"Total Articles: {metadata.get('total_articles', 0)}  |  "
            f"Sources: {metadata.get('sources_count', 0)}  |  "
            f"Categories: {metadata.get('categories_count', 0)}  |  "
            f"Avg Importance: {metadata.get('avg_importance', 0):.1%}"
        )
        pdf.cell(0, 8, stats_line, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        # ── EXECUTIVE SUMMARY ──
        sections = review_data.get("sections", {})
        exec_summary = sections.get("executive_summary", {})
        if exec_summary and exec_summary.get("text"):
            pdf.set_font(font_family, "", 14)
            pdf.set_text_color(200, 50, 50)
            pdf.cell(0, 10, exec_summary.get("title", "Executive Summary"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 50, 50)
            pdf.line(15, pdf.get_y(), 120, pdf.get_y())
            pdf.ln(4)

            pdf.set_font(font_family, "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, exec_summary["text"])
            pdf.ln(4)

            # Credibility indicator bar
            avg_cred = exec_summary.get("stats", {}).get("avg_credibility", 0)
            pdf.set_font(font_family, "", 9)
            pdf.set_text_color(80, 80, 80)
            cred_label = f"Overall Credibility: {avg_cred:.0%}"
            if avg_cred >= 0.8:
                cred_label += " — HIGH"
                pdf.set_text_color(34, 139, 34)
            elif avg_cred >= 0.5:
                cred_label += " — MEDIUM"
                pdf.set_text_color(200, 150, 0)
            else:
                cred_label += " — LOW"
                pdf.set_text_color(200, 50, 50)
            pdf.cell(0, 6, cred_label, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

        # ── TOP HEADLINES ──
        pdf.set_font(font_family, "", 16)
        pdf.set_text_color(40, 80, 150)
        pdf.cell(0, 10, "Top Headlines", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(40, 80, 150)
        pdf.line(15, pdf.get_y(), 100, pdf.get_y())
        pdf.ln(3)

        pdf.set_font(font_family, "", 11)
        pdf.set_text_color(50, 50, 50)
        headlines = review_data.get(
            "highlights", review_data.get("top_headlines", [])
        )[:5]
        for i, headline in enumerate(headlines, 1):
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 7, f"{i}. {headline}")
        pdf.ln(5)

        # ── SUMMARIES SECTION ──
        sections = review_data.get("sections", {})
        summaries_section = sections.get("summaries", {})
        if summaries_section.get("items"):
            pdf.add_page()
            pdf.set_font(font_family, "", 16)
            pdf.set_text_color(40, 80, 150)
            pdf.cell(0, 10, "Article Summaries", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(40, 80, 150)
            pdf.line(15, pdf.get_y(), 120, pdf.get_y())
            pdf.ln(5)

            for item in summaries_section["items"][:8]:
                pdf.set_font(font_family, "", 12)
                pdf.set_text_color(20, 20, 20)
                pdf.multi_cell(0, 6, item.get("title", ""))

                pdf.set_font(font_family, "", 9)
                pdf.set_text_color(120, 120, 120)
                importance = float(item.get("importance", 0))
                pdf.cell(
                    0, 5,
                    f"Source: {item.get('source', '')} | Sport: {item.get('sport', '')} | Score: {importance:.0%}",
                    new_x="LMARGIN", new_y="NEXT",
                )

                pdf.set_font(font_family, "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 5, item.get("summary", "No summary available."))
                pdf.ln(6)

        # ── CATEGORIES / ARTICLES ──
        for sport, articles in review_data.get("categories", {}).items():
            pdf.add_page()

            # Sport Header
            pdf.set_font(font_family, "", 18)
            pdf.set_text_color(200, 50, 50)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(
                0, 12, f" {sport.upper()} ",
                new_x="LMARGIN", new_y="NEXT", fill=True,
            )
            pdf.ln(5)

            for art in articles[:10]:
                pdf.set_font(font_family, "", 12)
                pdf.set_text_color(20, 20, 20)
                pdf.multi_cell(0, 6, art.get("title", "Untitled"))

                pdf.set_font(font_family, "", 9)
                pdf.set_text_color(120, 120, 120)
                score = float(art.get("importance_score", 0))
                source = art.get("source", "Unknown")
                pdf.cell(
                    0, 5,
                    f"Source: {source} | Score: {score:.2f}",
                    new_x="LMARGIN", new_y="NEXT",
                )

                pdf.set_font(font_family, "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 5, art.get("summary", "No summary available."))
                pdf.ln(5)

        # ── TRENDS PAGE ──
        trends = sections.get("trends", {})
        if trends:
            pdf.add_page()
            pdf.set_font(font_family, "", 16)
            pdf.set_text_color(40, 80, 150)
            pdf.cell(0, 10, "Trends & Insights", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(40, 80, 150)
            pdf.line(15, pdf.get_y(), 120, pdf.get_y())
            pdf.ln(5)

            # Trending sports
            pdf.set_font(font_family, "", 13)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, "Trending Sports:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(font_family, "", 11)
            for ts in trends.get("trending_sports", []):
                pdf.set_x(pdf.l_margin + 5)
                pdf.cell(
                    0, 6,
                    f"• {ts.get('sport', '')} — {ts.get('count', 0)} articles",
                    new_x="LMARGIN", new_y="NEXT",
                )
            pdf.ln(5)

            # Top keywords
            pdf.set_font(font_family, "", 13)
            pdf.cell(0, 8, "Top Keywords:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(font_family, "", 11)
            for kw in trends.get("top_keywords", [])[:10]:
                pdf.set_x(pdf.l_margin + 5)
                pdf.cell(
                    0, 6,
                    f"• {kw.get('keyword', '')} ({kw.get('count', 0)}x)",
                    new_x="LMARGIN", new_y="NEXT",
                )

        filepath = self._get_filepath(filename)
        pdf.output(filepath)
        logger.info(f"PDF exported: {filepath}")
        self._track_export("pdf", filename)
        return filename

    # ──────────────────────────────────────────────────────
    # EXCEL EXPORT
    # ──────────────────────────────────────────────────────

    def generate_excel(self, review_data: dict, filename: str = "review.xlsx") -> str:
        """Generate multi-sheet Excel workbook with styled headers."""
        wb = Workbook()

        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill("solid", fgColor="004E89")
        accent_fill = PatternFill("solid", fgColor="FF6B35")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        wrap_align = Alignment(wrap_text=True, vertical="top")
        center_align = Alignment(horizontal="center", vertical="center")

        def style_headers(ws, headers, fill=None):
            ws.append(headers)
            for col_num, cell in enumerate(ws[1], 1):
                cell.font = header_font
                cell.fill = fill or header_fill
                cell.alignment = center_align
                cell.border = border

        # ── Sheet 1: Overview ──
        ws_overview = wb.active
        ws_overview.title = "Overview"
        ws_overview.column_dimensions["A"].width = 30
        ws_overview.column_dimensions["B"].width = 50

        ws_overview.append(["Sports Press Review"])
        ws_overview.merge_cells("A1:B1")
        ws_overview["A1"].font = Font(bold=True, size=16, color="004E89")

        date_str = review_data.get("generated_at", review_data.get("date", ""))[:10]
        ws_overview.append(["Date", date_str])
        ws_overview.append([])

        metadata = review_data.get("metadata", {})
        ws_overview.append(["Metric", "Value"])
        ws_overview["A4"].font = Font(bold=True)
        ws_overview["B4"].font = Font(bold=True)
        ws_overview.append(["Total Articles", metadata.get("total_articles", 0)])
        ws_overview.append(["Sources Count", metadata.get("sources_count", 0)])
        ws_overview.append(["Categories Count", metadata.get("categories_count", 0)])
        ws_overview.append(["Avg Importance", f"{metadata.get('avg_importance', 0):.1%}"])
        ws_overview.append(["Avg Credibility", f"{metadata.get('avg_credibility', 0):.1%}"])
        ws_overview.append([])

        ws_overview.append(["Top Headlines"])
        ws_overview[f"A{ws_overview.max_row}"].font = Font(bold=True, size=12)
        for headline in review_data.get("highlights", review_data.get("top_headlines", []))[:10]:
            ws_overview.append([headline])

        # ── Sheet 2: All Articles ──
        ws_all = wb.create_sheet(title="All Articles")
        all_headers = [
            "Title", "Source", "Sport", "Importance", "Credibility",
            "Published Date", "Summary",
        ]
        style_headers(ws_all, all_headers)

        col_widths = [50, 20, 15, 12, 12, 18, 60]
        for i, w in enumerate(col_widths, 1):
            ws_all.column_dimensions[get_column_letter(i)].width = w

        for row_idx, art in enumerate(review_data.get("articles", []), 2):
            ws_all.cell(row=row_idx, column=1, value=art.get("title", ""))
            ws_all.cell(row=row_idx, column=2, value=art.get("source", ""))
            ws_all.cell(row=row_idx, column=3, value=art.get("sport", ""))
            ws_all.cell(row=row_idx, column=4, value=float(art.get("importance_score", 0)))
            ws_all.cell(row=row_idx, column=5, value=float(art.get("credibility", 0.75)))
            ws_all.cell(row=row_idx, column=6, value=art.get("published_date", ""))
            summary_cell = ws_all.cell(row=row_idx, column=7, value=art.get("summary", ""))
            summary_cell.alignment = wrap_align
            for col in range(1, 8):
                ws_all.cell(row=row_idx, column=col).border = border

        # ── Per-sport sheets ──
        sport_headers = ["Title", "Source", "Importance Score", "Summary"]
        for sport, articles in review_data.get("categories", {}).items():
            safe_name = sport[:31].replace("/", "-").replace("\\", "-")
            ws = wb.create_sheet(title=safe_name)
            style_headers(ws, sport_headers, fill=accent_fill)

            ws.column_dimensions["A"].width = 50
            ws.column_dimensions["B"].width = 20
            ws.column_dimensions["C"].width = 15
            ws.column_dimensions["D"].width = 80

            for row_idx, art in enumerate(articles, 2):
                ws.cell(row=row_idx, column=1, value=art.get("title", ""))
                ws.cell(row=row_idx, column=2, value=art.get("source", ""))
                ws.cell(row=row_idx, column=3, value=float(art.get("importance_score", 0)))
                summary_cell = ws.cell(row=row_idx, column=4, value=art.get("summary", ""))
                summary_cell.alignment = wrap_align
                for col in range(1, 5):
                    ws.cell(row=row_idx, column=col).border = border

        # ── Sources Sheet ──
        ws_sources = wb.create_sheet(title="Sources")
        source_headers = ["Source", "Articles", "Avg Importance", "Credibility"]
        style_headers(ws_sources, source_headers)
        ws_sources.column_dimensions["A"].width = 30

        sections = review_data.get("sections", {})
        top_sources = sections.get("top_sources", {}).get("sources", [])
        for row_idx, src in enumerate(top_sources, 2):
            ws_sources.cell(row=row_idx, column=1, value=src.get("source", ""))
            ws_sources.cell(row=row_idx, column=2, value=src.get("article_count", 0))
            ws_sources.cell(row=row_idx, column=3, value=src.get("avg_importance", 0))
            ws_sources.cell(row=row_idx, column=4, value=src.get("credibility", 0))

        filepath = self._get_filepath(filename)
        wb.save(filepath)
        logger.info(f"Excel exported: {filepath}")
        self._track_export("excel", filename)
        return filename

    # ──────────────────────────────────────────────────────
    # CSV EXPORT
    # ──────────────────────────────────────────────────────

    def generate_csv(self, review_data: dict, filename: str = "review.csv") -> str:
        """Generate flat CSV export."""
        filepath = self._get_filepath(filename)
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Category", "Title", "Source", "Importance Score",
                "Credibility", "Published Date", "Keywords", "Summary",
            ])

            for sport, articles in review_data.get("categories", {}).items():
                for art in articles:
                    keywords = art.get("keywords", [])
                    kw_str = "; ".join(keywords) if isinstance(keywords, list) else str(keywords)
                    writer.writerow([
                        sport,
                        art.get("title", ""),
                        art.get("source", ""),
                        float(art.get("importance_score", 0)),
                        float(art.get("credibility", 0.75)),
                        art.get("published_date", ""),
                        kw_str,
                        art.get("summary", ""),
                    ])
        logger.info(f"CSV exported: {filepath}")
        self._track_export("csv", filename)
        return filename

    # ──────────────────────────────────────────────────────
    # JSON EXPORT
    # ──────────────────────────────────────────────────────

    def generate_json(self, review_data: dict, filename: str = "review.json") -> str:
        """Generate full structured JSON export."""
        filepath = self._get_filepath(filename)
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=4, ensure_ascii=False, default=str)
        logger.info(f"JSON exported: {filepath}")
        self._track_export("json", filename)
        return filename

    # ──────────────────────────────────────────────────────
    # ZIP EXPORT
    # ──────────────────────────────────────────────────────

    def generate_zip(
        self, review_data: dict, filename: str = "review_exports.zip"
    ) -> str:
        """Generate ZIP bundle with all format exports."""
        pdf_file = self.generate_pdf(review_data, "review.pdf")
        excel_file = self.generate_excel(review_data, "review.xlsx")
        csv_file = self.generate_csv(review_data, "review.csv")
        json_file = self.generate_json(review_data, "review.json")

        filepath = self._get_filepath(filename)
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self._get_filepath(pdf_file), arcname=pdf_file)
            zipf.write(self._get_filepath(excel_file), arcname=excel_file)
            zipf.write(self._get_filepath(csv_file), arcname=csv_file)
            zipf.write(self._get_filepath(json_file), arcname=json_file)

        logger.info(f"ZIP exported: {filepath}")
        self._track_export("zip", filename)
        return filename
