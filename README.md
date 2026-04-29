# GitHub Dev Points Checker

這是一個 Flask 線上工具，透過 GitHub OAuth 授權後，根據下列規則計算 Dev Points：

- Account age: `0.5 pt / month` (max `6`)
- Public commits (last 90 days): `0.1 pt each` (max `3`)
- Original repos (public, non-empty): `0.5 pt each` (max `1`)
- Stars on original repos: `0.1 pt each` (max `5`)

達標條件：`總分 >= 7`

## 1) 建立 GitHub OAuth App

到 GitHub `Settings -> Developer settings -> OAuth Apps -> New OAuth App`

建議填寫：
- Application name: `GitHub Dev Points Checker`
- Homepage URL: `http://localhost:5000`
- Authorization callback URL: `http://localhost:5000/callback`

建立後取得：
- `Client ID`
- `Client Secret`

## 2) 環境變數

複製 `.env.example` 為 `.env`，填入你的值：

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

開啟：`http://localhost:5000`

## 4) 部署

可部署到 Render / Railway / Fly.io / 任意支援 Python 的平台。
部署時同樣設定上述三個環境變數，並把 callback URL 換成你的正式網域，例如：

`https://your-domain.com/callback`
