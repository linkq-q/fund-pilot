import sqlite3
from datetime import datetime
from pathlib import Path

from config import CASH_POOL_INITIAL

DB_PATH = Path(__file__).resolve().parent.parent / "fundtool.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS holdings (
                fund_code TEXT PRIMARY KEY,
                fund_name TEXT,
                fund_role TEXT CHECK (fund_role IN ('底仓', '收益型')),
                buy_amount REAL,
                buy_date TEXT,
                shares REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT,
                action TEXT CHECK (action IN ('买入', '减仓')),
                amount REAL,
                date TEXT,
                reason TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fund_nav (
                fund_code TEXT,
                nav REAL,
                date TEXT,
                PRIMARY KEY (fund_code, date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cash_pool (
                total_cash REAL,
                last_updated TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cash_pool_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_amount REAL,
                reason TEXT,
                date TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_advice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                fund_code TEXT,
                branch TEXT,
                action TEXT,
                confidence REAL,
                reason TEXT,
                risk_warning TEXT,
                cash_pool_change REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_card (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                term TEXT,
                explanation TEXT,
                example TEXT
            )
            """
        )

        cur = conn.execute("SELECT COUNT(*) AS cnt FROM cash_pool")
        if cur.fetchone()["cnt"] == 0:
            conn.execute(
                "INSERT INTO cash_pool (total_cash, last_updated) VALUES (?, ?)",
                (CASH_POOL_INITIAL, datetime.now().strftime("%Y-%m-%d")),
            )


def add_holding(fund_code, fund_name, fund_role, buy_amount, buy_date, shares):
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO holdings
            (fund_code, fund_name, fund_role, buy_amount, buy_date, shares)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (fund_code, fund_name, fund_role, buy_amount, buy_date, shares),
        )


def get_all_holdings():
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM holdings ORDER BY buy_date DESC").fetchall()
    return [dict(r) for r in rows]


def get_holding(fund_code):
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM holdings WHERE fund_code = ?", (fund_code,)).fetchone()
    return dict(row) if row else None


def delete_holding(fund_code):
    with _get_conn() as conn:
        conn.execute("DELETE FROM holdings WHERE fund_code = ?", (fund_code,))


def add_transaction(fund_code, action, amount, date, reason):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO transactions (fund_code, action, amount, date, reason) VALUES (?, ?, ?, ?, ?)",
            (fund_code, action, amount, date, reason),
        )


def get_transactions(fund_code):
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE fund_code = ? ORDER BY date DESC, id DESC",
            (fund_code,),
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_nav(fund_code, nav, date):
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO fund_nav (fund_code, nav, date)
            VALUES (?, ?, ?)
            ON CONFLICT(fund_code, date) DO UPDATE SET nav = excluded.nav
            """,
            (fund_code, nav, date),
        )


def get_latest_nav(fund_code):
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM fund_nav WHERE fund_code = ? ORDER BY date DESC LIMIT 1",
            (fund_code,),
        ).fetchone()
    return dict(row) if row else None


def get_nav_history(fund_code, days):
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM fund_nav WHERE fund_code = ? ORDER BY date DESC LIMIT ?",
            (fund_code, days),
        ).fetchall()
    return [dict(r) for r in rows]


def get_cash_pool():
    with _get_conn() as conn:
        row = conn.execute("SELECT total_cash FROM cash_pool LIMIT 1").fetchone()
    return row["total_cash"] if row else 0


def update_cash_pool(change_amount, reason, date):
    with _get_conn() as conn:
        row = conn.execute("SELECT total_cash FROM cash_pool LIMIT 1").fetchone()
        current_cash = row["total_cash"] if row else CASH_POOL_INITIAL
        new_cash = current_cash + change_amount

        if row:
            conn.execute(
                "UPDATE cash_pool SET total_cash = ?, last_updated = ?",
                (new_cash, date),
            )
        else:
            conn.execute(
                "INSERT INTO cash_pool (total_cash, last_updated) VALUES (?, ?)",
                (new_cash, date),
            )

        conn.execute(
            "INSERT INTO cash_pool_log (change_amount, reason, date) VALUES (?, ?, ?)",
            (change_amount, reason, date),
        )


def get_cash_pool_log():
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM cash_pool_log ORDER BY date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


def save_daily_advice(date, fund_code, branch, action, confidence, reason, risk_warning, cash_pool_change):
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_advice
            (date, fund_code, branch, action, confidence, reason, risk_warning, cash_pool_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date, fund_code, branch, action, confidence, reason, risk_warning, cash_pool_change),
        )


def get_today_advice():
    today = datetime.now().strftime("%Y-%m-%d")
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_advice WHERE date = ? ORDER BY id DESC",
            (today,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_latest_advice(fund_code):
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM daily_advice WHERE fund_code = ? ORDER BY date DESC, id DESC LIMIT 1",
            (fund_code,),
        ).fetchone()
    return dict(row) if row else None


def save_daily_card(date, term, explanation, example):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO daily_card (date, term, explanation, example) VALUES (?, ?, ?, ?)",
            (date, term, explanation, example),
        )


def get_today_card():
    today = datetime.now().strftime("%Y-%m-%d")
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM daily_card WHERE date = ? ORDER BY id DESC LIMIT 1", (today,)).fetchone()
    return dict(row) if row else None


def get_all_cards():
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM daily_card ORDER BY date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]
