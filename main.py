# ============================================================
#  Task Manager REST API
#  Built with: Python + FastAPI + SQLite
#  Features: User Auth (JWT), Full CRUD, Task Filtering
# ============================================================

from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
import uvicorn

# ── App Setup ────────────────────────────────────────────────
app = FastAPI(
    title="Task Manager API",
    description="A REST API for managing personal tasks with user authentication.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Config ──────────────────────────────────────────
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ── Database Setup ───────────────────────────────────────────
DB_NAME = "tasks.db"

def get_db():
    """Returns a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row   # allows dict-like access
    return conn

def init_db():
    """Creates tables if they don't already exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            status      TEXT DEFAULT 'pending',     -- pending | completed
            priority    TEXT DEFAULT 'medium',      -- low | medium | high
            due_date    TEXT,
            user_id     INTEGER NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

# ── Pydantic Schemas (Request / Response models) ─────────────
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"   # low | medium | high
    due_date: Optional[str] = None       # Format: YYYY-MM-DD

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None         # pending | completed
    priority: Optional[str] = None
    due_date: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[str]
    user_id: int
    created_at: str
    updated_at: str

# ── Helper Functions ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency: extracts and validates the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user is None:
        raise credentials_exception
    return dict(user)

# ── Auth Routes ──────────────────────────────────────────────
@app.post("/auth/register", response_model=UserResponse, status_code=201, tags=["Auth"])
def register(user: UserCreate):
    """Register a new user account."""
    conn = get_db()

    # Check if username or email already exists
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (user.username, user.email)
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already taken.")

    hashed = hash_password(user.password)
    cursor = conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (user.username, user.email, hashed)
    )
    conn.commit()
    new_user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(new_user)


@app.post("/auth/login", response_model=Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and receive a JWT access token."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (form_data.username,)
    ).fetchone()
    conn.close()

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")

    token = create_access_token({"sub": user["id"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def get_me(current_user: dict = Depends(get_current_user)):
    """Get the currently logged-in user's profile."""
    return current_user

# ── Task Routes ──────────────────────────────────────────────
VALID_STATUSES = {"pending", "completed"}
VALID_PRIORITIES = {"low", "medium", "high"}


def validate_task_values(status: Optional[str], priority: Optional[str]):
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {', '.join(VALID_STATUSES)}")
    if priority and priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Use: {', '.join(VALID_PRIORITIES)}")


def task_to_dict(task_row: sqlite3.Row) -> dict:
    return dict(task_row)


@app.post("/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    validate_task_values(None, task.priority)
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (title, description, status, priority, due_date, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (task.title, task.description, 'pending', task.priority, task.due_date, current_user["id"])
    )
    conn.commit()
    new_task = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return task_to_dict(new_task)


@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    validate_task_values(status, priority)
    conn = get_db()
    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [current_user["id"]]
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY created_at DESC"
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    return [task_to_dict(task) for task in tasks]


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"])
    ).fetchone()
    conn.close()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task_to_dict(task)


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    if task_update.status:
        validate_task_values(task_update.status, None)
    if task_update.priority:
        validate_task_values(None, task_update.priority)

    conn = get_db()
    existing_task = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"])
    ).fetchone()
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found.")

    fields = []
    values = []
    for field_name in ["title", "description", "status", "priority", "due_date"]:
        value = getattr(task_update, field_name)
        if value is not None:
            fields.append(f"{field_name} = ?")
            values.append(value)

    if not fields:
        conn.close()
        return task_to_dict(existing_task)

    values.append(datetime.utcnow().isoformat())
    values.append(task_id)
    conn.execute(
        f"UPDATE tasks SET {', '.join(fields)}, updated_at = ? WHERE id = ?",
        tuple(values)
    )
    conn.commit()
    updated_task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return task_to_dict(updated_task)


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"])
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    result = conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, current_user["id"])
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found.")
    return Response(status_code=204)


@app.get("/tasks/stats/summary", tags=["Tasks"])
def get_task_summary(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ?",
        (current_user["id"],)
    ).fetchone()["count"]
    completed = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'completed'",
        (current_user["id"],)
    ).fetchone()["count"]
    pending = total - completed
    priority_counts = conn.execute(
        "SELECT priority, COUNT(*) AS count FROM tasks WHERE user_id = ? GROUP BY priority",
        (current_user["id"],)
    ).fetchall()
    conn.close()

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "priority_counts": {row["priority"]: row["count"] for row in priority_counts}
    }


@app.on_event("startup")
def startup_event():
    init_db()

# ── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the Task Manager API!",
        "docs": "Visit /docs for the interactive API documentation.",
        "version": "1.0.0"
    }

# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("✅ Database initialized.")
    print("🚀 Starting server at http://localhost:8000")
    print("📖 API Docs at http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
