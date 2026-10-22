from fpdf import FPDF
import pymupdf as fitz  # PyMuPDF
import io
import os
from pathlib import Path


COLOR_PALETTES = {
    "Mauve & Plum Velvet": {
        "primary": "#4A355E",
        "secondary": "#6D5284",
        "subheading": "#8D73A8",
        "border": "#B39CCB",
        "badge": "#D7B6C7",
        "tint": "#F7EEF2",
    },
    "Classic Black & White": {
        "primary": "#111827",
        "secondary": "#4B5563",
        "subheading": "#374151",
        "border": "#D1D5DB",
        "badge": "#E5E7EB",
        "tint": "#FFFFFF",
    },
    "Navy & Cool Gray": {
        "primary": "#0F172A",
        "secondary": "#334155",
        "subheading": "#475569",
        "border": "#CBD5E1",
        "badge": "#E2E8F0",
        "tint": "#F8FAFC",
    },
    "Charcoal & Slate": {
        "primary": "#2B2D42",
        "secondary": "#4A4E69",
        "subheading": "#8D99AE",
        "border": "#C9D1D9",
        "badge": "#E0E1DD",
        "tint": "#EDF2F4",
    },
    "Emerald & Mint": {
        "primary": "#064E3B",
        "secondary": "#047857",
        "subheading": "#0D9488",
        "border": "#A7F3D0",
        "badge": "#D1FAE5",
        "tint": "#ECFDF5",
    },
    "Burgundy & Cream": {
        "primary": "#581845",
        "secondary": "#900C3F",
        "subheading": "#C70039",
        "border": "#E8D8D8",
        "badge": "#F5EBE6",
        "tint": "#FAF3E0",
    },
    "Midnight & Royal Blue": {
        "primary": "#0A192F",
        "secondary": "#1E3A8A",
        "subheading": "#2563EB",
        "border": "#BFDBFE",
        "badge": "#DBEAFE",
        "tint": "#F0F9FF",
    },
    "Deep Forest Green": {
        "primary": "#1B4332",
        "secondary": "#2D6A4F",
        "subheading": "#40916C",
        "border": "#B7E4C7",
        "badge": "#D8F3DC",
        "tint": "#F4FAF6",
    },
    "Teal & Seafoam": {
        "primary": "#134E4A",
        "secondary": "#0D9488",
        "subheading": "#14B8A6",
        "border": "#99F6E4",
        "badge": "#CCFBF1",
        "tint": "#F0FDFA",
    },
    "Espresso & Sand": {
        "primary": "#3E2723",
        "secondary": "#5D4037",
        "subheading": "#795548",
        "border": "#D7CCC8",
        "badge": "#EFEBE9",
        "tint": "#F5F2EB",
    },
    "Sapphire & Amber": {
        "primary": "#1E3A8A",
        "secondary": "#B45309",
        "subheading": "#D97706",
        "border": "#FDE68A",
        "badge": "#FEF3C7",
        "tint": "#FFFBEB",
    },
    "Steel & Ice Gray": {
        "primary": "#374151",
        "secondary": "#4B5563",
        "subheading": "#6B7280",
        "border": "#D1D5DB",
        "badge": "#E5E7EB",
        "tint": "#F3F4F6",
    },
    "Crimson & Rose": {
        "primary": "#881337",
        "secondary": "#BE123C",
        "subheading": "#E11D48",
        "border": "#FECDD3",
        "badge": "#FFE4E6",
        "tint": "#FFF1F2",
    },
    "Modern Olive & Khaki": {
        "primary": "#3F4E4F",
        "secondary": "#2C3639",
        "subheading": "#A27B5C",
        "border": "#DCD7C9",
        "badge": "#EAE5D9",
        "tint": "#F7F5F0",
    },
    "Amethyst & Lilac": {
        "primary": "#3B185F",
        "secondary": "#6A1B9A",
        "subheading": "#9333EA",
        "border": "#E9D5FF",
        "badge": "#F3E8FF",
        "tint": "#FAF5FF",
    },
    "Cobalt & Silver": {
        "primary": "#1D4ED8",
        "secondary": "#3B82F6",
        "subheading": "#64748B",
        "border": "#CBD5E1",
        "badge": "#E2E8F0",
        "tint": "#F8FAFC",
    },
}


def _hex_to_rgb(color):
    value = color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


PDF_PALETTES_HEX = {
    "Mauve & Plum Velvet": {
        "primary": "#4A355E",
        "secondary": "#6D5284",
        "accent": "#6D5284",
        "subheadings": "#8D73A8",
        "border": "#B39CCB",
        "soft_accent": "#D7B6C7",
        "light_shade": "#EBCED6",
        "paper": "#F7EEF2",
        "body": "#352742",
        "muted": "#8D73A8",
        "soft": "#F7EEF2",
    },
    "Classic Black & White": {
        "primary": "#111827",
        "accent": "#4B5563",
        "body": "#1f2937",
        "muted": "#4B5563",
        "soft": "#F3F4F6",
        "paper": "#FFFFFF",
        "border": "#D1D5DB",
    },
    "Navy & Cool Gray": {
        "primary": "#0F172A",
        "accent": "#334155",
        "body": "#1E293B",
        "muted": "#64748B",
        "soft": "#F8FAFC",
        "paper": "#FFFFFF",
        "border": "#CBD5E1",
    },
    "Charcoal & Slate": {
        "primary": "#2B2D42",
        "accent": "#8D99AE",
        "body": "#2B2D42",
        "muted": "#8D99AE",
        "soft": "#EDF2F4",
        "paper": "#FFFFFF",
        "border": "#8D99AE",
    },
    "Emerald & Mint": {
        "primary": "#064E3B",
        "accent": "#0D9488",
        "body": "#134E4A",
        "muted": "#059669",
        "soft": "#ECFDF5",
        "paper": "#FFFFFF",
        "border": "#A7F3D0",
    },
    "Burgundy & Cream": {
        "primary": "#581845",
        "accent": "#900C3F",
        "body": "#3A1B28",
        "muted": "#900C3F",
        "soft": "#FAF3E0",
        "paper": "#FAF3E0",
        "border": "#C70039",
    },
    "Midnight & Royal Blue": {
        "primary": "#0A192F",
        "accent": "#1E3A8A",
        "body": "#172554",
        "muted": "#2563EB",
        "soft": "#F0F9FF",
        "paper": "#FFFFFF",
        "border": "#93C5FD",
    },
    "Deep Forest Green": {
        "primary": "#1B4332",
        "accent": "#2D6A4F",
        "body": "#1F382B",
        "muted": "#40916C",
        "soft": "#D8F3DC",
        "paper": "#FFFFFF",
        "border": "#74C69D",
    },
    "Teal & Seafoam": {
        "primary": "#134E4A",
        "accent": "#14B8A6",
        "body": "#134E4A",
        "muted": "#0F766E",
        "soft": "#F0FDFA",
        "paper": "#FFFFFF",
        "border": "#99F6E4",
    },
    "Espresso & Sand": {
        "primary": "#3E2723",
        "accent": "#795548",
        "body": "#2E211E",
        "muted": "#6D4C41",
        "soft": "#F5F2EB",
        "paper": "#FAF8F5",
        "border": "#D7CCC8",
    },
    "Sapphire & Amber": {
        "primary": "#1E3A8A",
        "accent": "#D97706",
        "body": "#1E293B",
        "muted": "#3B82F6",
        "soft": "#FFFBEB",
        "paper": "#FFFFFF",
        "border": "#FDE68A",
    },
    "Steel & Ice Gray": {
        "primary": "#374151",
        "accent": "#6B7280",
        "body": "#1F2937",
        "muted": "#6B7280",
        "soft": "#F3F4F6",
        "paper": "#FFFFFF",
        "border": "#E5E7EB",
    },
    "Crimson & Rose": {
        "primary": "#881337",
        "accent": "#E11D48",
        "body": "#4C0519",
        "muted": "#9F1239",
        "soft": "#FFF1F2",
        "paper": "#FFFFFF",
        "border": "#FECDD3",
    },
    "Modern Olive & Khaki": {
        "primary": "#3F4E4F",
        "accent": "#A27B5C",
        "body": "#2C3531",
        "muted": "#5C6B65",
        "soft": "#DCD7C9",
        "paper": "#F8F7F4",
        "border": "#DCD7C9",
    },
    "Amethyst & Lilac": {
        "primary": "#3B185F",
        "accent": "#9333EA",
        "body": "#2E1065",
        "muted": "#7E22CE",
        "soft": "#FAF5FF",
        "paper": "#FFFFFF",
        "border": "#E9D5FF",
    },
    "Cobalt & Silver": {
        "primary": "#1D4ED8",
        "accent": "#64748B",
        "body": "#1E293B",
        "muted": "#3B82F6",
        "soft": "#F8FAFC",
        "paper": "#FFFFFF",
        "border": "#CBD5E1",
    },
}

WINDOWS_FONT_DIRECTORY = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
EMBEDDED_FONT_FILES = {
    "Arial": {"": "arial.ttf", "B": "arialbd.ttf", "I": "ariali.ttf", "BI": "arialbi.ttf"},
    "Calibri": {"": "calibri.ttf", "B": "calibrib.ttf", "I": "calibrii.ttf", "BI": "calibriz.ttf"},
    "SegoeUI": {"": "segoeui.ttf", "B": "segoeuib.ttf", "I": "segoeuii.ttf", "BI": "segoeuiz.ttf"},
    "Georgia": {"": "georgia.ttf", "B": "georgiab.ttf", "I": "georgiai.ttf", "BI": "georgiaz.ttf"},
    "Verdana": {"": "verdana.ttf", "B": "verdanab.ttf", "I": "verdanai.ttf", "BI": "verdanaz.ttf"},
    "Consolas": {"": "consola.ttf", "B": "consolab.ttf", "I": "consolai.ttf", "BI": "consolaz.ttf"},
    "Trebuchet": {"": "trebuc.ttf", "B": "trebucbd.ttf", "I": "trebucit.ttf", "BI": "trebucbi.ttf"},
    "TimesNewRoman": {"": "times.ttf", "B": "timesbd.ttf", "I": "timesi.ttf", "BI": "timesbi.ttf"},
}
BUILTIN_PDF_FONTS = {"Helvetica", "Times", "Courier"}


def _register_pdf_font(pdf, family):
    if family in BUILTIN_PDF_FONTS:
        return family
    files = EMBEDDED_FONT_FILES.get(family)
    if not files:
        return "Helvetica"
    paths = {style: WINDOWS_FONT_DIRECTORY / filename for style, filename in files.items()}
    if not all(path.is_file() for path in paths.values()):
        return "Helvetica"
    for style, path in paths.items():
        pdf.add_font(family=family, style=style, fname=str(path))
    return family


PALETTE_ALIASES = {
    "Navy and White": "Navy & Cool Gray",
    "Classic Black and White": "Classic Black & White",
    "Dark Green and White": "Deep Forest Green",
    "Mauve and Plum Velvet": "Mauve & Plum Velvet",
}


def get_pdf_palette(color_scheme):
    resolved = PALETTE_ALIASES.get(color_scheme, color_scheme)
    hex_palette = PDF_PALETTES_HEX.get(resolved, PDF_PALETTES_HEX["Classic Black & White"])
    return {name: _hex_to_rgb(color) for name, color in hex_palette.items()}



class CleanResume(FPDF):
    resume_font_family = "Helvetica"

    def set_font(self, family="", style="", size=0):
        # Apply the selected family consistently across every template.
        selected_family = getattr(self, "resume_font_family", "Helvetica")
        if family in {"", "Helvetica", "Times", "Courier"}:
            family = selected_family
        super().set_font(family, style, size)

    def section_header(self, title, style):
        x = self.l_margin
        y = self.get_y()
        width = self.w - self.l_margin - self.r_margin
        self.set_font("Helvetica", "B", 10 if style != "professional" else 11)
        self.set_text_color(*self.heading_color)

        if style in ("modern", "tech"):
            self.set_fill_color(*self.soft_color)
            self.rect(x, y, width, 7, style="F")
            self.set_fill_color(*self.accent_color)
            self.rect(x, y, 2.5 if style == "tech" else 1.5, 7, style="F")
            self.set_xy(x + 5, y + 1)
            self.cell(width - 7, 5, title.upper())
            self.set_y(y + 10)
        elif style in ("clean", "minimalist"):
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.25 if style == "minimalist" else 0.5)
            self.line(x, self.get_y(), x + (28 if style == "minimalist" else 18), self.get_y())
            self.ln(3 if style == "minimalist" else 4)
        elif style == "executive":
            self.set_font("Times", "B", 11)
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.55)
            self.line(x, self.get_y(), x + width, self.get_y())
            self.ln(3)
        elif style == "elegant":
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.25)
            self.line(x, self.get_y(), x + width, self.get_y())
            self.ln(3)
        elif style == "compact":
            self.set_font("Helvetica", "B", 9)
            self.cell(0, 5, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.25)
            self.line(x, self.get_y(), x + width, self.get_y())
            self.ln(1.5)
        else:
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.3)
            self.line(x, self.get_y(), x + width, self.get_y())
            self.ln(2)


def build_pdf(data, template=None, color_scheme=None, font_family="Helvetica"):
    pdf = CleanResume(orientation="P", unit="mm", format="A4")
    pdf.resume_font_family = _register_pdf_font(pdf, font_family)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    layouts = {
        "Professional Layout": {
            "header": "centered", "section_style": "professional",
            "section_order": ("summary", "experience", "projects", "education", "skills", "certifications"),
        },
        "Modern Layout": {
            "header": "banner", "section_style": "modern",
            "section_order": ("summary", "skills", "experience", "projects", "education", "certifications"),
        },
        "Clean Layout": {
            "header": "minimal", "section_style": "clean",
            "section_order": ("skills", "summary", "education", "experience", "projects", "certifications"),
        },
        "Executive Layout": {
            "header": "executive", "section_style": "executive",
            "section_order": ("summary", "experience", "projects", "education", "skills", "certifications"),
        },
        "Tech / Developer Layout": {
            "header": "tech", "section_style": "tech",
            "section_order": ("skills", "summary", "experience", "projects", "education", "certifications"),
        },
        "Minimalist Layout": {
            "header": "minimalist", "section_style": "minimalist",
            "section_order": ("summary", "experience", "projects", "education", "skills", "certifications"),
        },
        "Two-Column Sidebar Layout": {
            "header": "sidebar", "section_style": "clean",
            "section_order": ("summary", "experience", "projects", "education", "certifications"),
        },
        "Creative / Bold Header Layout": {
            "header": "creative", "section_style": "modern",
            "section_order": ("summary", "skills", "experience", "projects", "education", "certifications"),
        },
        "Compact / Single-Page Layout": {
            "header": "compact", "section_style": "compact",
            "section_order": ("summary", "experience", "projects", "education", "skills", "certifications"),
        },
        "Elegant / Corporate Layout": {
            "header": "elegant", "section_style": "elegant",
            "section_order": ("summary", "experience", "education", "projects", "skills", "certifications"),
        },
        "Academic / Research Layout": {
            "header": "executive", "section_style": "executive",
            "section_order": ("education", "summary", "projects", "experience", "skills", "certifications"),
        },
        "ATS Classic Single Column": {
            "header": "minimal", "section_style": "clean",
            "section_order": ("summary", "experience", "skills", "education", "projects", "certifications"),
        },
        "Data / Analytics Layout": {
            "header": "elegant", "section_style": "elegant",
            "section_order": ("summary", "skills", "projects", "experience", "education", "certifications"),
        },
    }
    template_aliases = {"Professional": "Professional Layout", "Modern": "Modern Layout", "Clean": "Clean Layout"}
    layout = layouts.get(template_aliases.get(template, template), layouts["Professional Layout"])
    palette = get_pdf_palette(color_scheme)
    pdf.heading_color = palette["primary"]
    pdf.accent_color = palette["accent"]
    pdf.body_color = palette["body"]
    pdf.muted_color = palette["muted"]
    pdf.soft_color = palette["soft"]

    content_x = pdf.l_margin
    content_width = pdf.w - pdf.l_margin - pdf.r_margin
    name = data.get("name") or "Candidate Name"
    email_phone = "  |  ".join(
        value for value in (data.get("email", ""), data.get("phone", "")) if value
    )
    headline = data.get("headline", "")
    additional_contact_items = [
        value for value in (data.get("location", ""), data.get("linkedin", ""), data.get("portfolio", ""), data.get("website", ""), data.get("github", "")) if value
    ]
    pdf.set_font("Helvetica", "", 9)
    additional_contact_lines = []
    current_contact_line = ""
    max_contact_width = content_width - (14 if layout["header"] == "banner" else 0)
    for contact_item in additional_contact_items:
        candidate = f"{current_contact_line}  |  {contact_item}" if current_contact_line else contact_item
        if current_contact_line and pdf.get_string_width(candidate) > max_contact_width:
            additional_contact_lines.append(current_contact_line)
            current_contact_line = contact_item
        else:
            current_contact_line = candidate
    if current_contact_line:
        additional_contact_lines.append(current_contact_line)

    if layout["header"] == "sidebar":
        sidebar_width = 43
        pdf.set_fill_color(*palette["primary"])
        pdf.rect(content_x, 10, sidebar_width, 277, style="F")
        pdf.set_xy(content_x + 5, 18)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.multi_cell(sidebar_width - 10, 6, name)
        pdf.set_font("Helvetica", "", 7.5)
        sidebar_contact = [data.get(key, "") for key in ("email", "phone", "location", "linkedin", "portfolio", "website", "github") if data.get(key)]
        if sidebar_contact:
            pdf.ln(3)
            pdf.multi_cell(sidebar_width - 10, 4, "\n".join(sidebar_contact))
        if data.get("skills"):
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(sidebar_width - 10, 5, "SKILLS", ln=True)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.multi_cell(sidebar_width - 10, 4, data["skills"])
        content_x += sidebar_width + 8
        content_width = pdf.w - content_x - pdf.r_margin
        pdf.set_xy(content_x, 18)
        pdf.set_font("Helvetica", "B", 19)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 9, name, ln=True)
        if headline:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*palette["muted"])
            pdf.cell(content_width, 5, headline, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, email_phone, ln=True)
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.5)
        pdf.line(content_x, pdf.get_y() + 2, content_x + content_width, pdf.get_y() + 2)
        pdf.set_y(pdf.get_y() + 9)
    elif layout["header"] == "banner":
        banner_y = pdf.get_y()
        banner_height = max(34, 29 + 5 * len(additional_contact_lines))
        pdf.set_fill_color(*palette["primary"])
        pdf.rect(content_x, banner_y, content_width, banner_height, style="F")
        pdf.set_xy(content_x + 7, banner_y + 6)
        pdf.set_font("Helvetica", "B", 21)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(content_width - 14, 10, name, ln=True)
        pdf.set_x(content_x + 7)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(content_width - 14, 5, email_phone, ln=True)
        for contact_line in additional_contact_lines:
            pdf.set_x(content_x + 7)
            pdf.cell(content_width - 14, 5, contact_line, ln=True)
        pdf.set_y(banner_y + banner_height + 7)
    elif layout["header"] == "creative":
        banner_y = pdf.get_y()
        banner_height = max(37, 31 + 5 * len(additional_contact_lines))
        pdf.set_fill_color(*palette["accent"])
        pdf.rect(content_x, banner_y, content_width, banner_height, style="F")
        pdf.set_xy(content_x + 8, banner_y + 7)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(content_width - 16, 10, name, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(content_width - 16, 5, email_phone, ln=True)
        for contact_line in additional_contact_lines:
            pdf.set_x(content_x + 8)
            pdf.cell(content_width - 16, 5, contact_line, ln=True)
        pdf.set_y(banner_y + banner_height + 8)
    elif layout["header"] in ("minimal", "minimalist"):
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 9, name, ln=True)
        if headline:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*palette["muted"])
            pdf.cell(content_width, 5, headline, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, email_phone, ln=True)
        if additional_contact_lines:
            pdf.multi_cell(content_width, 5, "\n".join(additional_contact_lines), align="L")
        rule_y = pdf.get_y() + 2
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.25 if layout["header"] == "minimalist" else 0.8)
        pdf.line(content_x, rule_y, content_x + 28, rule_y)
        pdf.set_y(rule_y + 7)
    elif layout["header"] == "executive":
        pdf.set_font("Times", "B", 21)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 10, name, ln=True, align="C")
        pdf.set_font("Times", "", 9)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, email_phone, ln=True, align="C")
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.8)
        pdf.line(content_x, pdf.get_y() + 3, content_x + content_width, pdf.get_y() + 3)
        pdf.set_y(pdf.get_y() + 10)
    elif layout["header"] == "compact":
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 7, name, ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 4, " | ".join([email_phone, *additional_contact_lines]), ln=True)
        pdf.set_y(pdf.get_y() + 4)
    elif layout["header"] == "tech":
        pdf.set_font("Courier", "B", 17)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 8, name, ln=True)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, " | ".join([email_phone, *additional_contact_lines]), ln=True)
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.5)
        pdf.line(content_x, pdf.get_y() + 2, content_x + content_width, pdf.get_y() + 2)
        pdf.set_y(pdf.get_y() + 9)
    else:
        pdf.set_font("Helvetica", "B", 19)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 9, name, ln=True, align="C")
        if headline:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*palette["muted"])
            pdf.cell(content_width, 5, headline, ln=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, email_phone, ln=True, align="C")
        if additional_contact_lines:
            pdf.multi_cell(content_width, 5, "\n".join(additional_contact_lines), align="C")
        rule_y = pdf.get_y() + 2
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.4)
        pdf.line(content_x, rule_y, content_x + content_width, rule_y)
        pdf.set_y(rule_y + 7)

    def write_section(title, text):
        if text and text.strip():
            pdf.section_header(title, layout["section_style"])
            pdf.set_font("Helvetica", "", 8 if layout["header"] == "compact" else 9)
            pdf.set_text_color(*pdf.body_color)
            pdf.multi_cell(0, 3.5 if layout["header"] == "compact" else 4.5, text.strip())
            pdf.ln(1.5 if layout["header"] == "compact" else 3)

    section_titles = {
        "summary": "Professional Summary",
        "skills": "Technical & Core Skills",
        "experience": "Work Experience",
        "projects": "Key Projects",
        "education": "Education",
        "certifications": "Certifications",
        "languages": "Languages",
        "awards": "Awards & Honors",
        "achievements": "Selected Achievements",
        "volunteer": "Volunteer Experience",
        "extracurricular": "Extracurricular Activities",
        "publications": "Publications",
        "interests": "Interests",
    }
    optional_sections = ("languages", "awards", "achievements", "volunteer", "extracurricular", "publications", "interests")
    for section in (*layout["section_order"], *optional_sections):
        write_section(section_titles[section], data.get(section))

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer


def generate_resume_pdf(
    data: dict,
    template: str = "Professional Layout",
    color_scheme: str = "Classic Black and White",
    font_family: str = "Helvetica",
) -> bytes:
    """Convert the existing builder payload to the clean text layout."""
    flat_data = dict(data)
    flat_data["skills"] = ", ".join(data.get("skills", []))
    flat_data["experience"] = "\n\n".join(
        " | ".join(value for value in (
            " at ".join(value for value in (item.get("role", ""), item.get("company", "")) if value),
            item.get("employment_type", ""), item.get("location", ""), item.get("duration", "")
        ) if value) + "\n" + item.get("description", "")
        for item in data.get("experience", []) if any(item.values())
    )
    flat_data["projects"] = "\n\n".join(
        " | ".join(value for value in (item.get("title", ""), item.get("dates", ""), item.get("url", "")) if value)
        + (f"\nTools: {item.get('tech')}" if item.get("tech") else "")
        + (f"\n{item.get('description')}" if item.get("description") else "")
        for item in data.get("projects", []) if any(item.values())
    )
    flat_data["education"] = "\n".join(
        " | ".join(value for value in (
            " ".join(part for part in (item.get("degree", ""), item.get("field", "")) if part),
            item.get("institute", ""), item.get("location", ""), item.get("year", ""), item.get("score", "")
        ) if value) + (f"\n{item.get('description')}" if item.get("description") else "")
        for item in data.get("education", []) if any(item.values())
    )
    flat_data["certifications"] = "\n".join(data.get("certifications", []))
    for section in ("languages", "awards", "achievements", "volunteer", "extracurricular", "publications", "interests"):
        value = data.get(section, [])
        flat_data[section] = "\n".join(value) if isinstance(value, list) else str(value or "")
    return build_pdf(flat_data, template=template, color_scheme=color_scheme, font_family=font_family).getvalue()


def render_pdf_to_thumbnail(pdf_bytes: bytes, dpi: int = 120) -> bytes:
    """Convert the first page of a generated PDF into a PNG thumbnail."""
    if not pdf_bytes:
        return b""

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if len(doc) == 0:
            return b""
        return doc[0].get_pixmap(dpi=dpi).tobytes("png")
    finally:
        doc.close()
