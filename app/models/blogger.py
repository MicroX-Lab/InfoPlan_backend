# encoding: utf-8
from datetime import datetime

from app.extensions import db
from app.models.tag import blogger_tags


class Blogger(db.Model):
    __tablename__ = "bloggers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    xhs_user_id = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    fans_count = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "xhs_user_id", name="uq_user_blogger"),
    )

    # 关系
    tags = db.relationship("Tag", secondary=blogger_tags, backref="bloggers", lazy="dynamic")
    notes = db.relationship("Note", backref="blogger", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "xhs_user_id": self.xhs_user_id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "description": self.description,
            "fans_count": self.fans_count,
            "tags": [t.to_dict() for t in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
