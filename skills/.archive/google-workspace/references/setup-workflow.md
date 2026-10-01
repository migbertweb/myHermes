# Google Workspace Setup Workflow

Combined setup procedures for Google Workspace OAuth2 authentication, covering both normal desktop and remote/SSH environments.

## Overview

This reference consolidates two skills (`google-workspace-setup` and `google-workspace-integration`) that both covered the same OAuth2 setup flow for Google Workspace. The primary setup is handled by the main `google-workspace` skill's `scripts/setup.py`; this reference documents the manual/pitfall overlay for when the automation doesn't work.

## First-Time OAuth Setup

### Prerequisites

- `credentials.json` (OAuth 2.0 Client ID from Google Cloud Console) placed at `~/.config/gws/credentials.json` (or another secure path).
- Required APIs enabled in Google Cloud Console: Gmail API, Google Calendar API, Google Drive API, Google Sheets API, Google Docs API, People API.

### Scope Requirements

Use specific scopes rather than `auth/cloud-platform` to adhere to least privilege:

- Gmail: `https://www.googleapis.com/auth/gmail.modify`
- Calendar: `https://www.googleapis.com/auth/calendar`
- Drive: `https://www.googleapis.com/auth/drive.file`

### Normal Desktop Flow

Run the setup script from the main google-workspace skill:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --check
$GSETUP --client-secret /path/to/client_secret.json
$GSETUP --auth-url --services email,calendar --format json
```

### Remote/SSH Flow

When the agent runs on a remote server, `run_local_server()` will fail to open a browser on the user's machine. Instead:

1. **Generate authorization URL** — provide the link to the user so they can open it in their local browser.
2. **Manual redirect capture** — the user will see a "Site cannot be reached" error at the end of the OAuth flow. They must copy the URL from the browser's address bar to retrieve the `?code=...` value.
3. **Exchange the code**:
   ```bash
   $GSETUP --auth-code "THE_URL_OR_CODE" --format json
   ```

## Pitfalls & Lessons Learned

### SSH Redirect Pitfall
In SSH environments, the user will see a "Site cannot be reached" error at the end of the OAuth flow. They must be explicitly told to copy the URL from the browser's address bar to retrieve the `?code=...` value.

### Build Error - Default Credentials
Always pass the `credentials` object explicitly to the `build()` function of the Google API client to avoid "Default Credentials not found" errors.

### Broadening Scopes
If `invalid_scope` errors occur during execution, avoid specifying narrow scopes (like `.readonly`) within the script if a broader token was originally issued. Instead, instantiate `Credentials` from the authorized user file without explicitly passing a restricted scope list if the token already contains the necessary permissions.

### Google Docs API Indexing
When updating an existing document, use `deleteContentRange` to clear previous content before inserting new text to avoid appending or overlapping.

## Verification

After setup, verify connectivity with:
- Gmail: List the 3 most recent messages
- Calendar: List events for the current day
- Drive: List files created in the last 24 hours

## When to Use Himalaya Instead

If the user only needs email (no Calendar/Drive/Sheets/Docs), the `himalaya` skill works with a Gmail App Password (Settings → Security → App Passwords) and takes ~2 minutes to set up with no Google Cloud project needed.
