"""
On-demand StudyNeat handoff. See studyneat_client.py for why this is a
single per-click call rather than any kind of sync - iGlobal_edu stays the
source of truth for ownership/subscription, StudyNeat only ever learns about
a book at the exact moment someone clicks through for it.
"""
import logging

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required

from app import app
from models import Book, Purchase, get_active_subscription
from studyneat_client import StudyNeatError, create_sso_session

logger = logging.getLogger(__name__)


@app.route('/studyneat/launch/<int:book_id>')
@login_required
def studyneat_launch(book_id):
    book = Book.query.get_or_404(book_id)

    owns_book = book.is_free or Purchase.query.filter_by(
        user_id=current_user.id, book_id=book_id, payment_status='success'
    ).first() is not None
    if not owns_book:
        flash('You need to own this book first.', 'warning')
        return redirect(url_for('reading', book_id=book_id))

    if not get_active_subscription(current_user.id):
        flash('AI Deep Dive requires an active Pro subscription.', 'warning')
        return redirect(url_for('subscribe'))

    try:
        redirect_url = create_sso_session(
            email=current_user.email,
            name=current_user.full_name,
            book_id=str(book_id),
        )
    except StudyNeatError as exc:
        logger.error("StudyNeat launch failed for user=%s book_id=%s: %s", current_user.id, book_id, exc)
        flash("Couldn't open AI Deep Dive right now - please try again shortly.", 'error')
        return redirect(url_for('reading', book_id=book_id))

    return redirect(redirect_url)
