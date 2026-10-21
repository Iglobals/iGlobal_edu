"""
JUPEB exam-access packages - the single source of truth for which iTest exam
keys exist, their human labels, how a book title maps onto them, and how a
package's price is computed.

Used by: models (helpers), routes (checkout/pricing), admin_routes (book
form), seed_data.py (fresh seeds). The Alembic migration that backfilled
existing rows (migrations/versions/c4e7a9b1d2f3_add_exam_packages.py) carries
an inline COPY of SUBJECT_ALIASES / parse_title_exam_package, because
migrations must not import live app code - keep the two in sync if the
mapping ever changes.

The exam key strings below are a contract with iTest - they must match the
keys iTest's /api/webhooks/igs/exam-access receiver understands exactly.
"""
import re

# (key, human label) - order is the order shown in the admin form.
EXAM_SUBJECTS = [
    ('jupeb-mathematics', 'Mathematics'),
    ('jupeb-physics', 'Physics'),
    ('jupeb-biology', 'Biology'),
    ('jupeb-chemistry', 'Chemistry'),
    ('jupeb-government', 'Government'),
    ('jupeb-literature-in-english', 'Literature-in-English'),
    ('jupeb-economics', 'Economics'),
    ('jupeb-crs', 'Christian Religious Studies'),
    ('jupeb-accounting', 'Accounting'),
    ('jupeb-business-studies', 'Business Studies'),
]
EXAM_KEYS = [k for k, _ in EXAM_SUBJECTS]
EXAM_LABELS = dict(EXAM_SUBJECTS)

# Default add-on prices (naira) used by the backfill migration and the seed.
SINGLE_SUBJECT_ADDON_NAIRA = 1000.0
THREE_IN_ONE_ADDON_NAIRA = 2000.0

# Purchase.package values
PACKAGE_BOOK = 'book'
PACKAGE_BOOK_EXAM = 'book_exam'
PACKAGES = (PACKAGE_BOOK, PACKAGE_BOOK_EXAM)

# Normalised subject name (lowercase, single spaces, hyphens -> spaces) -> key
SUBJECT_ALIASES = {
    'mathematics': 'jupeb-mathematics',
    'maths': 'jupeb-mathematics',
    'math': 'jupeb-mathematics',
    'physics': 'jupeb-physics',
    'biology': 'jupeb-biology',
    'chemistry': 'jupeb-chemistry',
    'government': 'jupeb-government',
    'literature': 'jupeb-literature-in-english',
    'literature in english': 'jupeb-literature-in-english',
    'economics': 'jupeb-economics',
    'crs': 'jupeb-crs',
    'christian religious studies': 'jupeb-crs',
    'accounting': 'jupeb-accounting',
    'business': 'jupeb-business-studies',
    'business studies': 'jupeb-business-studies',
}

_SINGLE_RE = re.compile(r'^\s*JUPEB\s+KEYPOINTS\s+FOR\s+(.+?)\s*$', re.IGNORECASE)
_THREE_IN_ONE_RE = re.compile(r'^\s*THREE-IN-ONE\b.*\(([^)]*)\)', re.IGNORECASE)


def _normalise_subject(name):
    return ' '.join(name.replace('-', ' ').lower().split())


def subject_to_key(name):
    """'Maths' / 'CRS' / 'Literature-in-English' -> exam key, or None."""
    return SUBJECT_ALIASES.get(_normalise_subject(name or ''))


def parse_title_exam_package(title):
    """Infer (exam_keys, addon_price_naira) from a book title.

    "JUPEB KEYPOINTS FOR <SUBJECT>"            -> ([key], 1000.0)
    "THREE-IN-ONE ... (A, B, C)"               -> ([kA, kB, kC], 2000.0)
    anything else, or any unrecognised subject -> ([], None)  (no package)

    All-or-nothing on purpose: a combo book with one unknown subject gets no
    package rather than a partial one, so an admin sets it explicitly.
    """
    title = title or ''
    m = _THREE_IN_ONE_RE.match(title)
    if m:
        parts = [p.strip() for p in m.group(1).split(',') if p.strip()]
        keys = [subject_to_key(p) for p in parts]
        if not keys or any(k is None for k in keys):
            return [], None
        deduped = list(dict.fromkeys(keys))
        return deduped, THREE_IN_ONE_ADDON_NAIRA
    m = _SINGLE_RE.match(title)
    if m:
        key = subject_to_key(m.group(1))
        if key:
            return [key], SINGLE_SUBJECT_ADDON_NAIRA
    return [], None


def clean_exam_keys(keys):
    """Keep only known keys, de-duplicated, in canonical order."""
    wanted = set(keys or [])
    return [k for k in EXAM_KEYS if k in wanted]


def exam_labels(keys):
    return [EXAM_LABELS.get(k, k) for k in (keys or [])]


def offers_exam_package(book):
    """True when this book can be bought with (or upgraded to) exam access.
    Works on a Book model instance or a row/dict with the same attributes."""
    get = (lambda f: book.get(f)) if isinstance(book, dict) else (lambda f: getattr(book, f, None))
    if get('is_free'):
        return False
    addon = get('exam_addon_price_naira') or 0
    return addon > 0 and bool(get('exam_keys'))


def package_price_naira(book, package):
    """Server-side price for a package. Raises ValueError for a package the
    book doesn't offer - never trust a client-sent amount."""
    if package == PACKAGE_BOOK:
        return float(book.price_naira or 0)
    if package == PACKAGE_BOOK_EXAM:
        if not offers_exam_package(book):
            raise ValueError('This book does not offer an exam package')
        return float(book.price_naira or 0) + float(book.exam_addon_price_naira)
    raise ValueError(f'Unknown package {package!r}')


def upgrade_price_naira(book):
    if not offers_exam_package(book):
        raise ValueError('This book does not offer an exam package')
    return float(book.exam_addon_price_naira)


def naira_to_kobo(naira):
    # round() not int(): 1999.99 * 100 == 199998.99999... in float.
    return int(round(float(naira) * 100))
