import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

GITHUB_API = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"


def github_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_all_original_nonempty_repos(token: str, username: str) -> list[dict]:
    repos = []
    page = 1

    while True:
        resp = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=github_headers(token),
            params={"per_page": 100, "page": page, "sort": "updated"},
            timeout=20,
        )
        resp.raise_for_status()
        batch = resp.json()

        if not batch:
            break

        for repo in batch:
            if (not repo.get("fork")) and repo.get("size", 0) > 0:
                repos.append(repo)

        if len(batch) < 100:
            break

        page += 1

    return repos


def get_commit_count_90_days(token: str, username: str) -> int:
    now = datetime.now(timezone.utc)
    ninety_days_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    query = f"author:{username} committer-date:>{ninety_days_ago}"

    resp = requests.get(
        f"{GITHUB_API}/search/commits",
        headers={
            **github_headers(token),
            "Accept": "application/vnd.github.cloak-preview+json",
        },
        params={"q": query, "per_page": 1},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    return int(data.get("total_count", 0))


def calculate_dev_points(token: str) -> dict:
    user_resp = requests.get(f"{GITHUB_API}/user", headers=github_headers(token), timeout=20)
    user_resp.raise_for_status()
    user = user_resp.json()

    username = user["login"]
    created_at = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    now = datetime.now(timezone.utc)

    months_old = (now.year - created_at.year) * 12 + (now.month - created_at.month)
    age_score = min(months_old * 0.5, 6.0)

    commit_count = get_commit_count_90_days(token, username)
    commit_score = min(commit_count * 0.1, 3.0)

    original_repos = get_all_original_nonempty_repos(token, username)
    original_repos_count = len(original_repos)
    total_stars = sum(int(repo.get("stargazers_count", 0)) for repo in original_repos)

    repo_score = min(original_repos_count * 0.5, 1.0)
    star_score = min(total_stars * 0.1, 5.0)

    total_score = age_score + commit_score + repo_score + star_score

    return {
        "username": username,
        "avatar_url": user.get("avatar_url"),
        "profile_url": user.get("html_url"),
        "months_old": months_old,
        "commit_count_90d": commit_count,
        "original_repos_count": original_repos_count,
        "total_stars": total_stars,
        "score": {
            "age": round(age_score, 1),
            "commits": round(commit_score, 1),
            "repos": round(repo_score, 1),
            "stars": round(star_score, 1),
            "total": round(total_score, 1),
            "threshold": 7.0,
            "passed": total_score >= 7.0,
        },
    }


@app.route("/")
def index():
    token = session.get("github_token")
    if not token:
        return render_template("index.html", result=None, error=None)

    try:
        result = calculate_dev_points(token)
        return render_template("index.html", result=result, error=None)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 401:
            session.pop("github_token", None)
            return render_template("index.html", result=None, error="授權過期，請重新登入 GitHub。")
        return render_template("index.html", result=None, error=f"GitHub API 錯誤: {exc}")
    except Exception as exc:
        return render_template("index.html", result=None, error=f"發生錯誤: {exc}")


@app.route("/login")
def login():
    if not GITHUB_CLIENT_ID:
        return "缺少 GITHUB_CLIENT_ID 環境變數", 500

    callback_url = url_for("callback", _external=True)
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "read:user public_repo",
    }
    return redirect(f"{GITHUB_OAUTH_AUTHORIZE}?{urlencode(params)}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("index"))

    if not GITHUB_CLIENT_SECRET or not GITHUB_CLIENT_ID:
        return "缺少 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET", 500

    token_resp = requests.post(
        GITHUB_OAUTH_ACCESS_TOKEN,
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        timeout=20,
    )
    token_resp.raise_for_status()
    data = token_resp.json()

    access_token = data.get("access_token")
    if not access_token:
        return "無法取得 GitHub access token", 400

    session["github_token"] = access_token
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("github_token", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10901, debug=True)


