from fpdf import FPDF
import io


class ConfigurableResumePDF(FPDF):
    """PDF canvas with configurable typography, accent color, and spacing."""

    SUPPORTED_FONTS = {"Helvetica", "Times", "Courier"}

    def __init__(self, font_family="Helvetica", primary_hex="#2563EB", spacing=4.0):
        if font_family not in self.SUPPORTED_FONTS:
            raise ValueError(
                f"Unsupported font '{font_family}'. Choose one of: "
                f"{', '.join(sorted(self.SUPPORTED_FONTS))}."
            )

        super().__init__(orientation="P", unit="mm", format="A4")
        self.font_family_name = font_family
        self.primary_hex = primary_hex
        self.spacing = max(0.0, float(spacing))
        self.primary_rgb = self.hex_to_rgb(primary_hex)

    @staticmethod
    def hex_to_rgb(hex_str):
        value = hex_str.lstrip("#")
        if len(value) != 6:
            raise ValueError("Accent color must be a 6-digit hex value.")
        try:
            return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
        except ValueError as exc:
            raise ValueError("Accent color must be a valid hex value.") from exc

    def section_header(self, title):
        self.set_font(self.font_family_name, "B", 11)
        self.set_text_color(*self.primary_rgb)
        self.cell(0, 6, title.upper(), ln=True)
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.3)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(self.spacing / 2)


def generate_custom_pdf(
    data,
    font_choice="Helvetica",
    color_hex="#2563EB",
    template="Classic Single Column",
    spacing=4.0,
):
    """Render a resume using the selected font, accent color, and template."""
    del template
    pdf = ConfigurableResumePDF(
        font_family=font_choice,
        primary_hex=color_hex,
        spacing=spacing,
    )
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font(font_choice, "B", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, data.get("name", "Candidate Name"), ln=True, align="C")

    pdf.set_font(font_choice, "", 9)
    pdf.set_text_color(100, 116, 139)
    contact = f"{data.get('email', '')}  |  {data.get('phone', '')}  |  {data.get('linkedin', '')}"
    pdf.cell(0, 5, contact, ln=True, align="C")
    pdf.ln(4)

    def write_section(title, text):
        if text and text.strip():
            pdf.section_header(title)
            pdf.set_font(font_choice, "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 4.5, text.strip())
            pdf.ln(3)

    write_section("Professional Summary", data.get("summary"))
    write_section("Core Skills", data.get("skills"))
    write_section("Work Experience", data.get("experience"))
    write_section("Key Projects", data.get("projects"))
    write_section("Education", data.get("education"))
    write_section("Certifications", data.get("certifications"))

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer


def build_pdf(data):
    """Backward-compatible default PDF builder used by the Streamlit app."""
    return generate_custom_pdf(data)


def generate_resume_pdf(data: dict) -> bytes:
    """Convert the structured builder payload to the configurable text layout."""
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
    return build_pdf(flat_data).getvalue()
