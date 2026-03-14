# encoding: utf-8
from datetime import datetime

from app.extensions import db


class Digest(db.Model):
    __tablename__ = "digests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    digest_json = db.Column(db.Text)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "digest": json.loads(self.digest_json) if self.digest_json else None,
        }
