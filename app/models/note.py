# encoding: utf-8
from datetime import datetime

from app.extensions import db
from app.models.tag import note_tags


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    note_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    blogger_id = db.Column(db.Integer, db.ForeignKey("bloggers.id"), nullable=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    note_type = db.Column(db.String(50))
    liked_count = db.Column(db.Integer, default=0)
    collected_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    tags_json = db.Column(db.Text)
    image_urls_json = db.Column(db.Text)
    note_url = db.Column(db.String(500))
    upload_time = db.Column(db.String(100))
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    summary = db.Column(db.Text)

    # 关系
    tags = db.relationship("Tag", secondary=note_tags, backref="notes", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "note_id": self.note_id,
            "title": self.title,
            "description": self.description,
            "note_type": self.note_type,
            "liked_count": self.liked_count,
            "collected_count": self.collected_count,
            "comment_count": self.comment_count,
            "note_url": self.note_url,
            "upload_time": self.upload_time,
            "summary": self.summary,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }
