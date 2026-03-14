# encoding: utf-8
from datetime import datetime

from app.extensions import db

# 步骤-笔记 多对多关联表
step_notes = db.Table(
    "step_notes",
    db.Column("step_id", db.Integer, db.ForeignKey("plan_steps.id"), primary_key=True),
    db.Column("note_id", db.Integer, db.ForeignKey("notes.id"), primary_key=True),
    db.Column("relevance_score", db.Float, default=0.0),
)


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = db.relationship("PlanStep", backref="goal", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps.order_by(PlanStep.step_number)],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PlanStep(db.Model):
    __tablename__ = "plan_steps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    time_estimate = db.Column(db.String(100))
    status = db.Column(db.String(50), default="pending")
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    related_notes = db.relationship("Note", secondary=step_notes, backref="plan_steps")

    def to_dict(self):
        return {
            "id": self.id,
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "time_estimate": self.time_estimate,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "related_notes": [n.to_dict() for n in self.related_notes],
        }
