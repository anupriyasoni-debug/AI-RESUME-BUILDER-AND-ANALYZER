from fpdf import FPDF
import io


def _hex_to_rgb(color):
    value = color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


PDF_PALETTES_HEX = {
    "Navy and White": {
        "primary": "#11304D", "accent": "#2D6791",
        "body": "#334155", "muted": "#5B7084", "soft": "#EBF2F8",
    },
    "Charcoal and Slate": {
        "primary": "#2B2D31", "accent": "#495563",
        "body": "#343A40", "muted": "#606B75", "soft": "#F0F2F4",
    },
    "Dark Green and White": {
        "primary": "#155337", "accent": "#357A55",
        "body": "#314136", "muted": "#5C7764", "soft": "#EBF4ED",
    },
    "Burgundy and Cream": {
        "primary": "#802637", "accent": "#9E4C50",
        "body": "#483834", "muted": "#7E645B", "soft": "#F8F1E2",
    },
    "Classic Black and White": {
        "primary": "#000000", "accent": "#1F1F1F",
        "body": "#222222", "muted": "#595959", "soft": "#F2F2F2",
    },
}


def get_pdf_palette(color_scheme):
    hex_palette = PDF_PALETTES_HEX.get(color_scheme, PDF_PALETTES_HEX["Classic Black and White"])
    return {name: _hex_to_rgb(color) for name, color in hex_palette.items()}


class CleanResume(FPDF):
    def section_header(self, title, style):
        x = self.l_margin
        y = self.get_y()
        width = self.w - self.l_margin - self.r_margin
        self.set_font("Helvetica", "B", 10 if style != "professional" else 11)
        self.set_text_color(*self.heading_color)

        if style == "modern":
            self.set_fill_color(*self.soft_color)
            self.rect(x, y, width, 7, style="F")
            self.set_fill_color(*self.accent_color)
            self.rect(x, y, 1.5, 7, style="F")
            self.set_xy(x + 5, y + 1)
            self.cell(width - 7, 5, title.upper())
            self.set_y(y + 10)
        elif style == "clean":
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.5)
            self.line(x, self.get_y(), x + 18, self.get_y())
            self.ln(4)
        else:
            self.cell(0, 6, title.upper(), ln=True)
            self.set_draw_color(*self.accent_color)
            self.set_line_width(0.3)
            self.line(x, self.get_y(), x + width, self.get_y())
            self.ln(2)


def build_pdf(data, template=None, color_scheme=None):
    pdf = CleanResume(orientation="P", unit="mm", format="A4")
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
    additional_contact_items = [
        value for value in (data.get("linkedin", ""), data.get("github", ""), data.get("location", "")) if value
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

    if layout["header"] == "banner":
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
    elif layout["header"] == "minimal":
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 9, name, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*palette["muted"])
        pdf.cell(content_width, 5, email_phone, ln=True)
        if additional_contact_lines:
            pdf.multi_cell(content_width, 5, "\n".join(additional_contact_lines), align="L")
        rule_y = pdf.get_y() + 2
        pdf.set_draw_color(*palette["accent"])
        pdf.set_line_width(0.8)
        pdf.line(content_x, rule_y, content_x + 28, rule_y)
        pdf.set_y(rule_y + 7)
    else:
        pdf.set_font("Helvetica", "B", 19)
        pdf.set_text_color(*palette["primary"])
        pdf.cell(content_width, 9, name, ln=True, align="C")
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
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*pdf.body_color)
            pdf.multi_cell(0, 4.5, text.strip())
            pdf.ln(3)

    section_titles = {
        "summary": "Professional Summary",
        "skills": "Technical & Core Skills",
        "experience": "Work Experience",
        "projects": "Key Projects",
        "education": "Education",
        "certifications": "Certifications",
    }
    for section in layout["section_order"]:
        write_section(section_titles[section], data.get(section))

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer


def generate_resume_pdf(
    data: dict,
    template: str = "Professional Layout",
    color_scheme: str = "Classic Black and White",
) -> bytes:
    """Convert the existing builder payload to the clean text layout."""
    flat_data = dict(data)
    flat_data["skills"] = ", ".join(data.get("skills", []))
    flat_data["experience"] = "\n\n".join(
        f"{item.get('role', '')} - {item.get('company', '')} ({item.get('duration', '')})\n{item.get('description', '')}"
        for item in data.get("experience", []) if any(item.values())
    )
    flat_data["projects"] = "\n\n".join(
        f"{item.get('title', '')} ({item.get('tech', '')})\n{item.get('description', '')}"
        for item in data.get("projects", []) if any(item.values())
    )
    flat_data["education"] = "\n".join(
        f"{item.get('degree', '')} - {item.get('institute', '')} ({item.get('year', '')})"
        for item in data.get("education", []) if any(item.values())
    )
    flat_data["certifications"] = "\n".join(data.get("certifications", []))
    return build_pdf(flat_data, template=template, color_scheme=color_scheme).getvalue()