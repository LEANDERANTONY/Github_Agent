import streamlit as st
import openai
import requests
import os

# -------------------------
# Load your own OpenAI API key from file
def load_openai_key():
    if os.path.exists("openai_key.txt"):
        with open("openai_key.txt") as f:
            return f.read().strip()
    else:
        raise Exception("Missing openai_key.txt")

# -------------------------
# GitHub repo fetch (username = public, blank = your private repos via token)
def get_github_repos(username=None):
    if username:
        url = f"https://api.github.com/users/{username}/repos"
        headers = {}
    else:
        if not os.path.exists("github_token.txt"):
            raise Exception("No GitHub username and no github_token.txt found.")
        with open("github_token.txt") as f:
            token = f.read().strip()
        url = "https://api.github.com/user/repos"
        headers = {"Authorization": f"token {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API error {response.status_code}: {response.text}")
    return response.json()

# -------------------------
# GPT-4o suggestion generation
def get_portfolio_suggestions(repos):
    openai.api_key = load_openai_key()

    repo_descriptions = [
        f"{repo['name']}: {repo['description'] or 'No description'}"
        for repo in repos
    ]

    prompt = (
        "You are an expert GitHub portfolio reviewer. "
        "Here is a list of public repositories and their descriptions:\n\n"
        + "\n".join(repo_descriptions)
        + "\n\nSuggest specific, actionable ways to improve the GitHub portfolio for recruiters."
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful technical reviewer."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
import re

def generate_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name='CustomBold',
        fontSize=12,
        leading=16,
        fontName="Helvetica-Bold",
        textColor="#222244",
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name='CustomBody',
        fontSize=10,
        leading=14,
        fontName="Helvetica",
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='CustomBullet',
        fontSize=10,
        leading=14,
        leftIndent=12,
        bulletIndent=0,
        bulletFontName="Helvetica-Bold"
    ))

    flowables = []

    for raw_line in text.split("\n"):
        raw_line = raw_line.strip()
        line = raw_line.replace("**", "")  # strip ALL double asterisks

        if line.startswith("# "):
            flowables.append(Paragraph(line.replace("# ", ""), styles["CustomBold"]))
            flowables.append(Spacer(1, 10))

        elif line.startswith("## "):
            flowables.append(Paragraph(line.replace("## ", ""), styles["CustomBold"]))
            flowables.append(Spacer(1, 8))

        elif re.match(r"^\d+\.", line):
            flowables.append(Paragraph(line, styles["CustomBold"]))
            flowables.append(Spacer(1, 8))

        elif line.startswith("- "):
            flowables.append(Paragraph(f"• {line[2:]}", styles["CustomBullet"]))
            flowables.append(Spacer(1, 4))

        elif line == "":
            flowables.append(Spacer(1, 10))

        else:
            flowables.append(Paragraph(line, styles["CustomBody"]))
            flowables.append(Spacer(1, 6))

    doc.build(flowables)
    buffer.seek(0)
    return buffer

def generate_docx(text):
    doc = Document()
    doc.add_heading("GitHub Portfolio Suggestions", level=1)
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_txt(text):
    return BytesIO(text.encode("utf-8"))

def generate_markdown(text):
    return BytesIO(text.encode("utf-8"))

# -------------------------
# Streamlit App UI
st.set_page_config(page_title="GitHub Portfolio Reviewer", page_icon="🤖")
st.title("🤖 GitHub Portfolio Reviewer Agent")

st.markdown("Enter a GitHub username to review their public portfolio. Leave it blank to review your own (if `github_token.txt` is present).")

github_username = st.text_input("GitHub Username (optional)", placeholder="e.g. torvalds")

if "feedback" not in st.session_state:
    st.session_state.feedback = None

if st.button("🔍 Review Portfolio"):
    try:
        with st.spinner("Fetching GitHub repos and querying GPT-4o..."):
            repos = get_github_repos(username=github_username)
            st.session_state.feedback = get_portfolio_suggestions(repos)
    except Exception as e:
        st.error(f"❌ {str(e)}")

if st.session_state.feedback:
    st.success("✅ Suggestions generated!")
    st.markdown("### 💡 GPT-4o Suggestions")
    st.markdown(st.session_state.feedback)

    # UI: format selection

    st.markdown("#### 📥 Download Suggestions")
    file_format = st.selectbox("📁 Choose download format", [
        "Markdown (.md)",
        "Text (.txt)",
        "Word (.docx)",
        "PDF (.pdf)"
    ])

    if file_format == "Markdown (.md)":
        file_data = generate_markdown(st.session_state.feedback)
        mime_type = "text/markdown"
        file_ext = "md"

    elif file_format == "Text (.txt)":
        file_data = generate_txt(st.session_state.feedback)
        mime_type = "text/plain"
        file_ext = "txt"

    elif file_format == "Word (.docx)":
        file_data = generate_docx(st.session_state.feedback)
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_ext = "docx"

    elif file_format == "PDF (.pdf)":
        file_data = generate_pdf(st.session_state.feedback)
        mime_type = "application/pdf"
        file_ext = "pdf"

    st.download_button(
        label=f"💾 Download Suggestions as {file_format.split()[0]}",
        data=file_data.getvalue(),
        file_name = f"{github_username or 'my'}_portfolio_suggestions.{file_ext}",
        mime=mime_type
    )



st.markdown("---")
st.caption("🧠 Built by Leander Antony • Powered by GPT-4o + GitHub API")

