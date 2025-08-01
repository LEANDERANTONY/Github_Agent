import os

# Folder where suggestions will be saved
SUGGESTIONS_DIR = "suggestions"
os.makedirs(SUGGESTIONS_DIR, exist_ok=True)

# Mapping of repo name to its individual suggestions
repo_suggestions = {
    "AI_Job_Application_Agent": [
        "Add a 'Results' section to the README with key metrics or demo screenshots",
        "Improve README with Overview, Features, Setup, and How to Run",
        "Add license and release badges",
        "Consider deploying a live demo via Streamlit"
    ],
    "Automatic_Ticket_Classifier": [
        "Add an Overview and Results section to README",
        "Document preprocessing steps clearly",
        "Include example inputs and outputs"
    ],
    "Credit_Card_Fraud_Detection": [
        "Include key evaluation metrics in README (Precision, Recall, F1-score)",
        "Add code comments and docstrings",
        "Describe dataset and imbalance-handling approach"
    ],
    "Gesture_Recognition": [
        "Document the model architecture used",
        "Include training sample images or visualizations",
        "Add environment setup and usage instructions"
    ],
    "Github_Agent": [
        "Clarify project goal in README",
        "Add demo output screenshots or expected terminal result",
        "Document OpenAI and GitHub token usage (safely)"
    ],
    "HelpmateAI_RAG_QA_System": [
        "Add architecture diagram and description",
        "List embedding models and reranking strategies used",
        "Include performance on sample queries"
    ],
    "Lending_Club_CaseStudy": [
        "Summarize business problem and solution approach",
        "Include feature engineering steps in README",
        "Highlight key model performance results"
    ],
    "Linear_Regression_BikeDemand": [
        "Add dataset visualization or time series plot",
        "Explain model assumptions and limitations",
        "Describe prediction accuracy (R², RMSE)"
    ],
    "numpy": [
        "Consider archiving if this is a test or fork",
        "If intentional: Add purpose and README clarity"
    ],
    "portfolio": [
        "Convert into an actual portfolio site or structured index of your projects",
        "Include thumbnails and links to key repos",
        "Add summary about your role, skills, and motivations"
    ],
    "Telecom_Churn_Case_study": [
        "Clarify business objective and dataset",
        "Add model insights and churn impact interpretation",
        "Document how to replicate results"
    ]
}

# Create markdown files
for repo, suggestions in repo_suggestions.items():
    filename = os.path.join(SUGGESTIONS_DIR, f"{repo}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {repo} – Suggestions\n\n")
        for s in suggestions:
            f.write(f"- [ ] {s}\n")
    print(f"✔️ Created: {filename}")

print("\n✅ All suggestion files generated.")
