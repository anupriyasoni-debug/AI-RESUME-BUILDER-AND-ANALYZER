import streamlit as st

from analyzer import JOB_TAXONOMY, extract_text, analyze_resume, generate_suggestions
from pdf_generator import build_pdf

st.set_page_config(page_title="Resumer - AI Resume Analyzer & Builder", layout="wide")


st.sidebar.title("📄 Resumer Studio")
app_mode = st.sidebar.radio("Navigate", ["Resume Analyzer", "Resume Builder"])

if app_mode == "Resume Analyzer":
    st.title("🎯 ATS Resume Analyzer")
    st.caption("Upload your resume, select a trending target role, and get real-time keyword alignment analysis.")

    col1, col2 = st.columns([1, 1])
    with col1:
        target_role = st.selectbox("Select Target Job Profile", list(JOB_TAXONOMY.keys()))
    with col2:
        uploaded_file = st.file_uploader("Upload Resume (.PDF or .DOCX)", type=["pdf", "docx"])

    if uploaded_file and target_role:
        with st.spinner("Extracting text and analyzing against ATS filters..."):
            text = extract_text(uploaded_file)

            if not text:
                st.error("Could not extract readable text. The document may be scanned or empty.")
            else:
                results = analyze_resume(text, target_role=target_role)
                suggestions = generate_suggestions(results, target_role)

                st.divider()

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Overall ATS Score", f"{results['total_score']} / 100")
                m2.metric("Role Keyword Fit", f"{results['role_score']} / 40")
                m3.metric("Completeness", f"{results['section_score']} / 30")
                m4.metric("Word Count", results["word_count"])

                st.progress(results["total_score"] / 100)

                st.subheader(f"🔍 Skill Alignment: {target_role}")
                s_col1, s_col2 = st.columns(2)

                with s_col1:
                    st.markdown("**✅ Matched Skills Detected:**")
                    if results["matched_skills"]:
                        st.write(", ".join([f"`{skill}`" for skill in results["matched_skills"]]))
                    else:
                        st.info("No target skills matched yet.")

                with s_col2:
                    st.markdown("**⚠️ Missing High-Value Skills:**")
                    if results["missing_skills"]:
                        st.write(", ".join([f"`{skill}`" for skill in results["missing_skills"]]))
                    else:
                        st.success("Great job! All core skills matched.")

                st.subheader("💡 Tailored ATS Recommendations")
                for tip in suggestions:
                    st.info(tip)

elif app_mode == "Resume Builder":
    st.title("🛠️ Resume Builder")
    st.caption("Fill out the fields to generate a clean, ATS-compliant PDF resume.")

    with st.form("resume_builder_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Full Name", placeholder="e.g. Mahak Sahu")
            email = st.text_input("Email", placeholder="e.g. name@example.com")
        with col_b:
            phone = st.text_input("Phone Number", placeholder="e.g. +91 9876543210")
            linkedin = st.text_input("LinkedIn Profile", placeholder="e.g. linkedin.com/in/username")

        summary = st.text_area("Professional Summary", placeholder="Brief 2-3 sentence career summary...")
        skills = st.text_area("Technical Skills", placeholder="e.g. Python, SQL, Git, PyTorch, Docker")
        experience = st.text_area("Work Experience", placeholder="Job Title - Company (Year)\n• Built...\n• Improved...")
        projects = st.text_area("Key Projects", placeholder="Project Name | Tech Stack\n• Developed...")
        education = st.text_area("Education", placeholder="B.Tech in Artificial Intelligence & Machine Learning\nMadhav Institute of Technology & Science (2025 - Present)")
        certifications = st.text_area("Certifications", placeholder="e.g. AWS Certified Cloud Practitioner")

        submitted = st.form_submit_button("Generate Resume PDF")

        if submitted:
            resume_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "linkedin": linkedin,
                "summary": summary,
                "skills": skills,
                "experience": experience,
                "projects": projects,
                "education": education,
                "certifications": certifications,
            }
            pdf_bytes = build_pdf(resume_data)
            st.success("Resume generated successfully!")
            st.download_button(
                label="📥 Download Resume PDF",
                data=pdf_bytes,
                file_name="ATS_Clean_Resume.pdf",
                mime="application/pdf",
            )
