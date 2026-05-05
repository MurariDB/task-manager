# ✅ Task Manager REST API

A production-ready REST API built with **Python + FastAPI + SQLite** featuring user authentication and full task management.

---

## 🚀 Features

- 🔐 **JWT Authentication** — Secure register/login with token-based auth
- 📋 **Full CRUD** — Create, Read, Update, Delete tasks
- 🔍 **Filtering** — Filter tasks by status or priority
- 📊 **Stats Dashboard** — Completion rate & priority breakdown
- 📖 **Auto API Docs** — Interactive Swagger UI at `/docs`
- 🗄️ **SQLite Database** — Zero setup required

---

## 🛠️ Tech Stack

| Tool       | Purpose                  |
|------------|--------------------------|
| Python 3.9+| Core language            |
| FastAPI    | Web framework            |
| SQLite     | Database                 |
| JWT (Jose) | Authentication tokens    |
| Passlib    | Password hashing (bcrypt)|
| Uvicorn    | ASGI server              |

---

## ⚡ Quick Start

### 1. Clone & Enter the Folder
```bash
git clone <your-repo-url>
cd task-manager-api
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
python main.py
```

Server starts at → **http://localhost:8000**  
Interactive API docs → **http://localhost:8000/docs** 🎉

---

## 📡 API Endpoints

### Auth
| Method | Endpoint          | Description              | Auth Required |
|--------|-------------------|--------------------------|---------------|
| POST   | `/auth/register`  | Create a new account     | ❌            |
| POST   | `/auth/login`     | Login & get JWT token    | ❌            |
| GET    | `/auth/me`        | Get current user profile | ✅            |

### Tasks
| Method | Endpoint               | Description                          | Auth Required |
|--------|------------------------|--------------------------------------|---------------|
| POST   | `/tasks`               | Create a new task                    | ✅            |
| GET    | `/tasks`               | Get all tasks (with optional filters)| ✅            |
| GET    | `/tasks/{id}`          | Get a single task                    | ✅            |
| PUT    | `/tasks/{id}`          | Update a task                        | ✅            |
| DELETE | `/tasks/{id}`          | Delete a task                        | ✅            |
| GET    | `/tasks/stats/summary` | Get task statistics                  | ✅            |

---

## 🧪 Example Usage

### Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "mypassword"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=john&password=mypassword"
```

### Create a Task (use token from login)
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Study FastAPI", "priority": "high", "due_date": "2024-12-31"}'
```

### Filter Tasks by Status
```bash
curl http://localhost:8000/tasks?status=pending \
  -H "Authorization: Bearer <your-token>"
```

---

## 📁 Project Structure

```
task-manager-api/
│
├── main.py           # All routes, models, and logic
├── requirements.txt  # Python dependencies
├── README.md         # Project documentation
└── tasks.db          # SQLite database (auto-created on first run)
```

---

## 💡 What You'll Learn from This Project

- ✅ How REST APIs work (GET, POST, PUT, DELETE)
- ✅ How JWT authentication works
- ✅ How to hash & verify passwords
- ✅ How to use SQLite with raw SQL queries
- ✅ How to structure a Python backend project
- ✅ How to read auto-generated API documentation

---

## 🔮 Ideas to Extend This Project

- [ ] Add task **categories/labels**
- [ ] Send **email reminders** for due tasks (using SMTP)
- [ ] Add **pagination** for tasks list
- [ ] Deploy to **Render / Railway / Heroku** (free hosting)
- [ ] Build a **frontend** with React or simple HTML

---

## 🌟 Why This Project Gets You Hired

Interviewers look for:
1. **REST API design** — covered ✅
2. **Authentication understanding** — JWT covered ✅
3. **Database interaction** — SQL covered ✅
4. **Clean code & structure** — documented & organized ✅
5. **Error handling** — HTTP exceptions covered ✅

---

Made with ❤️ using FastAPI
