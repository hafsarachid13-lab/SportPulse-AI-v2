"""
Professional Sports Press Review PDF
Modern magazine-quality layout with:
- Unicode + Arabic support
- Clickable article links
- Clean article cards
- Cover page
- Executive summary
- Headlines
- Trends
"""

import re
import logging
from fpdf import FPDF

logger = logging.getLogger(__name__)

# ── Arabic Support ──────────────────────────────────────
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False


# ── COLORS ──────────────────────────────────────────────
NAVY       = (10, 22, 40)
NAVY_MID   = (18, 36, 65)
ORANGE     = (255, 107, 53)

WHITE      = (255, 255, 255)
LIGHT_BG   = (244, 246, 248)
CARD_BG    = (252, 253, 255)

TEXT_PRI   = (25, 30, 40)
TEXT_SEC   = (90, 100, 115)
TEXT_MUTED = (145, 152, 165)

DIVIDER    = (215, 220, 230)

SCORE_HI   = (46, 125, 50)
SCORE_MED  = (255, 152, 0)
SCORE_LO   = (158, 158, 158)

LINK_BLUE  = (21, 101, 192)


SPORT_COLORS = {
    "football": (46, 125, 50),
    "soccer": (46, 125, 50),
    "basketball": (230, 81, 0),
    "tennis": (21, 101, 192),
    "golf": (27, 94, 32),
    "mma": (183, 28, 28),
    "boxing": (183, 28, 28),
    "rugby": (51, 105, 30),
    "formula 1": (198, 40, 40),
    "cycling": (216, 67, 21),
    "esport": (0, 131, 143),
}


# ────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────

def _sport_color(name: str):
    return SPORT_COLORS.get(
        str(name).lower().strip(),
        (55, 71, 79)
    )


def clean_summary(text: str) -> str:

    if not text:
        return ""

    text = str(text)

    # Remove URLs
    text = re.sub(r"http\S+", "", text)

    # Remove image credits
    text = re.sub(
        r"\(.*?(Getty|Reuters|AFP|AP|Photo).*?\)",
        "",
        text,
        flags=re.I
    )

    # Remove scores
    text = re.sub(r"Score:\s*\d+\-\d+", "", text)

    # Remove repeated punctuation
    text = re.sub(r"[•·]+", " ", text)
    text = re.sub(r"\.{2,}", ".", text)

    # Remove duplicate spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _safe_float(val, default=0):
    try:
        return float(val)
    except:
        return default


def _safe_text(text: str, unicode_font=True):

    if not text:
        return ""

    text = str(text)

    if unicode_font and HAS_ARABIC:
        try:
            if re.search(r'[\u0600-\u06FF]', text):
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
        except Exception:
            pass

    return text


# ────────────────────────────────────────────────────────
# MAIN CLASS
# ────────────────────────────────────────────────────────

class ReviewPDF(FPDF):

    def __init__(
        self,
        body_font="DejaVu",
        report_date="",
        **kw
    ):
        super().__init__(**kw)

        self.body_font = body_font
        self._report_date = report_date
        self._unicode = True
        self._is_cover = True

    @property
    def epw(self):
        return self.w - self.l_margin - self.r_margin

    def _t(self, text):
        return _safe_text(text, self._unicode)

    # ────────────────────────────────────────────────────
    # HEADER
    # ────────────────────────────────────────────────────

    def header(self):

        if self._is_cover:
            return

        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 8, "F")

        self.set_fill_color(*ORANGE)
        self.rect(0, 8, 210, 1, "F")

        self.set_y(2)

        self.set_font(self.body_font, "B", 8)
        self.set_text_color(255, 255, 255)

        self.cell(
            120,
            4,
            "SPORTS INTELLIGENCE REPORT"
        )

        self.set_font(self.body_font, "", 8)

        self.cell(
            0,
            4,
            self._report_date,
            align="R",
            ln=1
        )

        self.set_y(14)

    # ────────────────────────────────────────────────────
    # FOOTER
    # ────────────────────────────────────────────────────

    def footer(self):

        if self._is_cover:
            return

        self.set_y(-15)

        self.set_draw_color(*DIVIDER)

        self.line(
            self.l_margin,
            self.get_y(),
            210 - self.r_margin,
            self.get_y()
        )

        self.set_y(-11)

        self.set_font(self.body_font, "", 7)
        self.set_text_color(*TEXT_MUTED)

        self.cell(
            0,
            5,
            f"Confidential Intelligence Summary  |  Page {self.page_no()}",
            align="C"
        )

    # ────────────────────────────────────────────────────
    # SECTION TITLE
    # ────────────────────────────────────────────────────

    def _section_title(self, title, color=NAVY):

        y = self.get_y()

        self.set_fill_color(*color)
        self.rect(self.l_margin, y, 4, 10, "F")

        self.set_x(self.l_margin + 8)

        self.set_font(self.body_font, "B", 16)
        self.set_text_color(*color)

        self.cell(
            0,
            10,
            self._t(title.upper())
        )

        self.ln(15)

    # ────────────────────────────────────────────────────
    # SCORE BADGE
    # ────────────────────────────────────────────────────

    def _score_badge(self, score, x, y):

        if score <= 1:
            score *= 100

        if score >= 80:
            bg = SCORE_HI
            label = "HIGH"

        elif score >= 50:
            bg = SCORE_MED
            label = "MED"

        else:
            bg = SCORE_LO
            label = "LOW"

        self.set_fill_color(*bg)

        self.rect(x, y, 22, 7, "F")

        self.set_xy(x, y)

        self.set_font(self.body_font, "B", 7)
        self.set_text_color(255, 255, 255)

        self.cell(
            22,
            7,
            f"{int(score)} {label}",
            align="C"
        )

    # ────────────────────────────────────────────────────
    # PAGE SPACE CHECK
    # ────────────────────────────────────────────────────

    def _check_page_space(self, needed_h):

        if self.get_y() + needed_h > self.h - 20:
            self.add_page()

    # ────────────────────────────────────────────────────
    # COVER PAGE
    # ────────────────────────────────────────────────────

    def draw_cover(self, title, date_str, metadata):

        self._is_cover = True

        self.add_page()

        self.set_fill_color(*NAVY)

        self.rect(0, 0, 210, 297, "F")

        self.set_y(60)

        self.set_font(self.body_font, "B", 12)
        self.set_text_color(*ORANGE)

        self.cell(
            0,
            10,
            "AUTOMATED NEWS ANALYTICS",
            align="C",
            ln=1
        )

        self.set_font(self.body_font, "B", 38)
        self.set_text_color(255, 255, 255)

        self.multi_cell(
            0,
            18,
            "SPORTS\nINTELLIGENCE",
            align="C"
        )

        self.ln(6)

        self.set_fill_color(*ORANGE)
        self.rect(85, self.get_y(), 40, 3, "F")

        self.ln(15)

        self.set_font(self.body_font, "", 16)
        self.set_text_color(200, 210, 230)

        self.cell(
            0,
            10,
            date_str,
            align="C",
            ln=1
        )

        stats = [
            (str(metadata.get("total_articles", 0)), "ARTICLES"),
            (str(metadata.get("sources_count", 0)), "SOURCES"),
            (str(metadata.get("categories_count", 0)), "CATEGORIES"),
        ]

        y_stats = 220
        box_w = 50
        gap = 10

        start_x = (
            210 - (box_w * 3 + gap * 2)
        ) / 2

        for i, (val, lbl) in enumerate(stats):

            x = start_x + i * (box_w + gap)

            self.set_fill_color(*NAVY_MID)
            self.rect(x, y_stats, box_w, 35, "F")

            self.set_fill_color(*ORANGE)
            self.rect(x, y_stats, box_w, 1.5, "F")

            self.set_xy(x, y_stats + 8)

            self.set_font(self.body_font, "B", 20)
            self.set_text_color(255, 255, 255)

            self.cell(box_w, 10, val, align="C", ln=1)

            self.set_x(x)

            self.set_font(self.body_font, "", 8)
            self.set_text_color(160, 180, 200)

            self.cell(box_w, 8, lbl, align="C")

        self.set_xy(0, 270)

        self.set_font(self.body_font, "", 9)
        self.set_text_color(100, 120, 150)

        self.cell(
            210,
            10,
            "Generated by AI Sports News Engine",
            align="C"
        )

        self._is_cover = False

    # ────────────────────────────────────────────────────
    # EXECUTIVE SUMMARY
    # ────────────────────────────────────────────────────

    def draw_executive_summary(self, exec_data):

        if not exec_data:
            return

        text = exec_data.get("text")

        if not text:
            return

        self.add_page()

        self._section_title("Executive Summary")

        text = self._t(clean_summary(text))

        self.set_font(self.body_font, "", 11)

        h = len(
            self.multi_cell(
                self.epw - 15,
                6,
                text,
                split_only=True
            )
        ) * 6

        y = self.get_y()

        self.set_fill_color(*LIGHT_BG)

        self.rect(
            self.l_margin,
            y,
            self.epw,
            h + 15,
            "F"
        )

        self.set_xy(self.l_margin + 7, y + 7)

        self.set_text_color(*TEXT_PRI)

        self.multi_cell(
            self.epw - 14,
            6,
            text
        )

        self.ln(10)

    # ────────────────────────────────────────────────────
    # HEADLINES
    # ────────────────────────────────────────────────────

    def draw_headlines(self, headlines):

        if not headlines:
            return

        self._section_title("Critical Headlines")

        for i, hl in enumerate(headlines[:5], 1):

            self._check_page_space(15)

            y = self.get_y()

            self.set_fill_color(*ORANGE)
            self.rect(self.l_margin, y, 6, 6, "F")

            self.set_xy(self.l_margin, y)

            self.set_font(self.body_font, "B", 8)
            self.set_text_color(255, 255, 255)

            self.cell(6, 6, str(i), align="C")

            self.set_xy(self.l_margin + 10, y)

            self.set_font(self.body_font, "B", 11)
            self.set_text_color(*TEXT_PRI)

            self.multi_cell(
                self.epw - 12,
                6,
                self._t(hl)
            )

            self.ln(4)

    # ────────────────────────────────────────────────────
    # CATEGORY
    # ────────────────────────────────────────────────────

    def draw_category(self, sport_name, articles):

        if not articles:
            return

        self.add_page()

        color = _sport_color(sport_name)

        y = self.get_y()

        self.set_fill_color(*color)

        self.rect(
            self.l_margin,
            y,
            self.epw,
            15,
            "F"
        )

        self.set_xy(self.l_margin + 5, y + 2)

        self.set_font(self.body_font, "B", 15)
        self.set_text_color(255, 255, 255)

        self.cell(
            0,
            10,
            self._t(sport_name.upper())
        )

        self.set_y(y + 22)

        articles = [
            a for a in articles
            if len(a.get("summary", "")) > 40
        ]

        for art in articles:
            self._draw_article_card(art, color)

    # ────────────────────────────────────────────────────
    # ARTICLE CARD
    # ────────────────────────────────────────────────────

    def _draw_article_card(self, art, accent_color):

        title = self._t(
            art.get("title", "Untitled")
        )[:180]

        source = art.get(
            "source",
            "Unknown"
        )

        date = (
            art.get("published_date", "")
            or art.get("date", "")
        )[:10]

        summary = clean_summary(
            self._t(
                art.get(
                    "summary",
                    "No summary available."
                )
            )
        )

        if len(summary) > 280:
            summary = summary[:280] + "..."

        article_url = (
            art.get("url")
            or art.get("link")
        )

        score = _safe_float(
            art.get("importance_score", 0)
        )

        # Measure card
        self.set_font(self.body_font, "B", 11)

        title_lines = max(
            1,
            len(
                self.multi_cell(
                    self.epw - 38,
                    6.5,
                    title,
                    split_only=True
                )
            )
        )

        self.set_font(self.body_font, "", 9)

        summary_lines = max(
            1,
            len(
                self.multi_cell(
                    self.epw - 14,
                    6,
                    summary,
                    split_only=True
                )
            )
        )

        needed_h = (
            title_lines * 7
            + summary_lines * 6
            + 35
        )

        self._check_page_space(needed_h + 10)

        y_start = self.get_y()

        # Background
        self.set_fill_color(*CARD_BG)
        self.set_draw_color(*DIVIDER)

        self.rect(
            self.l_margin,
            y_start,
            self.epw,
            needed_h,
            "FD"
        )

        # Accent Bar
        self.set_fill_color(*accent_color)

        self.rect(
            self.l_margin,
            y_start,
            3,
            needed_h,
            "F"
        )

        # Score badge
        self._score_badge(
            score,
            210 - self.r_margin - 28,
            y_start + 4
        )

        # Title
        self.set_xy(
            self.l_margin + 8,
            y_start + 5
        )

        self.set_font(self.body_font, "B", 11)
        self.set_text_color(*TEXT_PRI)

        self.multi_cell(
            self.epw - 38,
            6.5,
            title
        )

        self.ln(1)

        # Meta
        self.set_x(self.l_margin + 8)

        self.set_font(self.body_font, "", 8)
        self.set_text_color(*TEXT_SEC)

        meta = (
            f"{source}  •  {date}"
            if date else source
        )

        if article_url:

            self.cell(
                0,
                5,
                self._t(meta),
                ln=1,
                link=article_url
            )

        else:

            self.cell(
                0,
                5,
                self._t(meta),
                ln=1
            )

        self.ln(3)

        # Summary
        self.set_x(self.l_margin + 8)

        self.set_font(self.body_font, "", 9)
        self.set_text_color(60, 65, 75)

        self.multi_cell(
            self.epw - 14,
            6,
            summary
        )

        # Clickable link
        if article_url:

            self.ln(3)

            self.set_x(self.l_margin + 8)

            self.set_font(self.body_font, "B", 9)
            self.set_text_color(*LINK_BLUE)

            self.cell(
                45,
                6,
                "Read Full Article →",
                link=article_url
            )

        self.set_text_color(*TEXT_PRI)

        self.set_y(y_start + needed_h + 6)

    # ────────────────────────────────────────────────────
    # TRENDS
    # ────────────────────────────────────────────────────

    def draw_trends(self, trends_data):

        if not trends_data:
            return

        self.add_page()

        self._section_title("Market Analysis")

        trending = trends_data.get(
            "trending_sports",
            []
        )

        if trending:

            self.set_font(self.body_font, "B", 12)
            self.set_text_color(*TEXT_PRI)

            self.cell(
                0,
                10,
                "Volume by Category",
                ln=1
            )

            max_count = max(
                [x.get("count", 1) for x in trending],
                default=1
            )

            bar_max = self.epw - 60

            for t in trending:

                sport = t.get("sport", "Unknown")
                count = t.get("count", 0)

                color = _sport_color(sport)

                bw = (
                    count / max_count
                ) * bar_max

                y = self.get_y()

                self.set_font(self.body_font, "B", 9)
                self.set_text_color(*TEXT_PRI)

                self.cell(
                    40,
                    8,
                    self._t(sport)
                )

                self.set_fill_color(*color)

                self.rect(
                    self.l_margin + 42,
                    y + 2,
                    max(bw, 2),
                    4,
                    "F"
                )

                self.set_xy(
                    self.l_margin + 45 + bw,
                    y
                )

                self.cell(
                    20,
                    8,
                    str(count)
                )

                self.ln(10)
