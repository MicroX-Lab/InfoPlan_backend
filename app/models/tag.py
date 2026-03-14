# encoding: utf-8
from app.extensions import db

# 博主-标签 多对多关联表
blogger_tags = db.Table(
    "blogger_tags",
    db.Column("blogger_id", db.Integer, db.ForeignKey("bloggers.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)

# 笔记-标签 多对多关联表
note_tags = db.Table(
    "note_tags",
    db.Column("note_id", db.Integer, db.ForeignKey("notes.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_auto_generated = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("name", "user_id", name="uq_tag_user"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_auto_generated": self.is_auto_generated,
        }
