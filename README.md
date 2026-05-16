# 🚀 NoteFlow Backend API

A high-performance, secure, and scalable RESTful API built with **FastAPI** to power the NoteFlow application.

## 🔗 Live Service
- **Base URL**: `https://noteflow-backend-b4m3.onrender.com`
- **Interactive API Docs**: `https://noteflow-backend-b4m3.onrender.com/docs`

---

## 🛠️ Features
- ✅ **JWT Authentication**: Secure token-based access.
- ✅ **PostgreSQL Integration**: Production-ready data persistence.
- ✅ **Encrypted Vault**: API-level content masking for protected notes.
- ✅ **Search & Filter**: Efficient querying for large datasets.

---

## 📡 Core Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a new user |
| `POST` | `/login` | Authenticate and receive JWT |
| `GET` | `/notes` | List all notes (supports search) |
| `POST` | `/notes` | Create a new note |
| `POST` | `/notes/{id}/verify-lock` | Unlock a protected note |
| `POST` | `/notes/{id}/share` | Share note with email |

---

## 🚀 Deployment (Render.com)
1. **Root Directory**: `backend`
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Env Vars**:
   - `DATABASE_URL`: Your PostgreSQL string.
   - `SECRET_KEY`: Long random string for JWT.

---

## 💻 Local Development
1. `pip install -r requirements.txt`
2. `python main.py` (Runs on `http://localhost:8000`)
