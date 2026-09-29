# Google Docs Import — One-Time Setup

Lets admins write a book chapter in Google Docs (native image resize/positioning,
familiar UI) and pull it straight into the book editor, using the exact same
Word-import pipeline that already exists — a Google Doc is exported as a real
`.docx` file server-side, so nothing new needs to understand it.

This uses a **service account**, not OAuth — no admin has to "log in with
Google" for this feature. Instead, each Google Doc that needs importing is
individually shared with the service account's email, the same way you'd
share it with any other person.

## Steps (reusing your existing Google Cloud project from the OAuth login setup)

1. Go to [console.cloud.google.com](https://console.cloud.google.com), select
   the same project you already used for "Sign in with Google."

2. **Enable the API**: APIs & Services → Library → search "Google Drive API" → Enable.

3. **Create a service account**: IAM & Admin → Service Accounts → Create
   Service Account. Give it any name (e.g. `docx-importer`). No project-level
   roles are required — access is controlled entirely by which Docs get
   shared with it, not by IAM permissions.

4. **Create a key**: open the new service account → Keys tab → Add Key →
   Create new key → JSON. This downloads a `.json` file — **treat it as a
   secret**, same as any API key.

5. **Copy the service account's email** — it's in that JSON file's
   `client_email` field, looks like:
   ```
   docx-importer@your-project-id.iam.gserviceaccount.com
   ```

6. **Add it to your `.env`** — either paste the whole JSON file's contents as
   one line into `GOOGLE_SERVICE_ACCOUNT_JSON`, or save the file somewhere on
   the server and point `GOOGLE_SERVICE_ACCOUNT_KEY_FILE` at its path. Only
   one of the two is needed.

7. Restart the app.

## Using it (per book, ongoing — not a one-time step)

For **each** Google Doc you want to import, open it in Google Docs → Share →
paste the service account's email (from step 5) → give it **Viewer** access
→ Send. Without this, the import will fail with a "no access to this doc"
error — that's expected, it just means this particular doc hasn't been
shared yet.

Then in the admin editor's "Import Word Document" modal, paste the doc's
URL instead of uploading a file.

## What does and doesn't come through

Manual page breaks (Insert → Break → Page break in Google Docs) are detected,
same as in Word. Headings, bold/italic, lists, images, and tables convert the
same way a `.docx` upload would — see the "what won't carry over 1:1" notes
already in the admin editor's docs for image text-wrapping, custom fonts, and
table styling limits, which apply here identically since it's the same
pipeline underneath.
