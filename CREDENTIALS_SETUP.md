# Credentials Setup Guide

## `client_secrets.json` (Manual Setup)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**, search for **YouTube Data API v3**, and click **Enable**
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth client ID**
   - If prompted, configure the **OAuth consent screen** first (choose "External", fill in the app name and your email)
6. Set application type to **Desktop app**, give it a name, click **Create**
7. Click **Download JSON** on the created credential
8. Rename the downloaded file to `client_secrets.json` and place it in the project root

> **OAuth Consent Screen tip:** You'll need to add your YouTube account as a **Test user** under the consent screen settings, since the app is in "Testing" mode.

---

## `token.json` (Auto-Generated)

You **don't create this manually** — it's generated automatically on the **first run**:

1. Make sure `client_secrets.json` is in place
2. Run the automation:
   ```powershell
   uv run youtube-automation
   ```
3. A browser window will open → sign in with your Google/YouTube account → grant the requested permissions
4. `token.json` is saved automatically to the project root and reused for all future runs (auto-refreshed when expired)

---

**Summary:** You only need to manually obtain `client_secrets.json` from Google Cloud Console. `token.json` is created for you on first run via the OAuth browser flow.
