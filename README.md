# 🚀 NoteFlow Backend API

A high-performance, secure, and scalable RESTful API built with **FastAPI** to power the NoteFlow application.

---

## 🛠️ Features

- ✅ **JWT Authentication**: Secure, stateless token-based access.
- ✅ **PostgreSQL Integration**: Production-ready data persistence with SQLAlchemy.
- ✅ **Encrypted Vault**: API-level content masking for protected notes.
- ✅ **Real-time Search**: Optimized filtering across multiple fields.
- ✅ **Note Sharing**: Granular access control for collaborative note-taking.

---

## 📡 Core Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a new user account |
| `POST` | `/login` | Authenticate and receive a JWT access token |
| `GET` | `/notes` | Retrieve all notes (paginated) |
| `POST` | `/notes` | Create a new note |
| `GET` | `/notes/{id}` | Get a specific note by ID |
| `PUT` | `/notes/{id}` | Update an existing note |
| `DELETE` | `/notes/{id}` | Delete a note and its shares |
| `POST` | `/notes/{id}/share` | Share a note with another user |
| `POST` | `/notes/{id}/lock` | Secure a note with a secondary password |
| `POST` | `/notes/{id}/verify-lock` | Verify password to unlock note content |

---

## 🚀 Deployment (Render.com)

1.  **Build Command**: `pip install -r requirements.txt`
2.  **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3.  **Required Environment Variables**:
    - `DATABASE_URL`: Your PostgreSQL connection string.
    - `SECRET_KEY`: A long, random string for JWT signing.
    - `TOKEN_EXPIRY_MINUTES`: JWT lifetime (default: 1440).

---

## 💻 Local Development

1.  **Clone the repo and navigate to backend**:
    ```bash
    cd backend
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the server**:
    ```bash
    python main.py
    ```
    The API will be available at `http://localhost:8000`.

---

## 👤 Author
**Kabra Gautam**  
*Full Stack Developer*
