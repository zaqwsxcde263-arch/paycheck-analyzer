"""Database connection, schema, and CRUD helpers."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DATABASE, DEFAULT_CURRENCY


def get_db_path():
    return DATABASE


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id)
            );
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                price REAL NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(id),
                category_id INTEGER NOT NULL REFERENCES categories(id),
                quantity INTEGER NOT NULL
            );
        """)
        cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("currency",))
        if cur.fetchone() is None:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                ("currency", DEFAULT_CURRENCY),
            )


def get_setting(key: str) -> str | None:
    with get_db() as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


# --- Categories ---
def list_categories():
    with get_db() as conn:
        cur = conn.execute("SELECT id, name FROM categories ORDER BY name")
        return [dict(row) for row in cur.fetchall()]


def get_category(category_id: int) -> dict | None:
    with get_db() as conn:
        cur = conn.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_category(name: str) -> int:
    with get_db() as conn:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        return cur.lastrowid


def update_category(category_id: int, name: str):
    with get_db() as conn:
        conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))


def delete_category(category_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# --- Products ---
def list_products(category_id: int | None = None):
    with get_db() as conn:
        if category_id is not None:
            cur = conn.execute(
                "SELECT p.id, p.name, p.category_id, c.name AS category_name FROM products p JOIN categories c ON p.category_id = c.id WHERE p.category_id = ? ORDER BY p.name",
                (category_id,),
            )
        else:
            cur = conn.execute(
                "SELECT p.id, p.name, p.category_id, c.name AS category_name FROM products p JOIN categories c ON p.category_id = c.id ORDER BY c.name, p.name"
            )
        return [dict(row) for row in cur.fetchall()]


def get_product(product_id: int) -> dict | None:
    with get_db() as conn:
        cur = conn.execute(
            "SELECT p.id, p.name, p.category_id, c.name AS category_name FROM products p JOIN categories c ON p.category_id = c.id WHERE p.id = ?",
            (product_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_product(name: str, category_id: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, category_id) VALUES (?, ?)",
            (name, category_id),
        )
        return cur.lastrowid


def update_product(product_id: int, name: str, category_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE products SET name = ?, category_id = ? WHERE id = ?",
            (name, category_id, product_id),
        )


def delete_product(product_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def get_category_ids_set() -> set[int]:
    with get_db() as conn:
        cur = conn.execute("SELECT id FROM categories")
        return {row[0] for row in cur.fetchall()}


def get_product_ids_set() -> set[int]:
    with get_db() as conn:
        cur = conn.execute("SELECT id FROM products")
        return {row[0] for row in cur.fetchall()}


def get_product_to_category() -> dict[int, int]:
    with get_db() as conn:
        cur = conn.execute("SELECT id, category_id FROM products")
        return {row[0]: row[1] for row in cur.fetchall()}


# --- Costs ---
def insert_costs(items: list[dict]):
    with get_db() as conn:
        for item in items:
            conn.execute(
                "INSERT INTO costs (date, price, product_id, category_id, quantity) VALUES (?, ?, ?, ?, ?)",
                (
                    item["date"],
                    item["price"],
                    item["product_id"],
                    item["category_id"],
                    item["quantity"],
                ),
            )


def count_costs() -> int:
    with get_db() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM costs")
        return cur.fetchone()[0]


def stats_by_month():
    with get_db() as conn:
        cur = conn.execute("""
            SELECT strftime('%Y-%m', date) AS period, SUM(price * quantity) AS total
            FROM costs GROUP BY period ORDER BY period DESC LIMIT 24
        """)
        return [dict(row) for row in cur.fetchall()]


def stats_by_category():
    with get_db() as conn:
        cur = conn.execute("""
            SELECT c.id, c.name AS category_name, SUM(co.price * co.quantity) AS total
            FROM costs co JOIN categories c ON co.category_id = c.id
            GROUP BY c.id ORDER BY total DESC
        """)
        return [dict(row) for row in cur.fetchall()]


def stats_by_week():
    with get_db() as conn:
        cur = conn.execute("""
            SELECT strftime('%Y-%W', date) AS period, SUM(price * quantity) AS total
            FROM costs GROUP BY period ORDER BY period DESC LIMIT 52
        """)
        return [dict(row) for row in cur.fetchall()]


def product_trends():
    """Per-product stats over time: product name, month, avg price, min, max, total quantity."""
    with get_db() as conn:
        cur = conn.execute("""
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                c.name AS category_name,
                strftime('%Y-%m', co.date) AS period,
                AVG(co.price) AS avg_price,
                MIN(co.price) AS min_price,
                MAX(co.price) AS max_price,
                SUM(co.quantity) AS total_quantity
            FROM costs co
            JOIN products p ON co.product_id = p.id
            JOIN categories c ON co.category_id = c.id
            GROUP BY p.id, period
            ORDER BY p.name, period DESC
        """)
        return [dict(row) for row in cur.fetchall()]
