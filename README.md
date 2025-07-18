# AI Chat Backend

A Flask-based backend for a multi-model AI chat application, supporting user authentication, conversation management, and integration with GPT, Claude, and Gemini models (mock and real).

---

## Project Structure

```
.
├── app/
│   ├── __init__.py         # App factory, config, blueprint registration
│   ├── models.py           # SQLAlchemy models: User, Conversation, ChatMessage
│   ├── routes/
│   │   ├── auth.py         # Auth endpoints: signup, login, refresh
│   │   └── chat.py         # Chat endpoints: start, chat, history, list
│   └── utils/
│       ├── mock_claude.json  # Mock responses for Claude
│       └── mock_gemini.json  # Mock responses for Gemini
├── migrations/             # Alembic migration scripts
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build instructions
├── docker-compose.yml      # Multi-container orchestration (web + db)
└── run.py                  # App entry point
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd aichat-backend
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```
DATABASE_URL=postgresql://chatuser:chatpass@db:5432/chathistory
SECRET_KEY=your_flask_secret
JWT_SECRET_KEY=your_jwt_secret
GEMINI_API_KEY=your_gemini_api_key   # Optional, only needed for real Gemini responses
```

### 3. Build and Run with Docker

```bash
docker-compose up --build
```

- The backend will be available at `http://localhost:5000`
- The PostgreSQL database will be available internally as `db:5432`

### 4. Database Migrations

If running locally (not in Docker), initialize the database:

```bash
flask db upgrade
```

---

## Notes

- **Rate Limit**: Each user can send up to 20 messages per day.
- **Mock Responses**: GPT and Claude always return mock responses. Gemini uses the real API if `GEMINI_API_KEY` is set, otherwise returns mock responses.
- **CORS**: Enabled for all origins.

---