CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background: linear-gradient(180deg, #f7f9fc 0%, #eef2f7 100%);
}

/* Hero header */
.hero-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    padding: 2rem 2.2rem;
    border-radius: 18px;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);
}
.hero-header h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.9rem;
    margin: 0 0 0.3rem 0;
}
.hero-header p {
    opacity: 0.92;
    margin: 0;
    font-size: 1rem;
}

/* Cards */
.custom-card {
    background: white;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #eef0f4;
    margin-bottom: 1.1rem;
}

.section-heading {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 1.02rem;
    color: #1f2937;
    margin-bottom: 0.7rem;
}

/* Badges / pills */
.badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 0.2rem 0.35rem 0.2rem 0;
}
.badge-skill { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }
.badge-found { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.badge-missing { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.empty-hint { color: #9ca3af; font-size: 0.9rem; }

/* Suggestion items */
.suggestion-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 0.7rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.55rem;
    font-size: 0.92rem;
    color: #374151;
}

/* Buttons */
.stButton>button, .stDownloadButton>button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: white;
    border-radius: 14px;
    padding: 1rem;
    border: 1.5px dashed #c7d2fe;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

/* Metric tweaks */
[data-testid="stMetricValue"] {
    font-family: 'Poppins', sans-serif;
}
</style>
"""