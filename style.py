CUSTOM_CSS = """
<style>
:root {
    --fs-h1: 1.85rem;
    --fs-h2: 1.05rem;
    --fs-h3: 0.98rem;
    --fs-body: 0.92rem;
    --fs-small: 0.8rem;
    --fs-label: 0.74rem;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
    font-family: inherit;
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

GRADIENT_CSS = """
<style>
:root {
    --app-ink: #172033;
    --app-muted: #637083;
    --app-border: #e2e8f0;
    --app-accent: #3157a4;
    --app-surface: #ffffff;
}
.stApp { background: #f5f7fb !important; color: var(--app-ink) !important; }
.block-container { max-width: 1280px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
[data-testid="stSidebar"] * { color: #263247; }
[data-testid="stSidebar"] [role="radiogroup"] label { border-radius: 8px; padding: .35rem .5rem; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #f1f4fa; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #edf2ff; color: #244a91; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--app-border) !important; border-radius: 12px !important; background: var(--app-surface); }
[data-testid="stMetric"] { border: 1px solid var(--app-border); border-radius: 10px; padding: .9rem 1rem; background: #fff; }
[data-testid="stMetricLabel"] { color: var(--app-muted) !important; }
[data-testid="stMetricValue"] { color: var(--app-ink); }
.stButton > button, .stDownloadButton > button { border-radius: 8px; font-weight: 600; transition: border-color .15s ease, background .15s ease; }
.stButton > button[kind="primary"], .stDownloadButton > button { background: var(--app-accent); border-color: var(--app-accent); color: #fff; }
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover { background: #264887; border-color: #264887; }
.stButton > button[kind="secondary"] { background: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #244a91 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"] > div { background: #fff !important; color: #172033 !important; border-color: #cbd5e1 !important; }
[data-testid="stFileUploaderDropzone"] { color: #475569 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] [data-baseweb="select"] > div { border-radius: 8px; }
[data-testid="stFileUploaderDropzone"] { border: 1px dashed #b8c5d8; border-radius: 10px; background: #fff; }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
</style>
"""

LIGHT_POLISH_CSS = """
<style>
/* Consistent dashboard rhythm and aligned cards across Streamlit columns. */
.block-container > div { gap: 1.15rem; }
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
    gap: 1rem !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 0; }
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div { height: 100%; }
.hero {
    min-height: 260px;
    display: flex;
    align-items: center;
    margin-bottom: .3rem;
}
.hero h1 { max-width: 780px; line-height: 1.08 !important; text-wrap: balance; }
.hero p { line-height: 1.65; margin-bottom: 0; }
.compare-hero {
    padding: 1.35rem 1.5rem;
    border: 1px solid #d9ddf5;
    border-radius: 18px;
    background: radial-gradient(circle at 90% 15%, rgba(139,124,255,.16), transparent 18rem), linear-gradient(120deg,#27265d,#5141a8 68%,#167d75);
    color: #fff;
    margin: .6rem 0 1rem;
    box-shadow: 0 16px 38px rgba(49, 54, 110, .16);
}
.compare-hero .eyebrow { color: #dbeafe !important; }
.compare-hero h3 { margin: .4rem 0; color: #fff !important; line-height: 1.2; }
.compare-hero p { margin: .35rem 0 0; color: #e7eaff !important; line-height: 1.55; }
.preview-card, .capability, .how-step { height: 100%; box-sizing: border-box; }
.preview-card { display: flex; flex-direction: column; }
.preview-card .wireframe { flex: 1; }
.preview-card > p:last-child { margin-top: auto; padding-top: .45rem; }
.capability { display: flex; flex-direction: column; }
.capability p { flex: 1; line-height: 1.55; }
.how-step { display: flex; flex-direction: column; }
.how-step h4 { min-height: 2.6em; line-height: 1.3; }
[data-testid="stMetric"] {
    min-height: 108px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: .8rem .9rem;
    background: #fff;
}
[data-testid="stMetricLabel"] { line-height: 1.35; }
[data-testid="stMarkdownContainer"] p { line-height: 1.6; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stFileUploaderDropzone"] { min-height: 170px; }
.stButton > button, .stDownloadButton > button {
    min-height: 2.75rem;
    white-space: normal;
    line-height: 1.25;
}
@media (max-width: 900px) {
    .block-container { padding: 1.5rem 1rem 3rem !important; }
    .hero { padding: 1.7rem 1.35rem !important; }
}
@media (max-width: 700px) {
    .block-container { padding: 1.25rem .85rem 2.5rem !important; }
    [data-testid="stHorizontalBlock"] { gap: .7rem !important; }
    .hero { min-height: 0; padding: 1.5rem 1.15rem !important; }
    .hero h1 { font-size: clamp(1.9rem, 9vw, 3rem) !important; }
    .preview-card { min-height: 0; }
    .how-step h4 { min-height: 0; }
}
</style>
"""

DARK_THEME_CSS = """
<style>
:root {
    --ink: #f3f5fa !important;
    --muted: #9aa4b8 !important;
    --line: #252b3b !important;
    --accent: #8b7cff !important;
    --surface: #151923 !important;
    --canvas: #0a0b0e !important;
    --shadow-card: 0 18px 48px rgba(0, 0, 0, .28) !important;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.stApp {
    background:
        radial-gradient(circle at 82% -10%, rgba(108, 92, 231, .14), transparent 30rem),
        radial-gradient(circle at 0% 40%, rgba(57, 72, 140, .08), transparent 32rem),
        #0a0b0e !important;
    color: #f3f5fa !important;
}
.block-container {
    max-width: 1320px !important;
    padding: 2.5rem 3.2rem 4rem !important;
}

h1, h2, h3, h4, h5, h6, p, label, [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"] {
    color: #f3f5fa;
}
h1, h2, h3, h4, h5, h6 { letter-spacing: -.025em; }
[data-testid="stCaptionContainer"], .stMarkdown small { color: #9aa4b8 !important; }

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(18, 20, 26, .99), rgba(10, 11, 14, .99)) !important;
    border-right: 1px solid #272b36 !important;
    box-shadow: 16px 0 40px rgba(0, 0, 0, .18);
}
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.15rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="font-size:1.25rem"] {
    padding: .2rem .45rem .9rem;
    color: #f8fafc !important;
}
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: .45rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 2.65rem;
    padding: .68rem .8rem !important;
    border: 1px solid transparent;
    border-radius: 10px !important;
    background: transparent !important;
    color: #c2c8d5 !important;
    transition: background .18s ease, border-color .18s ease, color .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(139, 124, 255, .09) !important;
    border-color: #33304e !important;
    color: #f8fafc !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[aria-checked="true"]) {
    background: linear-gradient(100deg, #292c35, #22252d) !important;
    border-color: #383c47 !important;
    color: #ffffff !important;
    box-shadow: inset 3px 0 #8b7cff !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [role="radiogroup"] label span { color: inherit !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #f3f5fa !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div { color: #f8fafc !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="font-size:1.25rem"] { color: #f8fafc !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="font-size:1.25rem"] span { color: #a78bfa !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #aab3c4 !important; }
[data-testid="stSidebar"] label { color: #cbd5e1 !important; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="font-size:1.25rem"] { color: #f8fafc !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="font-size:1.25rem"] span { color: #a78bfa !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #aab3c4 !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[aria-checked="true"]) { color: #ffffff !important; }

.hero {
    border: 1px solid rgba(139, 124, 255, .3) !important;
    background:
        radial-gradient(circle at 82% 30%, rgba(139, 124, 255, .32), transparent 16rem),
        linear-gradient(120deg, #121521 0%, #1c1c38 55%, #302460 100%) !important;
    box-shadow: 0 24px 70px rgba(55, 42, 140, .24) !important;
}
.hero h1 { color: #ffffff !important; }
.hero p { color: #b8c0d0 !important; }
.eyebrow { color: #a99eff !important; }

.preview-card, .capability, .how-step, .font-preview, .custom-card,
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(20, 23, 32, .78) !important;
    border-color: #272b36 !important;
    box-shadow: var(--shadow-card) !important;
    backdrop-filter: blur(16px);
}
.preview-card:hover, .capability:hover, .how-step:hover {
    border-color: rgba(139, 124, 255, .55) !important;
    transform: translateY(-3px);
}
.preview-card.is-selected {
    background: linear-gradient(145deg, rgba(46, 42, 83, .8), rgba(20, 23, 32, .92)) !important;
    border-color: #8b7cff !important;
}
.preview-card h4, .capability h4, .preview-card strong { color: #f8fafc !important; }
.preview-card p, .capability p, .how-step p { color: #9aa4b8 !important; }
.wireframe { background: #0f1219 !important; border-color: #30374a !important; }
.wireframe-header { border-bottom-color: #30374a !important; }
.wireframe-person-name, .wireframe-detail { color: #c6ccda !important; }
.wireframe-label { color: #8792a8 !important; }
.wireframe-line, .wireframe-contact { background: #30374a !important; }
.wireframe.compact .wireframe-header { background: #181d29 !important; }
.quote-card {
    background: linear-gradient(90deg, rgba(55, 45, 105, .52), rgba(27, 35, 67, .5)) !important;
    color: #c8c2ff !important;
}

[data-testid="stMetric"] {
    background: rgba(20, 23, 32, .72) !important;
    border: 1px solid #292f40 !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, .2);
}
[data-testid="stMetricLabel"] { color: #9aa4b8 !important; }
[data-testid="stMetricValue"] { color: #f8fafc !important; }
[data-testid="stProgressBar"] > div > div { background: #8b7cff !important; }

[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] {
    color: #f3f5fa !important;
    background: #11151e !important;
    border-color: #30374a !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"] {
    border-style: dashed !important;
    background: linear-gradient(135deg, rgba(139, 124, 255, .08), rgba(17, 21, 30, .9)) !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
    border-color: #8b7cff !important;
    box-shadow: 0 0 0 1px #8b7cff, 0 0 24px rgba(139, 124, 255, .15) !important;
}
.stButton > button, .stDownloadButton > button {
    min-height: 2.55rem;
    border: 1px solid rgba(139, 124, 255, .45) !important;
    border-radius: 0.75rem !important;
    background: linear-gradient(135deg, #7568e8, #9a72e8) !important;
    box-shadow: 0 8px 22px rgba(99, 82, 218, .2);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #b8afff !important;
    box-shadow: 0 10px 28px rgba(139, 124, 255, .35) !important;
}
[data-testid="stButton"] button[kind="secondary"],
.stButton > button[kind="secondary"] {
    background: #292d38 !important;
    background-color: #292d38 !important;
    background-image: none !important;
    border: 1px solid #414756 !important;
    color: #f8fafc !important;
    box-shadow: none !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    background: #343947 !important;
    border-color: #686f82 !important;
    color: #ffffff !important;
}
[data-testid="stExpander"] {
    background: rgba(18, 21, 29, .72) !important;
    border: 1px solid #292f40 !important;
    border-radius: 14px !important;
}
hr { border-color: #252b3b !important; }

/* Consistent dashboard rhythm and aligned cards across Streamlit columns. */
.block-container > div { gap: 1.15rem; }
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
    gap: 1rem !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 0;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div {
    height: 100%;
}
.hero {
    min-height: 260px;
    display: flex;
    align-items: center;
    margin-bottom: .3rem;
}
.hero h1 {
    max-width: 780px;
    line-height: 1.08 !important;
    text-wrap: balance;
}
.hero p {
    line-height: 1.65;
    margin-bottom: 0;
}
.compare-hero {
    padding: 1.35rem 1.5rem;
    border: 1px solid #35304e;
    border-radius: 18px;
    background: radial-gradient(circle at 90% 15%, rgba(139,124,255,.25), transparent 18rem), linear-gradient(120deg,#171a29,#28204c 68%,#173b3d);
    color: #fff;
    margin: .6rem 0 1rem;
    box-shadow: 0 18px 42px rgba(0,0,0,.24);
}
.compare-hero .eyebrow { color: #bfdbfe !important; }
.compare-hero h3 { margin: .4rem 0; color: #fff !important; line-height: 1.2; }
.compare-hero p { margin: .35rem 0 0; color: #d9d9eb !important; line-height: 1.55; }
.preview-card, .capability, .how-step {
    height: 100%;
    box-sizing: border-box;
}
.preview-card { display: flex; flex-direction: column; }
.preview-card .wireframe { flex: 1; }
.preview-card > p:last-child { margin-top: auto; padding-top: .45rem; }
.capability {
    display: flex;
    flex-direction: column;
}
.capability p { flex: 1; line-height: 1.55; }
.how-step { display: flex; flex-direction: column; }
.how-step h4 { min-height: 2.6em; line-height: 1.3; }
.section-heading, [data-testid="stSubheader"] {
    margin-top: 1.5rem !important;
    margin-bottom: .8rem !important;
}
[data-testid="stMetric"] {
    min-height: 108px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
[data-testid="stMetricLabel"] { line-height: 1.35; }
[data-testid="stMarkdownContainer"] p { line-height: 1.6; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stFileUploaderDropzone"] { min-height: 170px; }
.stButton > button, .stDownloadButton > button {
    min-height: 2.75rem;
    white-space: normal;
    line-height: 1.25;
}

@media (max-width: 900px) {
    .block-container { padding: 1.5rem 1rem 3rem !important; }
    .hero { padding: 1.7rem 1.35rem !important; }
}
@media (max-width: 700px) {
    .block-container { padding: 1.25rem .85rem 2.5rem !important; }
    [data-testid="stHorizontalBlock"] { gap: .7rem !important; }
    .hero { min-height: 0; padding: 1.5rem 1.15rem !important; }
    .hero h1 { font-size: clamp(1.9rem, 9vw, 3rem) !important; }
    .preview-card { min-height: 0; }
    .how-step h4 { min-height: 0; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition-duration: .01ms !important; }
}
</style>
"""
