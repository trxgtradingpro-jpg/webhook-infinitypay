import sqlite3
from datetime import datetime

DB_PATH = "database.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # TABELA DE PEDIDOS (email antes do pagamento)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            reference TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # TABELA DE TRANSAÇÕES PROCESSADAS
    c.execute("""
        CREATE TABLE IF NOT EXISTS processed (
            transaction_nsu TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print("🗄️ BANCO INICIALIZADO COM SUCESSO")


# ======================================================
# ORDERS
# ======================================================

def salvar_order_email(reference, email):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "INSERT OR REPLACE INTO orders (reference, email, created_at) VALUES (?, ?, ?)",
        (reference, email, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    print(f"💾 BANCO | SALVO reference={reference} email={email}")


def buscar_email(reference):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "SELECT email FROM orders WHERE reference = ?",
        (reference,)
    )

    row = c.fetchone()
    conn.close()

    return row[0] if row else None


# ======================================================
# TRANSAÇÕES PROCESSADAS
# ======================================================

def transacao_ja_processada(transaction_nsu):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM processed WHERE transaction_nsu = ?",
        (transaction_nsu,)
    )

    exists = c.fetchone() is not None
    conn.close()

    return exists


def marcar_processada(transaction_nsu):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "INSERT OR IGNORE INTO processed (transaction_nsu, created_at) VALUES (?, ?)",
        (transaction_nsu, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    print(f"✅ TRANSAÇÃO MARCADA COMO PROCESSADA: {transaction_nsu}")
