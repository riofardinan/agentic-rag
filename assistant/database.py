import json
import sqlite3
import textwrap

from assistant import config

SAMPLE_EMPLOYEES = [
    # (id, nama, jabatan, departemen, sisa cuti tahunan)
    ("EMP001", "Budi Santoso", "Software Engineer", "Engineering", 8),
    ("EMP002", "Rina Wulandari", "HR Specialist", "People & Culture", 10),
]


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row  # hasil query bisa diakses seperti dict
    return connection


def init_database():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT,
                position TEXT,
                department TEXT,
                leave_balance INTEGER
            );
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                start_date TEXT,
                end_date TEXT,
                days INTEGER,
                reason TEXT,
                status TEXT DEFAULT 'menunggu persetujuan atasan',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                problem TEXT,
                status TEXT DEFAULT 'baru',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                employee_id TEXT,
                title TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                role TEXT,
                content TEXT,
                steps TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        db.executemany("INSERT OR IGNORE INTO employees VALUES (?, ?, ?, ?, ?)", SAMPLE_EMPLOYEES)


def list_employees() -> list[sqlite3.Row]:
    with connect() as db:
        return db.execute("SELECT * FROM employees ORDER BY id").fetchall()


def get_employee(employee_id: str) -> sqlite3.Row:
    with connect() as db:
        return db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()


def add_leave_request(employee_id: str, start_date: str, end_date: str, days: int, reason: str) -> int:
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO leave_requests (employee_id, start_date, end_date, days, reason) VALUES (?, ?, ?, ?, ?)",
            (employee_id, start_date, end_date, days, reason),
        )
        return cursor.lastrowid


def add_it_ticket(employee_id: str, problem: str) -> int:
    with connect() as db:
        cursor = db.execute("INSERT INTO it_tickets (employee_id, problem) VALUES (?, ?)", (employee_id, problem))
        return cursor.lastrowid


def save_message(thread_id: str, employee_id: str, role: str, content: str, steps: list[str]):
    # Pesan pertama sebuah percakapan selalu pertanyaan pengguna, jadi pertanyaan itu menjadi judulnya
    title = textwrap.shorten(content, width=config.CHAT_TITLE_LENGTH, placeholder="...")
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO conversations (thread_id, employee_id, title) VALUES (?, ?, ?)",
                   (thread_id, employee_id, title))
        db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?", (thread_id,))
        db.execute("INSERT INTO messages (thread_id, role, content, steps) VALUES (?, ?, ?, ?)",
                   (thread_id, role, content, json.dumps(steps)))


def list_conversations(employee_id: str) -> list[sqlite3.Row]:
    with connect() as db:
        return db.execute("SELECT * FROM conversations WHERE employee_id = ? ORDER BY updated_at DESC, rowid DESC",
                          (employee_id,)).fetchall()


def list_messages(thread_id: str) -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT role, content, steps FROM messages WHERE thread_id = ? ORDER BY id",
                          (thread_id,)).fetchall()
    return [{"role": row["role"], "content": row["content"], "steps": json.loads(row["steps"])} for row in rows]
