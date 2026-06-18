"""
EnglishFlow Database — SQLite
Tables: users, materials, payments
"""

import sqlite3
import os
import uuid
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(DB_DIR, "englishflow.db")


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            name TEXT,
            plan TEXT,
            access_code TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            filename TEXT,
            file_type TEXT DEFAULT 'pdf',
            plan_level TEXT DEFAULT 'todos',
            user_id INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            amount REAL,
            pix_code TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    # Migration: add user_id to materials if missing
    try:
        conn.execute("ALTER TABLE materials ADD COLUMN user_id INTEGER DEFAULT NULL REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass
    # Migration: material_progress table
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS material_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (material_id) REFERENCES materials(id)
        );
    """)
    conn.commit()
    conn.close()


# ── USER OPERATIONS ──

def create_user(telegram_id: str, name: str, plan: str) -> dict:
    """Cria usuário com código de acesso único."""
    code = str(uuid.uuid4())[:8].upper()  # Ex: A1B2C3D4
    conn = get_db()
    conn.execute(
        "INSERT INTO users (telegram_id, name, plan, access_code) VALUES (?, ?, ?, ?)",
        (telegram_id, name, plan, code)
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE access_code = ?", (code,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_code(code: str) -> dict | None:
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE access_code = ? AND active = 1", (code,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_telegram_id(tid: str) -> dict | None:
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE telegram_id = ? AND active = 1", (tid,)).fetchone()
    conn.close()
    return dict(user) if user else None


# ── MATERIAL OPERATIONS ──

def get_materials(plan: str = None, user_id: int = None) -> list[dict]:
    conn = get_db()
    if user_id:
        # Materiais do plano + materiais específicos do usuário
        rows = conn.execute(
            """SELECT * FROM materials 
               WHERE (plan_level IN ('todos', (SELECT plan FROM users WHERE id = ?)) AND user_id IS NULL)
                  OR user_id = ?
               ORDER BY created_at DESC""",
            (user_id, user_id)
        ).fetchall()
    elif plan:
        rows = conn.execute(
            "SELECT * FROM materials WHERE plan_level IN ('todos', ?) AND user_id IS NULL ORDER BY created_at DESC",
            (plan,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM materials ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_material(title: str, description: str, filename: str, file_type: str, plan_level: str, user_id: int = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO materials (title, description, filename, file_type, plan_level, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, filename, file_type, plan_level, user_id)
    )
    conn.commit()
    conn.close()


def get_all_users() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, plan, access_code FROM users WHERE active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_material(material_id: int):
    conn = get_db()
    mat = conn.execute("SELECT filename FROM materials WHERE id = ?", (material_id,)).fetchone()
    if mat and mat["filename"]:
        filepath = os.path.join(os.path.dirname(__file__), "materiais", mat["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)
    conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


# ── PAYMENT OPERATIONS ──

def create_payment(user_id: int, plan: str, amount: float, pix_code: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO payments (user_id, plan, amount, pix_code, status) VALUES (?, ?, ?, ?, 'pending')",
        (user_id, plan, amount, pix_code)
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def confirm_payment(payment_id: int):
    conn = get_db()
    conn.execute("UPDATE payments SET status = 'confirmed' WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


def get_payments_by_user(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── PROGRESS OPERATIONS ──

def toggle_material_progress(user_id: int, material_id: int) -> bool:
    """Marca/desmarca material como concluido. Retorna o novo estado."""
    conn = get_db()
    existing = conn.execute(
        "SELECT id, completed FROM material_progress WHERE user_id = ? AND material_id = ?",
        (user_id, material_id)
    ).fetchone()
    if existing:
        new_state = 0 if existing["completed"] else 1
        conn.execute(
            "UPDATE material_progress SET completed = ?, completed_at = datetime('now','localtime') WHERE id = ?",
            (new_state, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO material_progress (user_id, material_id, completed, completed_at) VALUES (?, ?, 1, datetime('now','localtime'))",
            (user_id, material_id)
        )
        new_state = True
    conn.commit()
    conn.close()
    return new_state


def get_user_progress(user_id: int) -> dict:
    """Retorna progresso do usuario: total, concluidos, porcentagem."""
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) as c FROM materials WHERE (plan_level IN ('todos', (SELECT plan FROM users WHERE id=?)) AND user_id IS NULL) OR user_id = ?",
        (user_id, user_id)
    ).fetchone()["c"]
    done = conn.execute(
        """SELECT COUNT(*) as c FROM material_progress 
           WHERE user_id = ? AND completed = 1 
           AND material_id IN (SELECT id FROM materials WHERE (plan_level IN ('todos', (SELECT plan FROM users WHERE id=?)) AND user_id IS NULL) OR user_id = ?)""",
        (user_id, user_id, user_id)
    ).fetchone()["c"]
    conn.close()
    pct = round((done / total * 100)) if total > 0 else 0
    return {"total": total, "done": done, "pct": pct}


def get_completed_materials(user_id: int) -> set:
    """Retorna IDs dos materiais concluidos."""
    conn = get_db()
    rows = conn.execute(
        "SELECT material_id FROM material_progress WHERE user_id = ? AND completed = 1",
        (user_id,)
    ).fetchall()
    conn.close()
    return {r["material_id"] for r in rows}


# ── DASHBOARD STATS ──

def get_admin_stats() -> dict:
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    users_by_plan = [dict(r) for r in conn.execute(
        "SELECT plan, COUNT(*) as count FROM users GROUP BY plan"
    ).fetchall()]
    total_materials = conn.execute("SELECT COUNT(*) as c FROM materials").fetchone()["c"]
    pending_payments = conn.execute(
        "SELECT COUNT(*) as c FROM payments WHERE status = 'pending'"
    ).fetchone()["c"]
    confirmed_payments = conn.execute(
        "SELECT COUNT(*) as c FROM payments WHERE status = 'confirmed'"
    ).fetchone()["c"]
    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'confirmed'"
    ).fetchone()["total"]
    recent_users = [dict(r) for r in conn.execute(
        "SELECT name, plan, access_code, created_at FROM users ORDER BY created_at DESC LIMIT 5"
    ).fetchall()]
    conn.close()
    return {
        "total_users": total_users,
        "users_by_plan": users_by_plan,
        "total_materials": total_materials,
        "pending_payments": pending_payments,
        "confirmed_payments": confirmed_payments,
        "total_revenue": total_revenue,
        "recent_users": recent_users
    }
