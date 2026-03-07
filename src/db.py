from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Optional


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  category_id INTEGER,
  unit TEXT,
  FOREIGN KEY(category_id) REFERENCES categories(id)
);

-- Price history is recorded explicitly (works for "price changes" dashboard)
CREATE TABLE IF NOT EXISTS product_prices (
  id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL,
  price REAL NOT NULL,
  currency TEXT NOT NULL,
  effective_date TEXT NOT NULL, -- ISO date
  note TEXT,
  UNIQUE(product_id, currency, effective_date),
  FOREIGN KEY(product_id) REFERENCES products(id)
);

-- Purchases are the main "paycheck" spend entries
CREATE TABLE IF NOT EXISTS purchases (
  id INTEGER PRIMARY KEY,
  purchased_at TEXT NOT NULL, -- ISO datetime
  product_id INTEGER NOT NULL,
  category_id INTEGER, -- denormalized snapshot for convenience
  quantity REAL NOT NULL DEFAULT 1,
  unit_price REAL NOT NULL,
  currency TEXT NOT NULL,
  total REAL NOT NULL,
  note TEXT,
  FOREIGN KEY(product_id) REFERENCES products(id),
  FOREIGN KEY(category_id) REFERENCES categories(id)
);

-- Optional FX rates. Base currency is arbitrary; we store directed rates.
-- "rate" means: 1 unit of from_currency equals rate units of to_currency.
CREATE TABLE IF NOT EXISTS fx_rates (
  id INTEGER PRIMARY KEY,
  as_of TEXT NOT NULL, -- ISO date
  from_currency TEXT NOT NULL,
  to_currency TEXT NOT NULL,
  rate REAL NOT NULL,
  source TEXT NOT NULL DEFAULT 'manual',
  UNIQUE(as_of, from_currency, to_currency)
);
"""


@dataclass(frozen=True)
class DBConfig:
    path: str


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def connect(cfg: DBConfig) -> sqlite3.Connection:
    _ensure_parent_dir(cfg.path)
    con = sqlite3.connect(cfg.path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_SQL)
    con.commit()


def _exec(con: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> None:
    con.execute(sql, tuple(params))
    con.commit()


def _query(con: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    cur = con.execute(sql, tuple(params))
    return list(cur.fetchall())


def upsert_category(con: sqlite3.Connection, name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty")
    con.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,))
    row = con.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
    con.commit()
    return int(row["id"])


def list_categories(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return _query(con, "SELECT id, name FROM categories ORDER BY name")


def upsert_product(con: sqlite3.Connection, name: str, category_id: Optional[int], unit: Optional[str]) -> int:
    name = name.strip()
    unit = (unit or "").strip() or None
    if not name:
        raise ValueError("Product name cannot be empty")
    con.execute("INSERT OR IGNORE INTO products(name, category_id, unit) VALUES (?,?,?)", (name, category_id, unit))
    # If it already exists, update optional fields when provided
    if category_id is not None or unit is not None:
        con.execute(
            """
            UPDATE products
            SET category_id = COALESCE(?, category_id),
                unit = COALESCE(?, unit)
            WHERE name = ?
            """,
            (category_id, unit, name),
        )
    row = con.execute("SELECT id FROM products WHERE name = ?", (name,)).fetchone()
    con.commit()
    return int(row["id"])


def list_products(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return _query(
        con,
        """
        SELECT p.id, p.name, p.unit, p.category_id, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        ORDER BY p.name
        """,
    )


def record_price(
    con: sqlite3.Connection,
    product_id: int,
    price: float,
    currency: str,
    effective_date_: date,
    note: Optional[str] = None,
) -> None:
    currency = currency.strip().upper()
    if not currency:
        raise ValueError("Currency cannot be empty")
    _exec(
        con,
        """
        INSERT OR REPLACE INTO product_prices(product_id, price, currency, effective_date, note)
        VALUES (?,?,?,?,?)
        """,
        (product_id, float(price), currency, effective_date_.isoformat(), (note or "").strip() or None),
    )


def list_prices(con: sqlite3.Connection, product_id: Optional[int] = None) -> list[sqlite3.Row]:
    if product_id is None:
        return _query(
            con,
            """
            SELECT pp.*, p.name AS product_name
            FROM product_prices pp
            JOIN products p ON p.id = pp.product_id
            ORDER BY p.name, pp.currency, pp.effective_date
            """,
        )
    return _query(
        con,
        """
        SELECT pp.*, p.name AS product_name
        FROM product_prices pp
        JOIN products p ON p.id = pp.product_id
        WHERE pp.product_id = ?
        ORDER BY pp.currency, pp.effective_date
        """,
        (product_id,),
    )


def add_purchase(
    con: sqlite3.Connection,
    purchased_at: datetime,
    product_id: int,
    category_id: Optional[int],
    quantity: float,
    unit_price: float,
    currency: str,
    note: Optional[str] = None,
) -> None:
    currency = currency.strip().upper()
    qty = float(quantity)
    up = float(unit_price)
    total = qty * up
    _exec(
        con,
        """
        INSERT INTO purchases(purchased_at, product_id, category_id, quantity, unit_price, currency, total, note)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            purchased_at.isoformat(timespec="seconds"),
            product_id,
            category_id,
            qty,
            up,
            currency,
            total,
            (note or "").strip() or None,
        ),
    )


def list_purchases(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return _query(
        con,
        """
        SELECT pu.*,
               p.name AS product_name,
               c.name AS category_name
        FROM purchases pu
        JOIN products p ON p.id = pu.product_id
        LEFT JOIN categories c ON c.id = pu.category_id
        ORDER BY pu.purchased_at DESC, pu.id DESC
        """,
    )


def upsert_fx_rate(
    con: sqlite3.Connection,
    as_of_: date,
    from_currency: str,
    to_currency: str,
    rate: float,
    source: str = "manual",
) -> None:
    fc = from_currency.strip().upper()
    tc = to_currency.strip().upper()
    if not fc or not tc or fc == tc:
        raise ValueError("Currencies must be non-empty and different")
    _exec(
        con,
        """
        INSERT OR REPLACE INTO fx_rates(as_of, from_currency, to_currency, rate, source)
        VALUES (?,?,?,?,?)
        """,
        (as_of_.isoformat(), fc, tc, float(rate), source),
    )


def get_fx_rate(con: sqlite3.Connection, as_of_: date, from_currency: str, to_currency: str) -> Optional[float]:
    fc = from_currency.strip().upper()
    tc = to_currency.strip().upper()
    if fc == tc:
        return 1.0
    row = con.execute(
        """
        SELECT rate
        FROM fx_rates
        WHERE as_of = ? AND from_currency = ? AND to_currency = ?
        """,
        (as_of_.isoformat(), fc, tc),
    ).fetchone()
    if row:
        return float(row["rate"])
    # Try inverse if present
    row2 = con.execute(
        """
        SELECT rate
        FROM fx_rates
        WHERE as_of = ? AND from_currency = ? AND to_currency = ?
        """,
        (as_of_.isoformat(), tc, fc),
    ).fetchone()
    if row2:
        inv = float(row2["rate"])
        if inv != 0:
            return 1.0 / inv
    return None

