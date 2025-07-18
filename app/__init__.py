from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask_cors import CORS


db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")


    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    migrate = Migrate(app, db)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'msg': 'Rate limit reacheded'}), 429

    return app
