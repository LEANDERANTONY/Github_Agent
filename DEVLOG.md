# 🛠️ DEVLOG.md – GitHub Portfolio Reviewer Agent

This log tracks the technical improvements, design decisions, and implementation challenges addressed during development.

---

## 📅 August 1, 2025 – Streamlit Frontend Integration & Export System

### ✅ Goals Achieved:
- Integrated a **Streamlit web interface** to interact with the GitHub Portfolio Reviewer agent.
- Enabled **public usage** with minimal user input:
  - No need for OpenAI key input (uses internal key).
  - GitHub token optional (reads from `github_token.txt` if user skips input).
- Allowed users to **download GPT-4o suggestions** in various formats:
  - `.md` (Markdown)
  - `.txt` (Plain Text)
  - `.docx` (Word)
  - `.pdf` (PDF via ReportLab)

---

### 🧩 Design Challenges & Fixes

#### 1. 📄 File Export Issues
- **Issue**: PDF output was broken due to `usedforsecurity` error in `reportlab 4.x`.
- **Fix**: Downgraded to `reportlab==3.6.12` to restore compatibility with `canvas()` method.

#### 2. 🧾 PDF Formatting (Option 2: ReportLab Platypus)
- Switched to `reportlab.platypus` for better paragraph styling.
- Added three custom styles:
  - `CustomBold` for headings and section titles
  - `CustomBody` for general paragraph text
  - `CustomBullet` for bullet points
- Stripped all markdown `**bold**` syntax for clean formatting.
- Ensured **headings are larger than body text**.
- Added spacing between sections for readability.

#### 3. ⚠️ Formatting Edge Cases
- Markdown-like formatting (e.g., `**bold**`) was showing asterisks literally.
- Solution: Replaced all instances of `**` before parsing to clean up output.

---

## 🧱 Architecture & UX Improvements

### 🔄 Persistent Suggestions
- Switched to `st.session_state.feedback` so that suggestions:
  - Remain visible after download
  - Do not disappear unless the app is refreshed

### 🧩 Clean Download UX
- Added a selectbox with label `📁 Choose download format`.
- Download button auto-generates filename:
  - e.g., `my_portfolio_suggestions.pdf` or `torvalds_portfolio_suggestions.md`

### 📂 File Organization
- `DEVLOG.md` now added to project root for visibility.
- Modular functions split into:
  - `generate_pdf()`, `generate_docx()`, etc.
  - Future enhancements will move utils to `/utils/` folder.

---

## ⏭️ Next Steps (Planned)
- GitHub OAuth login instead of requiring token.
- Add branding: logo header, custom colors in PDF.
- Host public-facing version on Streamlit Cloud or Hugging Face Spaces.

---

