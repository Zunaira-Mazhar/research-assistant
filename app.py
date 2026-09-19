import streamlit as st
from backend import (
    generate_research_report,
    load_history,
    add_to_history,
    read_uploaded_file,
    verify_document,
)

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

#  CUSTOM STYLING 
st.markdown("""
    <style>
    :root {
        --border-light: #E5E8EC;
        --border-dark: rgba(255,255,255,.09);
    }

    h1 {
        color: var(--text-color) !important;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: var(--text-color) !important;
        font-weight: 600;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        opacity: 0.7;
        font-size: 15px !important;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2E7D5B, #256B4C);
        color: white !important;
        border: none !important;
        border-radius: 10px;
        padding: 0.6em 1.5em;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(46, 125, 91, 0.25);
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #256B4C, #1E5A3E);
        box-shadow: 0 6px 16px rgba(46, 125, 91, 0.35);
        transform: translateY(-1px);
    }

    div.stButton > button[kind="secondary"] {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="secondary"]:hover {
        border: 1.5px solid #2E7D5B !important;
        color: #2E7D5B !important;
    }

    .stTextInput input, .stTextArea textarea {
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 15px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1.5px solid #2E7D5B !important;
        box-shadow: 0 0 0 3px rgba(46, 125, 91, 0.1);
    }

    div[data-testid="stExpander"] {
        border-radius: 12px;
        margin-bottom: 10px;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    .stMarkdown {
        line-height: 1.7;
    }

    /* ===== ANIMATIONS ===== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    .hero-icon {
        animation: pulse 2.5s ease-in-out infinite;
    }

    /* ===== HERO BANNERS (original size/corners) ===== */
    .hero-banner {
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 2.2rem;
        margin-bottom: 8px;
    }
    .hero-banner p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
    }
    .banner-research {
        background: linear-gradient(135deg, #1E2A38 0%, #2E7D5B 100%);
    }
    .banner-verify {
        background: linear-gradient(135deg, #1E2A38 0%, #4A6FA5 100%);
    }
    .banner-history {
        background: linear-gradient(135deg, #1E2A38 0%, #7B5EA7 100%);
    }
    .banner-about {
        background: linear-gradient(135deg, #1E2A38 0%, #B4874F 100%);
    }

    /* ===== FEATURE CARDS ===== */
    .feature-card {
        background: var(--secondary-background-color);
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        border: 1px solid var(--border-light);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: all 0.25s ease;
        height: 100%;
    }

    @media (prefers-color-scheme: dark) {
        .feature-card {
            border-color: var(--border-dark);
            box-shadow: 0 8px 25px rgba(0,0,0,.20);
        }
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border: 1px solid #2E7D5B;
    }
    .feature-card .icon {
        font-size: 2.2rem;
        margin-bottom: 10px;
    }
    .feature-card h4 {
        color: var(--text-color);
        margin-bottom: 6px;
    }
    .feature-card p {
        color: var(--text-color);
        opacity: 0.70;
        font-size: 0.9rem;
    }

    /* ===== VERDICT BADGES ===== */
    .verdict-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
    .verdict-supported {
        background-color: #E3F5EC;
        color: #1E7A4D;
    }
    .verdict-partial {
        background-color: #FFF4DD;
        color: #B4740F;
    }
    .verdict-not {
        background-color: #FCE8E8;
        color: #C23B3B;
    }
    .verdict-unknown {
        background-color: #EDEDED;
        color: #666666;
    }

    .claim-card {
        background: var(--secondary-background-color);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 16px;
        border: 1px solid var(--border-light);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    @media (prefers-color-scheme: dark) {
        .claim-card {
            border-color: var(--border-dark);
            box-shadow: 0 8px 25px rgba(0,0,0,.20);
        }
    }
    .claim-text {
        font-weight: 600;
        color: var(--text-color);
        font-size: 1.02rem;
        margin-bottom: 8px;
    }
    .reasoning-text {
        color: var(--text-color);
        opacity: 0.70;
        font-size: 0.92rem;
        line-height: 1.6;
    }
    .claim-card a {
        color: #2E7D5B;
    }

    /* ===== ABOUT PAGE (rich layout, dark-mode aware) ===== */
    .about-intro {
        text-align: center;
        max-width: 760px;
        margin: 0 auto 28px;
    }
    .about-intro .big-icon {
        font-size: 3.2rem;
        margin-bottom: 8px;
    }
    .about-intro .heading {
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--text-color);
    }
    .about-intro .text {
        opacity: 0.70;
        line-height: 1.65;
        color: var(--text-color);
    }

    .about-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--border-light);
        border-radius: 18px;
        padding: 23px;
        height: 100%;
        box-shadow: 0 8px 25px rgba(20,25,40,.06);
    }
    @media (prefers-color-scheme: dark) {
        .about-card {
            border-color: var(--border-dark);
            box-shadow: 0 8px 25px rgba(0,0,0,.20);
        }
    }
    .about-card .step {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2E7D5B, #256B4C);
        color: white;
        font-weight: 800;
        font-size: 1.05rem;
        margin-bottom: 15px;
    }
    .about-card .title {
        font-weight: 800;
        margin-bottom: 7px;
        color: var(--text-color);
    }
    .about-card .text {
        opacity: 0.70;
        line-height: 1.55;
        font-size: 0.9rem;
        color: var(--text-color);
    }

    .tech-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--border-light);
        border-radius: 14px;
        text-align: center;
        padding: 18px;
    }
    @media (prefers-color-scheme: dark) {
        .tech-card {
            border-color: var(--border-dark);
        }
    }
    .tech-card .icon {
        font-size: 1.6rem;
        margin-bottom: 6px;
    }
    .tech-card .title {
        font-weight: 700;
        color: var(--text-color);
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background-color: #1E2A38;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: #2C3E50 !important;
        color: #FFFFFF !important;
        border: 1px solid #3D5166 !important;
        border-radius: 10px;
        margin-bottom: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #3D5166 !important;
        border: 1px solid #5B7A99 !important;
        transform: translateX(3px);
    }

    /* ===== MOBILE RESPONSIVENESS ===== */
    @media (max-width: 768px) {
        .hero-banner {
            padding: 24px 16px;
            border-radius: 12px;
        }
        .hero-banner h1 {
            font-size: 1.5rem;
        }
        .hero-banner p {
            font-size: 0.9rem;
        }
        .hero-icon {
            font-size: 2rem !important;
        }
        .feature-card {
            padding: 16px;
            margin-bottom: 12px;
        }
        .feature-card .icon {
            font-size: 1.6rem;
        }
        .claim-card {
            padding: 14px 16px;
        }
        .claim-text {
            font-size: 0.95rem;
        }
        .about-card {
            padding: 16px;
        }
        div.stButton > button {
            font-size: 14px;
        }
        .stTextInput input, .stTextArea textarea {
            font-size: 14px;
        }
    }
    </style>
""", unsafe_allow_html=True)

#  SESSION STATE 
if "current_page" not in st.session_state:
    st.session_state.current_page = "New Research"
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "verification_output" not in st.session_state:
    st.session_state.verification_output = None


#  SIDEBAR 
with st.sidebar:
    st.markdown("## 📚 Research Assistant")
    st.markdown("---")

    if st.button("🏠 New Research", use_container_width=True):
        st.session_state.current_page = "New Research"

    if st.button("✅ Verify My Document", use_container_width=True):
        st.session_state.current_page = "Verify Document"

    if st.button("📜 Search History", use_container_width=True):
        st.session_state.current_page = "History"

    if st.button("ℹ️ About", use_container_width=True):
        st.session_state.current_page = "About"

    st.markdown("---")
    st.caption(f"Total searches: {len(st.session_state.history)}")


def verdict_class(verdict: str) -> str:
    v = verdict.lower()
    if "not" in v:
        return "verdict-not"
    if "partial" in v:
        return "verdict-partial"
    if "support" in v:
        return "verdict-supported"
    return "verdict-unknown"


#  PAGE: NEW RESEARCH 
def show_new_research_page():
    st.markdown("""
        <div class="hero-banner banner-research fade-in">
            <div class="hero-icon" style="font-size: 3rem;">📚🔬</div>
            <h1>AI Research Assistant</h1>
            <p>Get research summaries backed by real, verifiable papers instantly.</p>
        </div>
    """, unsafe_allow_html=True)

    topic = st.text_input(
        "Enter a research topic:",
        placeholder="e.g. effects of social media on teenagers"
    )

    generate = st.button("Generate Research Report", type="primary")

    if not generate:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">🔍</div>
                    <h4>Real Papers Only</h4>
                    <p>Every result comes from actual research, never invented.</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">⚖️</div>
                    <h4>Finds Contradictions</h4>
                    <p>Automatically spots where papers disagree with each other.</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">🧩</div>
                    <h4>Identifies Gaps</h4>
                    <p>Highlights what hasn't been studied yet in your topic.</p>
                </div>
            """, unsafe_allow_html=True)

    if generate:
        if not topic:
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("Searching real papers and analyzing..."):
                report = generate_research_report(topic)

            add_to_history(topic, report)
            st.session_state.history = load_history()

            st.markdown('<div class="fade-in">', unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(report)
            st.markdown('</div>', unsafe_allow_html=True)


#  PAGE: VERIFY DOCUMENT 
def show_verify_document_page():
    st.markdown("""
        <div class="hero-banner banner-verify fade-in">
            <div class="hero-icon" style="font-size: 3rem;">✅📄</div>
            <h1>Verify My Document</h1>
            <p>Upload your own research and check its claims against real, published papers.</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload a document (PDF, DOCX, or TXT):",
        type=["pdf", "docx", "txt"]
    )

    verify = st.button("Verify Document", type="primary")

    if not verify and st.session_state.verification_output is None:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">📥</div>
                    <h4>Any Format</h4>
                    <p>Works with PDF, Word, or plain text documents.</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">🧠</div>
                    <h4>Smart Claim Extraction</h4>
                    <p>AI identifies the key checkable claims in your writing.</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
                <div class="feature-card">
                    <div class="icon">🔗</div>
                    <h4>Real Evidence</h4>
                    <p>Each claim is checked against real, cited research papers.</p>
                </div>
            """, unsafe_allow_html=True)

    if verify:
        if not uploaded_file:
            st.warning("Please upload a document first.")
        else:
            with st.spinner("Reading document and verifying claims against real research..."):
                text = read_uploaded_file(uploaded_file)

                if not text.strip():
                    st.error("Could not extract any text from this file.")
                    return

                results = verify_document(text)
                st.session_state.verification_output = results

    if st.session_state.verification_output:
        st.markdown("---")
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        if not st.session_state.verification_output:
            st.info("No checkable claims were found in this document.")
        else:
            for item in st.session_state.verification_output:
                badge_class = verdict_class(item["verdict"])
                papers_html = ""
                for p in item["papers"]:
                    papers_html += f"<div style='margin-top:6px;'>• <a href='{p['link']}' target='_blank'>{p['title']} ({p['year']})</a></div>"

                st.markdown(f"""
                    <div class="claim-card">
                        <div class="verdict-badge {badge_class}">{item['verdict']}</div>
                        <div class="claim-text">{item['claim']}</div>
                        <div class="reasoning-text">{item['reasoning']}</div>
                        {papers_html}
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


#  PAGE: HISTORY 
def show_history_page():
    st.markdown("""
        <div class="hero-banner banner-history fade-in">
            <div class="hero-icon" style="font-size: 3rem;">📜🕒</div>
            <h1>Search History</h1>
            <p>Revisit every research report you've generated.</p>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("No searches yet. Go to 'New Research' to get started.")
    else:
        for item in reversed(st.session_state.history):
            with st.expander(f"🔍 {item['topic']}"):
                st.markdown(item["report"])


#  PAGE: ABOUT 
def show_about_page():
    st.markdown("""
        <div class="hero-banner banner-about fade-in">
            <div class="hero-icon" style="font-size: 3rem;">ℹ️📖</div>
            <h1>About This Tool</h1>
            <p>Understand what real research says without spending hours reading papers.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="about-intro">
            <div class="big-icon">🔬</div>
            <div class="heading">How Research Assistant Works</div>
            <div class="text">
                Enter a topic or upload a document, and the system helps connect
                your research with real academic evidence.
            </div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    steps = [
        ("1", "Enter or Upload", "Enter a research topic or upload your own PDF, DOCX, or TXT document."),
        ("2", "Find Real Research", "The system searches published papers using the OpenAlex database."),
        ("3", "Analyze Evidence", "AI summarizes findings, checks claims, contradictions, and research gaps."),
        ("4", "Verify Yourself", "Reports include real citations and links so you can inspect the evidence."),
    ]

    for i, (number, title, description) in enumerate(steps):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(f"""
                <div class="about-card fade-in">
                    <div class="step">{number}</div>
                    <div class="title">{title}</div>
                    <div class="text">{description}</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")

    tech1, tech2, tech3, tech4 = st.columns(4)
    technologies = [
        ("🐍", "Python"),
        ("🧩", "LangGraph"),
        ("⚡", "Groq"),
        ("🎈", "Streamlit"),
    ]

    for col, (icon, name) in zip((tech1, tech2, tech3, tech4), technologies):
        with col:
            st.markdown(f"""
                <div class="tech-card">
                    <div class="icon">{icon}</div>
                    <div class="title">{name}</div>
                </div>
            """, unsafe_allow_html=True)


#  MAIN ROUTING 
if st.session_state.current_page == "New Research":
    show_new_research_page()
elif st.session_state.current_page == "Verify Document":
    show_verify_document_page()
elif st.session_state.current_page == "History":
    show_history_page()
elif st.session_state.current_page == "About":
    show_about_page()
