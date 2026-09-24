from fpdf import FPDF
import io


class CleanResume(FPDF):
    def section_header(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 41, 59)
        self.cell(0, 6, title.upper(), ln=True)
        self.set_draw_color(148, 163, 184)
        self.set_line_width(0.3)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(2)


def build_pdf(data):
    pdf = CleanResume(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, data.get("name", "Candidate Name"), ln=True, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    contact = f"{data.get('email', '')}  |  {data.get('phone', '')}  |  {data.get('linkedin', '')}"
    pdf.cell(0, 5, contact, ln=True, align="C")
    pdf.ln(5)

    def write_section(title, text):
        if text and text.strip():
            pdf.section_header(title)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 4.5, text.strip())
            pdf.ln(3)

    write_section("Professional Summary", data.get("summary"))
    write_section("Technical & Core Skills", data.get("skills"))
    write_section("Work Experience", data.get("experience"))
    write_section("Key Projects", data.get("projects"))
    write_section("Education", data.get("education"))
    write_section("Certifications", data.get("certifications"))

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer


def generate_resume_pdf(data: dict) -> bytes:
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
    return build_pdf(flat_data).getvalue()