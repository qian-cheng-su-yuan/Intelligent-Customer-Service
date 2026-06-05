import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    paid_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logistics (
    order_id TEXT PRIMARY KEY,
    carrier TEXT NOT NULL,
    tracking_no TEXT NOT NULL,
    status TEXT NOT NULL,
    latest_event TEXT NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS repair_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    contact TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    amount REAL NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pending_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    risk_reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    reviewer TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT
);
"""


SEED_SQL = """
INSERT OR IGNORE INTO orders(order_id, customer_id, product_name, amount, status, paid_at)
VALUES
    ('ORD-1001', 'CUST-001', 'AI Noise Cancelling Headphones', 899.00, 'paid', '2026-05-20 10:15:00'),
    ('ORD-1002', 'CUST-001', 'Smart Keyboard', 299.00, 'shipped', '2026-05-22 09:30:00'),
    ('ORD-2001', 'CUST-002', 'Portable Monitor', 1299.00, 'paid', '2026-05-18 14:05:00');

INSERT OR IGNORE INTO logistics(order_id, carrier, tracking_no, status, latest_event)
VALUES
    ('ORD-1001', 'SF Express', 'SF123456789CN', 'in_transit', 'Package arrived at Shanghai transfer center.'),
    ('ORD-1002', 'JD Logistics', 'JD987654321CN', 'delivered', 'Package delivered to front desk.'),
    ('ORD-2001', 'YTO Express', 'YT20260601001', 'created', 'Shipment label created.');
"""


def connect(database_path: Path | str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path | str, seed: bool = False) -> None:
    with connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
        if seed:
            connection.executescript(SEED_SQL)
        connection.commit()
