"""
Manual page-break detection for .docx imports.

mammoth (the library admin_routes.py uses to convert .docx -> HTML) does not
support Word page breaks at all - it hits `<w:br w:type="page"/>` and just
drops it with an "Unsupported break type: page" warning (confirmed against
mammoth's own issue tracker, not guessed). Word also doesn't store *implicit*
page breaks anywhere in the file - only explicit ones the author inserted
with Ctrl+Enter - so this can only ever detect breaks someone deliberately
placed, never "natural" reading-page boundaries in an unpaginated document.

Fix: pre-process the raw .docx with python-docx before handing it to
mammoth. Find every explicit page-break run, insert a new paragraph
containing a unique sentinel string immediately after it, and re-save. That
sentinel is now just plain text as far as mammoth is concerned, so it
survives conversion as its own <p>, and admin_routes.py splits chapters into
pages on it after the normal <h1>-chapter-splitting pass.
"""
import io

from docx import Document
from docx.oxml.ns import qn

PAGE_BREAK_SENTINEL = "@@IGLOBALS_PAGE_BREAK_7f3a9c@@"


def inject_page_break_sentinels(file_bytes: bytes) -> bytes:
    """Returns the docx bytes unchanged if it has no manual page breaks at
    all (the common case) - only re-saves through python-docx when there's
    actually something to mark, to avoid any risk of python-docx's
    save/reload round-trip subtly altering formatting mammoth would
    otherwise see untouched."""
    doc = Document(io.BytesIO(file_bytes))
    found_any = False

    for para in list(doc.paragraphs):
        has_page_break = any(
            br.get(qn('w:type')) == 'page'
            for run in para.runs
            for br in run._element.findall(qn('w:br'))
        )
        if not has_page_break:
            continue
        found_any = True
        marker_para = doc.add_paragraph()  # appended at doc end, then relocated below
        marker_para.add_run(PAGE_BREAK_SENTINEL)
        para._p.addnext(marker_para._p)

    if not found_any:
        return file_bytes

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def split_nodes_into_pages(nodes) -> list:
    """Splits a chapter's accumulated BeautifulSoup nodes into pages
    wherever a standalone <p>@@IGLOBALS_PAGE_BREAK_7f3a9c@@</p> marker
    paragraph appears (inserted above), dropping the marker itself. Always
    returns at least one page, even if empty, so a chapter with no manual
    breaks still ends up as a single-page chapter."""
    pages = []
    current = []

    for node in nodes:
        is_marker = (
            getattr(node, 'name', None) == 'p'
            and node.get_text(strip=True) == PAGE_BREAK_SENTINEL
        )
        if is_marker:
            pages.append(''.join(str(n) for n in current))
            current = []
        else:
            current.append(node)

    pages.append(''.join(str(n) for n in current))
    return pages
