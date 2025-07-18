from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import ChatMessage, User, Conversation
from app import db
from datetime import datetime, date
import os
import json
import google.generativeai as genai


MOCK_CLAUDE_PATH = os.path.join(os.path.dirname(__file__), '../utils/mock_claude.json')
MOCK_GEMINI_PATH = os.path.join(os.path.dirname(__file__), '../utils/mock_gemini.json')

def load_mock_responses(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return []

MOCK_CLAUDE_RESPONSES = load_mock_responses(MOCK_CLAUDE_PATH)
MOCK_GEMINI_RESPONSES = load_mock_responses(MOCK_GEMINI_PATH)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_mock_response(model, prompt):
    if model == "gpt":
        return f"[GPT] Echo: {prompt}"
    elif model == "claude":
        for item in MOCK_CLAUDE_RESPONSES:
            if item["prompt"].lower() == prompt.lower():
                return item["response"]
        return "[Claude] Sorry, I don't have a mock response for that prompt."
    elif model == "gemini":
        if not GEMINI_API_KEY:
            return "[Gemini] API key not configured."
        try:
            gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Gemini] API error: {str(e)}"
    else:
        return "Unknown model"

def estimate_tokens(text):
    # Simple proxy: 1 token per word
    return len(text.split())

def check_daily_limit(username):
    now = datetime.utcnow()
    start_of_day = datetime(now.year, now.month, now.day)

    user = User.query.filter_by(username=username).first()
    if not user:
        return {"error": "User not found"}, 404, None

    message_count = ChatMessage.query.filter(
        ChatMessage.user_id == user.id,
        ChatMessage.timestamp >= start_of_day,
        ChatMessage.timestamp <= now
    ).count()

    if message_count >= 20:
        return {"message": "Rate limit reached"}, 429, user

    return {"message": "OK"}, 200, user

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/start_conversation", methods=["POST", "OPTIONS"])
@jwt_required()
def start_conversation():
    if request.method == "OPTIONS":
        return '', 204

    username = get_jwt_identity()

    limit_status, status_code, user = check_daily_limit(username)
    if status_code != 200:
        return jsonify(limit_status), status_code

    # Find the next conversation_number for this user
    max_conv = db.session.query(db.func.max(Conversation.conversation_number)).filter_by(user_id=user.id).scalar()
    next_number = (max_conv or 0) + 1
    conversation = Conversation(user_id=user.id, conversation_number=next_number)
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"conversation_number": conversation.conversation_number}), 201

@chat_bp.route("/", methods=["POST", "OPTIONS"])
@jwt_required()
def chat():
    if request.method == "OPTIONS":
        return '', 204

    username = get_jwt_identity()
    limit_status, status_code, user = check_daily_limit(username)
    if status_code != 200:
        return jsonify(limit_status), status_code

    data = request.get_json()
    model = data.get("model")
    prompt = data.get("prompt")
    conversation_number = data.get("conversation_number")
    if not model or not prompt or not conversation_number:
        return jsonify({"msg": "Missing model, prompt, or conversation_number"}), 400

    conversation = Conversation.query.filter_by(user_id=user.id, conversation_number=conversation_number).first()
    if not conversation:
        return jsonify({"msg": "Conversation not found"}), 404

    # Simulate model response
    response = get_mock_response(model.lower(), prompt)

    # Estimate tokens
    prompt_tokens = estimate_tokens(prompt)
    response_tokens = estimate_tokens(response)

    # Store chat log
    chat_msg = ChatMessage(
        user_id=user.id,
        conversation_id=conversation.id,
        model=model,
        prompt=prompt,
        response=response,
        timestamp=datetime.utcnow()
    )
    db.session.add(chat_msg)
    db.session.commit()

    return jsonify({
        "model": model,
        "prompt": prompt,
        "response": response,
        "timestamp": chat_msg.timestamp.isoformat(),
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "conversation_number": conversation_number
    }), 200

@chat_bp.route("/history", methods=["GET", "OPTIONS"])
@jwt_required()
def chat_history():
    if request.method == "OPTIONS":
        return '', 204
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    conversation_number = request.args.get("conversation_number", type=int)
    query = ChatMessage.query.join(Conversation).filter(ChatMessage.user_id == user.id)
    if conversation_number:
        query = query.filter(Conversation.conversation_number == conversation_number, Conversation.user_id == user.id)
    messages = query.order_by(ChatMessage.timestamp.asc()).all()
    history = [
        {
            "model": msg.model,
            "prompt": msg.prompt,
            "response": msg.response,
            "timestamp": msg.timestamp.isoformat(),
            "conversation_number": msg.conversation.conversation_number
        }
        for msg in messages
    ]
    return jsonify(history), 200

@chat_bp.route("/conversations", methods=["GET", "OPTIONS"])
@jwt_required()
def list_conversations():
    if request.method == "OPTIONS":
        return '', 204
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    conversations = (
        Conversation.query
        .filter_by(user_id=user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    numbers = [c.conversation_number for c in conversations]
    return jsonify(numbers), 200
