import psycopg2
import os

print("📦 DATABASE.PY CARREGADO")

DATABASE_URL = os.environ.get("DATABASE_URL")

# FLAG DE RESET (IMPORTANTE)
RESET_DB = os.environ.get("RESET_DB") == "1"


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def reset_db_se_necessario():
    if not RESET_DB:
        return

    print("⚠️ RESET_DB ATIVO — APAGANDO TABELAS", flush=True)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS orders;")
    cur.execute("DROP TABLE IF EXISTS processed;")

    conn.commit()
    cur.close()
    conn.close()

    print("🔥 BANCO RESETADO COM SUCESSO", flush=True)


def init_db():
    reset_db_se_necessario()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            plano TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDENTE',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed (
            transaction_nsu TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("🗄️ POSTGRES OK", flush=True)


def salvar_order(order_id, plano, email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (order_id, plano, email)
        VALUES (%s, %s, %s)
    """, (order_id,_
