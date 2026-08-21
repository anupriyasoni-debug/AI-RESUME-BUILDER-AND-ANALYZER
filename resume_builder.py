import streamlit as st


def resume_builder_page():
    st.markdown("<div class='section-heading'>📝 Build Your Resume</div>", unsafe_allow_html=True)

    data = {}
    container = st.container(border=True)
    tabs = container.tabs(["👤 Personal", "🎓 Education", "💼 Experience", "🚀 Projects", "🛠️ Skills", "📜 Certifications"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            data["name"] = st.text_input("Full Name")
            data["email"] = st.text_input("Email")
            data["phone"] = st.text_input("Phone")
        with col2:
            data["linkedin"] = st.text_input("LinkedIn URL")
            data["location"] = st.text_input("Location (City, Country)")
        data["summary"] = st.text_area(
            "Professional Summary", height=100,
            placeholder="A short 2-3 line pitch about who you are and what you're looking for."
        )

    with tabs[1]:
        num_edu = st.number_input("Number of education entries", min_value=0, max_value=5, value=1, key="num_edu")
        education = []
        for i in range(int(num_edu)):
            st.markdown(f"**Education #{i + 1}**")
            c1, c2 = st.columns(2)
            with c1:
                degree = st.text_input("Degree / Course", key=f"edu_degree_{i}")
                year = st.text_input("Year", key=f"edu_year_{i}")
            with c2:
                institute = st.text_input("Institute / University", key=f"edu_institute_{i}")
                score = st.text_input("Score / CGPA (optional)", key=f"edu_score_{i}")
            education.append({"degree": degree, "institute": institute, "year": year, "score": score})
            if i < int(num_edu) - 1:
                st.divider()
        data["education"] = education

    with tabs[2]:
        num_exp = st.number_input("Number of experience entries", min_value=0, max_value=5, value=1, key="num_exp")
        experience = []
        for i in range(int(num_exp)):
            st.markdown(f"**Experience #{i + 1}**")
            c1, c2 = st.columns(2)
            with c1:
                role = st.text_input("Job Title", key=f"exp_role_{i}")
            with c2:
                company = st.text_input("Company", key=f"exp_company_{i}")
            duration = st.text_input("Duration (e.g. Jan 2023 - Present)", key=f"exp_duration_{i}")
            description = st.text_area("Description (one point per line)", key=f"exp_desc_{i}", height=80)
            experience.append({"role": role, "company": company, "duration": duration, "description": description})
            if i < int(num_exp) - 1:
                st.divider()
        data["experience"] = experience

    with tabs[3]:
        num_proj = st.number_input("Number of projects", min_value=0, max_value=5, value=1, key="num_proj")
        projects = []
        for i in range(int(num_proj)):
            st.markdown(f"**Project #{i + 1}**")
            title = st.text_input("Project Title", key=f"proj_title_{i}")
            tech = st.text_input("Tech Stack Used", key=f"proj_tech_{i}")
            description = st.text_area("Description", key=f"proj_desc_{i}", height=80)
            projects.append({"title": title, "tech": tech, "description": description})
            if i < int(num_proj) - 1:
                st.divider()
        data["projects"] = projects

    with tabs[4]:
        skills_text = st.text_area(
            "Enter skills separated by commas", height=100,
            placeholder="Python, SQL, Machine Learning, React, Git"
        )
        data["skills"] = [s.strip() for s in skills_text.split(",") if s.strip()]
        if data["skills"]:
            badges = "".join(f"<span class='badge badge-skill'>{s}</span>" for s in data["skills"])
            st.markdown(f"<div style='margin-top:0.5rem;'>{badges}</div>", unsafe_allow_html=True)

    with tabs[5]:
        cert_text = st.text_area("Enter certifications, one per line", height=100)
        data["certifications"] = [c.strip() for c in cert_text.split("\n") if c.strip()]

    _render_progress(data)

    return data


def _render_progress(data):
    checks = [
        bool(data.get("name")),
        bool(data.get("email")),
        bool(data.get("summary")),
        any(any(e.values()) for e in data.get("education", [])),
        any(any(e.values()) for e in data.get("experience", [])),
        any(any(p.values()) for p in data.get("projects", [])),
        bool(data.get("skills")),
    ]
    completion = int(sum(checks) / len(checks) * 100)
    with st.container(border=True):
        st.markdown(f"<div class='section-heading'>Profile Completeness: {completion}%</div>", unsafe_allow_html=True)
        st.progress(completion / 100)