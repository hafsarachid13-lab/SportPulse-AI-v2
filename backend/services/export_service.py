import os
import logging
import csv
import json
import zipfile
from datetime import datetime
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

logger = logging.getLogger(__name__)


class ReviewPDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "", 16)
        self.set_text_color(20, 50, 100)
        self.cell(0, 12, "Daily Sports Press Review", new_x="LMARGIN", new_y="NEXT", align="C")
        
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


class ExportService:
    def __init__(self, output_dir: str = "static_exports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Determine font path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.font_path = os.path.abspath(os.path.join(self.base_dir, "..", "fonts", "DejaVuSans.ttf"))

    def _get_filepath(self, filename: str) -> str:
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(f"Invalid filename: {filename}")
        return os.path.join(self.output_dir, filename)

    def get_export_path(self, filename: str) -> str:
        return self._get_filepath(filename)

    def generate_pdf(self, review_data: dict, filename: str = "review.pdf") -> str:
        pdf = ReviewPDF()
        
        # Use DejaVu for Unicode support
        try:
            pdf.add_font("DejaVu", "", self.font_path, uni=True)
            font_family = "DejaVu"
        except Exception as e:
            logger.warning(f"Could not load DejaVu font, falling back to default: {e}")
            font_family = "Helvetica"
            
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # COVER PAGE INFO
        pdf.set_font(font_family, "", 22)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(10)
        pdf.cell(0, 10, review_data.get("title", "Sports Press Review"), new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_font(font_family, "", 12)
        pdf.set_text_color(100, 100, 100)
        date_str = review_data.get('generated_at', review_data.get('date', ''))[:10]
        pdf.cell(0, 8, f"Date: {date_str}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        # TOP HEADLINES
        pdf.set_font(font_family, "", 14)
        pdf.set_text_color(40, 80, 150)
        pdf.cell(0, 10, "Top Headlines", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font(font_family, "", 11)
        pdf.set_text_color(50, 50, 50)
        for headline in review_data.get("highlights", review_data.get("top_headlines", []))[:5]:
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 7, f"• {headline}")
        pdf.ln(5)
        
        # CATEGORIES / ARTICLES
        for sport, articles in review_data.get("categories", {}).items():
            pdf.add_page()
            
            # Sport Header
            pdf.set_font(font_family, "", 18)
            pdf.set_text_color(200, 50, 50)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, 12, f" {sport.upper()} ", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(5)
            
            for art in articles[:10]:
                pdf.set_font(font_family, "", 12)
                pdf.set_text_color(20, 20, 20)
                pdf.multi_cell(0, 6, art.get("title", "Untitled"))
                
                pdf.set_font(font_family, "", 9)
                pdf.set_text_color(120, 120, 120)
                score = float(art.get('importance_score', 0))
                source = art.get('source', 'Unknown')
                pdf.cell(0, 5, f"Source: {source} | Score: {score:.2f}", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font(font_family, "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 5, art.get("summary", "No summary available."))
                pdf.ln(5)
                
        filepath = self._get_filepath(filename)
        pdf.output(filepath)
        logger.info(f"PDF exported: {filepath}")
        return filename

    def generate_excel(self, review_data: dict, filename: str = "review.xlsx") -> str:
        wb = Workbook()
        
        # Helper styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="4F81BD")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        def apply_header_styles(ws, headers):
            ws.append(headers)
            for col_num, cell in enumerate(ws[1], 1):
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
                cell.border = border
                ws.column_dimensions[cell.column_letter].width = 20
        
        # Sheet 1: Overview
        ws_overview = wb.active
        ws_overview.title = "Overview"
        ws_overview.append(["Sports Press Review"])
        ws_overview.append(["Date", review_data.get('generated_at', review_data.get('date', ''))[:10]])
        ws_overview.append([])
        
        ws_overview.append(["Top Headlines"])
        ws_overview.column_dimensions["A"].width = 80
        for i, headline in enumerate(review_data.get("highlights", review_data.get("top_headlines", [])), 5):
            cell = ws_overview.cell(row=i, column=1, value=headline)
            cell.border = border

        # Create one sheet per sport category
        headers = ["Title", "Source", "Importance Score", "Summary"]
        for sport, articles in review_data.get("categories", {}).items():
            # Max length for sheet name is 31
            ws = wb.create_sheet(title=sport[:31])
            apply_header_styles(ws, headers)
            
            ws.column_dimensions["A"].width = 50
            ws.column_dimensions["B"].width = 20
            ws.column_dimensions["C"].width = 15
            ws.column_dimensions["D"].width = 80
            
            for row_idx, art in enumerate(articles, 2):
                ws.cell(row=row_idx, column=1, value=art.get("title", ""))
                ws.cell(row=row_idx, column=2, value=art.get("source", ""))
                ws.cell(row=row_idx, column=3, value=float(art.get("importance_score", 0)))
                
                # Wrap text for summary
                summary_cell = ws.cell(row=row_idx, column=4, value=art.get("summary", ""))
                summary_cell.alignment = Alignment(wrap_text=True)
                
                for col in range(1, 5):
                    ws.cell(row=row_idx, column=col).border = border

        filepath = self._get_filepath(filename)
        wb.save(filepath)
        logger.info(f"Excel exported: {filepath}")
        return filename

    def generate_csv(self, review_data: dict, filename: str = "review.csv") -> str:
        filepath = self._get_filepath(filename)
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Title", "Source", "Score", "Summary"])
            
            for sport, articles in review_data.get("categories", {}).items():
                for art in articles:
                    writer.writerow([
                        sport,
                        art.get("title", ""),
                        art.get("source", ""),
                        float(art.get("importance_score", 0)),
                        art.get("summary", "")
                    ])
        logger.info(f"CSV exported: {filepath}")
        return filename

    def generate_json(self, review_data: dict, filename: str = "review.json") -> str:
        filepath = self._get_filepath(filename)
        with open(filepath, mode='w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=4, ensure_ascii=False)
        logger.info(f"JSON exported: {filepath}")
        return filename

    def generate_zip(self, review_data: dict, filename: str = "review_exports.zip") -> str:
        # Generate all files temporarily
        pdf_file = self.generate_pdf(review_data, "review.pdf")
        excel_file = self.generate_excel(review_data, "review.xlsx")
        csv_file = self.generate_csv(review_data, "review.csv")
        json_file = self.generate_json(review_data, "review.json")
        
        filepath = self._get_filepath(filename)
        with zipfile.ZipFile(filepath, 'w') as zipf:
            zipf.write(self._get_filepath(pdf_file), arcname=pdf_file)
            zipf.write(self._get_filepath(excel_file), arcname=excel_file)
            zipf.write(self._get_filepath(csv_file), arcname=csv_file)
            zipf.write(self._get_filepath(json_file), arcname=json_file)
            
        logger.info(f"ZIP exported: {filepath}")
        return filename
