from fpdf import FPDF


class ResumePDF(FPDF):
    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, title.upper(), ln=True)
        self.set_draw_color(50, 50, 50)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(3)

    def body_text(self, text, size=10):
        self.set_font("Helvetica", "", size)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(1)


def generate_resume_pdf(data: dict) -> bytes:
    pdf = ResumePDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, data.get("name", "Your Name"), ln=True)

    contact_bits = [data.get("email", ""), data.get("phone", ""),
                     data.get("location", ""), data.get("linkedin", "")]
    contact_line = " | ".join([c for c in contact_bits if c])
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, contact_line, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    if data.get("summary"):
        pdf.section_title("Professional Summary")
        pdf.body_text(data["summary"])

    if data.get("skills"):
        pdf.section_title("Skills")
        pdf.body_text(", ".join(data["skills"]))

    if data.get("experience"):
        entries = [e for e in data["experience"] if any(e.values())]
        if entries:
            pdf.section_title("Work Experience")
            for exp in entries:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6, f'{exp.get("role", "")} - {exp.get("company", "")}', ln=True)
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, exp.get("duration", ""), ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.body_text(exp.get("description", ""))

    if data.get("projects"):
        entries = [p for p in data["projects"] if any(p.values())]
        if entries:
            pdf.section_title("Projects")
            for proj in entries:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6, proj.get("title", ""), ln=True)
                if proj.get("tech"):
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 5, f'Tech: {proj["tech"]}', ln=True)
                    pdf.set_text_color(0, 0, 0)
                pdf.body_text(proj.get("description", ""))

    if data.get("education"):
        entries = [e for e in data["education"] if any(e.values())]
        if entries:
            pdf.section_title("Education")
            for edu in entries:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6, f'{edu.get("degree", "")} - {edu.get("institute", "")}', ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(100, 100, 100)
                line = edu.get("year", "")
                if edu.get("score"):
                    line += f'  |  Score: {edu["score"]}'
                pdf.cell(0, 5, line, ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)

    if data.get("certifications"):
        pdf.section_title("Certifications")
        for cert in data["certifications"]:
            pdf.body_text(f"- {cert}", size=10)

    return bytes(pdf.output())