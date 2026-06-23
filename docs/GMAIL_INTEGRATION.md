# Gmail Integration Guide

PhishShield-Engine comes with native support for scanning your Gmail inbox using the official Google API. This enables the engine to automatically classify incoming emails, log security risk scores, and flag threats right from your live mailbox!

## Setup Instructions

### 1. Create a Google Cloud Project

To access the Gmail API, you need to set up OAuth 2.0 Credentials via the Google Cloud Console.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a project** > **New Project** and name it something like `PhishShield-Gmail-Scanner`.
3. In the left-hand navigation menu, click **APIs & Services** > **Library**.
4. Search for the **Gmail API** and click **Enable**.

### 2. Configure the OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select **External** (if you don't have a Google Workspace account) and click `Create`.
3. Fill in the required fields (App name, User support email, Developer contact).
4. For **Scopes**, click `Add or Remove Scopes` and add the specific Gmail scope: `https://www.googleapis.com/auth/gmail.modify`
5. Under **Test users**, add the email address of the inbox you want to monitor. Click `Save and Continue`.

### 3. Generate Credentials

1. Go to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Choose **Desktop app** as the Application type and give it a name like `PhishShield Local Client`.
4. Click `Create`.
5. A modal will pop up with your credentials. Click **Download JSON** to download the credentials file.

### 4. Configure PhishShield-Engine

1. Rename the downloaded JSON file to `credentials.json`.
2. Move the file into your local path so it lives at: `config/credentials.json`.
3. The directory tree should look like this:

```text
PhishShield-Engine/
├── config/
│   ├── config.yaml
│   └── credentials.json    <-- Place your downloaded file here
```

### 5. Authenticate your Inbox (First Run)

To trigger the Google OAuth login flow and generate an access token for PhishShield-Engine, run the integration script manually:

```bash
python -m src.integrations.gmail_client
```

- A browser tab will open prompting you to log into your Google Account.
- You might see a warning saying `Google hasn't verified this app`. Because this is your own private app, click **Advanced** -> **Go to PhishShield Local Client (unsafe)**.
- Accept the permissions requested (read and modify your email).
- Once completed, the window will say the authentication flow has completed. You can close the browser.

A `token.json` file will automatically be created in the main directory. This saves your access/refresh tokens.

### 6. Automated Threat Handling

Anytime the Gmail client is triggered via `scan_inbox()`, it will automatically download your recent emails using the `token.json` session.

By default, any email flagged with a prediction of `spam` or a `security_risk_score > 70` is logged as a threat in PhishShield.

You can wire this `scan_inbox()` call to a cronjob, an internal task scheduler, or execute it manually using the CLI.

> **Note**: If you want to configure auto-deletion or auto-labelling natively inside the Gmail client, edit the `_mark_as_threat(msg_id)` method inside `src/integrations/gmail_client.py`!

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)
**Last Updated**: 2026-06-23
