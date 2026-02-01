import sqlite3

DB_NAME = "orders.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_nsu TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS processed (
            transaction_nsu TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


def salvar_order_email(order_nsu, email):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO orders (order_nsu, email) VALUES (?, ?)",
        (order_nsu, email)
    )
    conn.commit()
    conn.close()


def buscar_email(order_nsu):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT email FROM orders WHERE order_nsu = ?",
        (order_nsu,)
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def transacao_ja_processada(transaction_nsu):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT 1 FROM processed WHERE transaction_nsu = ?",
        (transaction_nsu,)
    )
    existe = c.fetchone() is not None
    conn.close()
    return existe


def marcar_processada(transaction_nsu):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO processed (transaction_nsu) VALUES (?)",
        (transaction_nsu,)
    )
    conn.commit()
    conn.close()
