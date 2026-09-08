CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --fs-h1: 1.85rem;
    --fs-h2: 1.05rem;
    --fs-h3: 0.98rem;
    --fs-body: 0.92rem;
    --fs-small: 0.8rem;
    --fs-label: 0.74rem;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background: linear-gradient(180deg, #f7f9fc 0%, #eef2f7 100%);
}

/* ---------- Hero header ---------- */
.hero-header {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #4338ca 0%, #7c3aed 45%, #c026a3 100%);
    padding: 2.1rem 2.3rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 1.6rem;
    box-shadow: 0 12px 32px rgba(76, 29, 149, 0.28);
}
.hero-header::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: 0.12;
    background-image: radial-gradient(circle, #ffffff 1px, transparent 1px);
    background-size: 16px 16px;
    pointer-events: none;
}
.hero-header::after {
    content: "";
    position: absolute;
    top: -40%; right: -10%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(255,255,255,0.16) 0%, transparent 70%);
    pointer-events: none;
}
.hero-header-inner { position: relative; z-index: 1; }
.hero-title-row { display: flex; align-items: center; }
.hero-header h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: var(--fs-h1);
    margin: 0;
    letter-spacing: -0.01em;
}
.hero-header p {
    color: rgba(255, 255, 255, 0.94);
    font-weight: 500;
    margin: 0.6rem 0 0 0;
    font-size: var(--fs-body);
    letter-spacing: 0.1px;
}

/* ---------- Icon badges ---------- */
.icon-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    flex-shrink: 0;
}
.icon-badge-hero {
    width: 46px; height: 46px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    margin-right: 0.85rem;
}
.icon-badge-section {
    width: 32px; height: 32px;
    margin-right: 0.6rem;
}
.icon-badge-sidebar {
    width: 32px; height: 32px;
    background: rgba(255, 255, 255, 0.1);
    color: #c4b5fd;
    margin-right: 0.65rem;
}
.icon-badge-feature {
    width: 44px; height: 44px;
    background: #f5f3ff;
    color: #7c3aed;
    margin: 0 auto 0.7rem auto;
}

/* ---------- Typography helpers ---------- */
.section-heading {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: var(--fs-h3);
    color: #1f2937;
    display: flex;
    align-items: center;
    margin-bottom: 0.75rem;
}
.eyebrow {
    font-size: var(--fs-label);
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #9ca3af;
}

/* ---------- Cards ---------- */
.custom-card {
    background: white;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #eef0f4;
    margin-bottom: 1.1rem;
}

/* ---------- Upload card ---------- */
.upload-card-label {
    font-size: var(--fs-h3);
    font-weight: 600;
    font-family: 'Poppins', sans-serif;
    color: #1f2937;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
}
[data-testid="stFileUploaderDropzone"] {
    background: #fafaff;
    border-radius: 14px;
    border: 1.5px dashed #c7d2fe;
}
div:has(> [data-testid="stFileUploader"]) {
    background: white;
    border-radius: 18px;
    padding: 1.5rem 1.6rem;
    border: 1px solid #e9e8f5;
    box-shadow: 0 6px 22px rgba(76, 29, 149, 0.07);
    margin-bottom: 1.2rem;
}

/* ---------- Feature grid (empty state) ---------- */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 0.5rem;
}
.feature-item {
    background: white;
    border: 1px solid #eef0f4;
    border-radius: 16px;
    padding: 1.3rem 1.1rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.feature-item h4 {
    font-family: 'Poppins', sans-serif;
    font-size: 0.92rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.35rem 0;
}
.feature-item p {
    font-size: var(--fs-small);
    color: #6b7280;
    margin: 0;
    line-height: 1.4;
}
@media (max-width: 700px) {
    .feature-grid { grid-template-columns: 1fr; }
}

/* ---------- Badges / pills ---------- */
.badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: var(--fs-small);
    font-weight: 500;
    margin: 0.2rem 0.35rem 0.2rem 0;
}
.badge-skill { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }
.badge-found { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.badge-missing { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.empty-hint { color: #9ca3af; font-size: var(--fs-body); }

/* ---------- Suggestion items ---------- */
.suggestion-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.55rem;
    font-size: var(--fs-body);
    color: #374151;
}
.suggestion-item .icon-badge { width: 24px; height: 24px; background: #fef3c7; color: #b45309; margin-right: 0.15rem; }

/* ---------- Buttons ---------- */
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

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: #111827;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
.sidebar-brand-row { display: flex; align-items: center; margin-bottom: 0.2rem; }
.sidebar-brand-row span.brand-text {
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 1.05rem;
    color: #f9fafb !important;
}

/* ---------- Metric tweaks ---------- */
[data-testid="stMetricValue"] {
    font-family: 'Poppins', sans-serif;
}
[data-testid="stMetricLabel"] {
    font-size: var(--fs-label) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6b7280 !important;
}
</style>
"""