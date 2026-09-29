"""
Pulls a Google Doc as a .docx file via a service account, so it can go
through the exact same admin_routes.py conversion pipeline (mammoth +
docx_pages.py) as a manually-uploaded Word file.

Deliberately NOT using the Docs API's own HTML export - that path drops
manual page breaks entirely (confirmed: Google's own guidance recommends a
.docx round-trip for anyone who needs page breaks to survive). Exporting as
.docx instead means zero new conversion code - a Google Doc becomes just
another .docx by the time process_docx_bytes() ever sees it.

Auth: a service account, NOT OAuth - there is no per-admin login/consent
step here. Each Google Doc that needs importing must be explicitly shared
with the service account's email (Share button in Google Docs, paste its
address, Viewer access is enough) - same as sharing a doc with any other
Google account. See docs/GOOGLE_DOCS_IMPORT_SETUP.md for the one-time setup.
"""
import os
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

_DOC_URL_PATTERN = re.compile(r'/document/d/([a-zA-Z0-9_-]+)')


class GoogleDocsImportError(Exception):
    """User-facing error - message is safe to show directly in the admin UI."""
    pass


def extract_doc_id(url_or_id: str) -> str:
    """Accepts either a full Google Docs URL or a bare file ID, returns the ID."""
    url_or_id = url_or_id.strip()
    match = _DOC_URL_PATTERN.search(url_or_id)
    if match:
        return match.group(1)
    if re.fullmatch(r'[a-zA-Z0-9_-]{20,}', url_or_id):
        return url_or_id
    raise GoogleDocsImportError(
        "That doesn't look like a Google Docs link or ID. Paste the full URL "
        "from your browser's address bar while the doc is open."
    )


def _get_drive_service():
    key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    key_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY_FILE')

    if key_json:
        import json
        info = json.loads(key_json)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    elif key_file:
        credentials = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    else:
        raise GoogleDocsImportError(
            'Google Docs import is not configured on the server '
            '(GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_SERVICE_ACCOUNT_KEY_FILE missing).'
        )

    return build('drive', 'v3', credentials=credentials, cache_discovery=False)


def export_doc_as_docx(url_or_id: str) -> bytes:
    """Fetches a Google Doc's content as raw .docx bytes. Raises
    GoogleDocsImportError with a user-facing message on any failure -
    most commonly, the doc not being shared with the service account yet."""
    doc_id = extract_doc_id(url_or_id)
    service = _get_drive_service()

    try:
        return service.files().export(fileId=doc_id, mimeType=DOCX_MIME_TYPE).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise GoogleDocsImportError(
                "Doc not found. Double-check the link, and make sure it's a Google Doc "
                "(not a Word file already stored in Drive)."
            )
        if e.resp.status == 403:
            raise GoogleDocsImportError(
                "No access to this doc. Share it with the import service account's email "
                "(see the admin settings page) - Viewer access is enough - then try again."
            )
        raise GoogleDocsImportError(f'Google Drive returned an error: {e}')
