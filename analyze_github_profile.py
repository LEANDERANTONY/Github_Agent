import requests
import openai

# Read tokens from local files
with open('github_token.txt') as f:
    GITHUB_TOKEN = f.read().strip()
with open('openai_key.txt') as f:
    OPENAI_KEY = f.read().strip()

GITHUB_USER = "LEANDERANTONY"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_repos(user):
    url = f"https://api.github.com/users/{user}/repos?per_page=100"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_portfolio_suggestions(repos):
    openai.api_key = OPENAI_KEY
    repo_descriptions = [
        f"{repo['name']}: {repo['description'] or 'No description'}"
        for repo in repos
    ]
    prompt = (
        "You are an expert GitHub portfolio reviewer. "
        "Here is a list of my public repositories and their descriptions:\n\n"
        + "\n".join(repo_descriptions)
        + "\n\nSuggest specific, actionable ways I can improve my GitHub portfolio for recruiters."
    )
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful technical reviewer."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    repos = get_repos(GITHUB_USER)
    print("Your repos:")
    for repo in repos:
        print(f"- {repo['name']}")
    print("\nPortfolio suggestions from GPT-4o:\n")
    print(get_portfolio_suggestions(repos))

