import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ================= ORDERS =================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            plano TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # ================= PAYMENTS =================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            transaction_nsu TEXT UNIQUE,
            plano TEXT,
            email TEXT,
            valor INTEGER,
            metodo TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # ================= PROCESSED =================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed (
            transaction_nsu TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("🗄️ POSTGRES CONECTADO E TABELAS OK", flush=True)


# ================= ORDERS =================

def salvar_order(plano, email, telefone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (plano, email, telefone) VALUES (%s, %s, %s)",
        (plano, email, telefone)
    )
    conn.commit()
    cur.close()
    conn.close()


def buscar_email_pendente(plano):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT email
        FROM orders
        WHERE plano = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (plano,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def listar_orders(limit=200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT plano, email, telefone, created_at
        FROM orders
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ================= PAYMENTS =================

def salvar_pagamento(transaction_nsu, plano, email, valor, metodo):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO payments
        (transaction_nsu, plano, email, valor, metodo, status)
        VALUES (%s, %s, %s, %s, %s, 'Pago')
        ON CONFLICT (transaction_nsu) DO NOTHING
    """, (transaction_nsu, plano, email, valor, metodo))
    conn.commit()
    cur.close()
    conn.close()


def listar_pagamentos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT plano, email, valor, metodo, status, created_at
        FROM payments
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ================= PROCESSED =================

def transacao_ja_processada(transaction_nsu):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM processed WHERE transaction_nsu = %s",
        (transaction_nsu,)
    )
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def marcar_processada(transaction_nsu):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO processed (transaction_nsu)
        VALUES (%s)
        ON CONFLICT DO NOTHING
    """, (transaction_nsu,))
    conn.commit()
    cur.close()
    conn.close()


# ================= DASHBOARD =================

def dashboard_stats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM payments WHERE status='Pago'")
    total_vendas = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(valor),0) FROM payments WHERE status='Pago'")
    total_faturado = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM payments WHERE metodo='pix'")
    pagamentos_pix = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM payments WHERE metodo <> 'pix'")
    pagamentos_cartao = cur.fetchone()[0]

    cur.execute("""
        SELECT plano, COUNT(*)
        FROM payments
        GROUP BY plano
    """)
    planos = cur.fetchall()
    vendas_por_plano = {p[0]: p[1] for p in planos}

    cur.execute("""
        SELECT DATE(created_at), SUM(valor)
        FROM payments
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)
    dias = cur.fetchall()

    faturamento_labels = [str(d[0]) for d in dias]
    faturamento_values = [d[1] for d in dias]

    cur.close()
    conn.close()

    return {
        "total_vendas": total_vendas,
        "total_faturado": total_faturado,
        "pagamentos_pix": pagamentos_pix,
        "pagamentos_cartao": pagamentos_cartao,
        "planos_labels": list(vendas_por_plano.keys()),
        "planos_values": list(vendas_por_plano.values()),
        "faturamento_labels": faturamento_labels,
        "faturamento_values": faturamento_values
    }
