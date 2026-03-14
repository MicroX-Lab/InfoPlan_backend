# encoding: utf-8
"""注册所有 Blueprint"""


def register_blueprints(app):
    from app.api.auth import auth_bp
    from app.api.health import health_bp
    from app.api.notes import notes_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(health_bp)
    app.register_blueprint(notes_bp, url_prefix="/api/note")
