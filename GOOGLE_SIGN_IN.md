# Google sign-in setup

RentalOps checks Google sign-in and your approved-email list before accessing any records. Missing configuration blocks access. This is a single-owner app: all approved users share the same records, not separate accounts or property permissions.

## 1. Register the app with Google

1. Open https://console.cloud.google.com and create or select a project for RentalOps.
2. Open **Google Auth Platform** (older interfaces may call this **APIs & Services → OAuth consent screen**).
3. Configure branding: app name **RentalOps**, your support email, and developer contact email.
4. Under **Audience**, choose **External** for a personal Google account. Keep the app in testing for this initial setup and add your Google email as a test user. Google Workspace accounts may allow an internal audience instead.
5. Under **Clients**, create an OAuth client with application type **Web application**.
6. Add your exact Streamlit application URL as an **Authorized JavaScript origin**, without a trailing path. Example: `https://your-app.streamlit.app`.
7. Add that same application's URL followed by `/oauth2callback` as an **Authorized redirect URI**. Example: `https://your-app.streamlit.app/oauth2callback`.
8. Copy the client ID and client secret privately. Do not commit the downloaded credentials file or share it in chat.

Streamlit requests the basic OpenID Connect identity scopes: `openid profile email`. It does not need access to Gmail, Drive, or Calendar. Provider testing limits and session behavior depend on Google's current policy.

## 2. Configure Streamlit Secrets

In Streamlit Community Cloud, open the app's **Settings → Secrets**. Preserve your existing `DATABASE_URL` and add the entries below. Replace every placeholder privately. Top-level entries must appear **before** the `[auth]` table; otherwise TOML treats them as authentication settings.

```toml
DATABASE_URL = "YOUR_EXISTING_NEON_CONNECTION_STRING"
allowed_emails = ["YOUR_GOOGLE_EMAIL"]

[auth]
redirect_uri = "https://YOUR-APP.streamlit.app/oauth2callback"
cookie_secret = "YOUR_RANDOM_COOKIE_SECRET"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Use a password manager's generator for a random cookie secret of at least 64 characters. Do not use your Google password. If Python is available locally, `python -c "import secrets; print(secrets.token_urlsafe(48))"` generates a suitable random value; enter it directly into Secrets and keep it private.

Save and let Streamlit restart. The redirect URI must exactly match Google's setting, including scheme, domain, and path. You do not need to replace the Neon connection string.

## 3. Verify the hosted flow

1. Open the app in a private browser window. Records should be hidden and **Sign in with Google** should appear.
2. Sign in with your approved account. Verify your records are available and the sidebar shows your email and **Sign out**.
3. Sign out. Verify records are hidden again.
4. To test rejection, add a second account as a Google test user but do not add it to `allowed_emails`. It should receive **This Google account is not authorized to access RentalOps**. Remove the extra test user afterward if no longer needed.

Automated tests check authorization logic and that missing setup cannot access the database. They do not perform real Google login; complete these browser checks to validate the deployment.

## Troubleshooting

- **Private access is not configured:** confirm all placeholders were replaced, `allowed_emails` is a top-level list, and the Google metadata URL matches this guide.
- **redirect_uri_mismatch:** compare Google's authorized redirect URI and Streamlit's `redirect_uri` exactly.
- **Access blocked by Google:** confirm your account is a test user when the consent screen is in testing.
- **Not authorized in RentalOps:** confirm the signed-in account's verified email is listed in `allowed_emails`.

Sign-in cookies may last up to 30 days; use **Sign out** on shared devices. Signing out of one session does not necessarily end already-open sessions in other tabs. An approved-email list controls this app's access; it does not replace database backups, operational monitoring, or an independent data protection review before real business use.
