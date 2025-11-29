from typing import Optional, Dict
from datetime import timezone

from app.database import SessionLocal
from app.models.session import Session as DBSession
from app.models.user import User as DBUser


def store_refresh_token(hashed: str, user_email: str, expiry) -> None:
    """Persist a refresh token into the database against the user's session.

    expiry may be timezone-aware; the DB stores naive UTC datetimes, so we
    normalize before writing. When returning a record we convert back to
    timezone-aware UTC.
    """
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            raise ValueError("user not found")

        # normalize expiry to naive UTC for DB storage
        if hasattr(expiry, "astimezone"):
            expiry_naive = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            expiry_naive = expiry

        session = DBSession(user_id=user.id, refresh_token_hash=hashed, expires_at=expiry_naive, active=True)
        db.add(session)
        db.commit()
    finally:
        db.close()


def get_refresh_token(hashed: str) -> Optional[Dict]:
    db = SessionLocal()
    try:
        sess = db.query(DBSession).filter(DBSession.refresh_token_hash == hashed, DBSession.active == True).first()
        if not sess:
            return None
        user = db.query(DBUser).filter(DBUser.id == sess.user_id).first()
        # return expiry as timezone-aware UTC to match security helpers
        expiry = sess.expires_at.replace(tzinfo=timezone.utc)
        return {"user_email": user.email, "expiry": expiry}
    finally:
        db.close()


def revoke_refresh_token(hashed: str) -> None:
    db = SessionLocal()
    try:
        sess = db.query(DBSession).filter(DBSession.refresh_token_hash == hashed).first()
        if not sess:
            return
        sess.active = False
        db.add(sess)
        db.commit()
    finally:
        db.close()


def revoke_all_refresh_tokens_for_user(user_email: str) -> None:
    """Revoke all active refresh tokens for a user. Used to enforce single-session behavior."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            return
        
        db.query(DBSession).filter(
            DBSession.user_id == user.id,
            DBSession.active == True
        ).update({"active": False})
        db.commit()
    finally:
        db.close()
