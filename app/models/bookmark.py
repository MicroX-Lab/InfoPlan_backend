# encoding: utf-8
from datetime import datetime

from app.extensions import db


class UserBookmark(db.Model):
    __tablename__ = "user_bookmarks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)
    custom_tags_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "note_id", name="uq_user_note_bookmark"),
    )

    note = db.relationship("Note", backref="bookmarks")

    def to_dict(self):
        return {
            "id": self.id,
            "note": self.note.to_dict() if self.note else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
