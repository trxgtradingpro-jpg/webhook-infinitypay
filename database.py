import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

# ======================================================
# CONEXÃO
# ======================================================

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ======================================================
# INIT / MIGRATIONS
# ======================================================

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # TABELA DE PEDIDOS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            plano TEXT NOT NULL,
            nome TEXT,
            email TEXT NOT NULL,
            telefone TEXT,
            status TEXT NOT NULL DEFAULT 'PENDENTE',
            email_tentativas INTEGER DEFAULT 0,
            erro_email TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # TRANSAÇÕES PROCESSADAS (WEBHOOK)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_transactions (
            transaction_nsu TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("🗄️ POSTGRES OK (estrutura completa)", flush=True)

# ======================================================
# PEDIDOS
# ======================================================

def salvar_order(order_id, plano, nome, email, telefone):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (order_id, plano, nome, email, telefone)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, plano, nome, email, telefone))

    conn.commit()
    cur.close()
    conn.close()


def buscar_order_por_id(order_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT order_id, plano, nome, email, telefone,
               status, email_tentativas, erro_email, created_at
        FROM orders
        WHERE order_id = %s
    """, (order_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "order_id": row[0],
        "plano": row[1],
        "nome": row[2],
        "email": row[3],
        "telefone": row[4],
        "status": row[5],
        "email_tentativas": row[6],
        "erro_email": row[7],
        "created_at": row[8]
    }


def marcar_order_processada(order_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = 'PAGO'
        WHERE order_id = %s
    """, (order_id,))

    conn.commit()
    cur.close()
    conn.close()


def registrar_falha_email(order_id, tentativas, erro):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET email_tentativas = %s,
            erro_email = %s
        WHERE order_id = %s
    """, (tentativas, erro, order_id))

    conn.commit()
    cur.close()
    conn.close()

# ======================================================
# TRANSAÇÕES / WEBHOOK
# ======================================================

def transacao_ja_processada(transaction_nsu):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM processed_transactions
        WHERE transaction_nsu = %s
    """, (transaction_nsu,))

    existe = cur.fetchone() is not None
    cur.close()
    conn.close()

    return existe


def marcar_transacao_processada(transaction_nsu):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO processed_transactions (transaction_nsu)
        VALUES (%s)
        ON CONFLICT DO NOTHING
    """, (transaction_nsu,))

    conn.commit()
    cur.close()
    conn.close()

# ======================================================
# DASHBOARD
# ======================================================

def listar_pedidos():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT order_id, nome, email, telefone,
               plano, status, created_at
        FROM orders
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def buscar_pedido_detalhado(order_id):
    return buscar_order_por_id(order_id)


def obter_estatisticas():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'PAGO'")
    pagos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'PENDENTE'")
    pendentes = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total": total,
        "pagos": pagos,
        "pendentes": pendentes
    }
