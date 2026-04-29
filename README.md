# GitHub Dev Points Checker

這是一個 Flask 線上工具，透過 GitHub OAuth 授權後，依規則計算 Dev Points，並顯示是否達到 7 分門檻。

## 計分規則

- Account age: `0.5 pt / month` (max `6`)
- Public commits (last 90 days): `0.1 pt each` (max `3`)
- Original repos (public, non-empty): `0.5 pt each` (max `1`)
- Stars on original repos: `0.1 pt each` (max `5`)

達標條件：`總分 >= 7`（總分上限 15）

## Original repos 定義

工具內的 `Original repos` 會同時符合：

- `fork == false`（不是 fork）
- `size > 0`（不是空 repo）
- 來源為使用者公開 repo 清單（public repos）

## 1) 建立 GitHub OAuth App

到 GitHub：`Settings -> Developer settings -> OAuth Apps -> New OAuth App`

建議填寫（本專案目前使用 `10901` port）：

- Application name: `GitHub Dev Points Checker`
- Homepage URL: `http://localhost:10901`
- Authorization callback URL: `http://localhost:10901/callback`

建立後取得：

- `Client ID`
- `Client Secret`

## 2) 環境變數

建立 `.env`（可參考 `.env.example`）：

```env
FLASK_SECRET_KEY=任意隨機字串
GITHUB_CLIENT_ID=你的 Client ID
GITHUB_CLIENT_SECRET=你的 Client Secret
```

## 3) 安裝與啟動

```bash
pip install -r requirements.txt
python app.py
```

開啟：`http://localhost:10901`

## 4) GitHub 哪裡看授權過的網站

- 已授權的 OAuth Apps：<https://github.com/settings/applications>
- 你自己建立的 OAuth Apps（可改 callback / 管理 secret）：<https://github.com/settings/developers>

## 5) 部署

可部署到 Render / Railway / Fly.io / 任意支援 Python 的平台。
部署時同樣設定上述三個環境變數，並把 callback URL 換成正式網域，例如：

`https://your-domain.com/callback`
