"""
AutoWMS — Automotive Spare Parts Warehouse Management System
Database layer: schema, seed data, and all CRUD operations.
"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wms.db")


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

def initialize_database():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    UNIQUE NOT NULL,
            contact TEXT    DEFAULT '',
            email   TEXT    DEFAULT '',
            phone   TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS parts (
            sku           TEXT    PRIMARY KEY,
            description   TEXT    NOT NULL,
            category      TEXT    DEFAULT 'General',
            unit          TEXT    DEFAULT 'EA',
            reorder_level INTEGER DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number              TEXT    UNIQUE NOT NULL,
            supplier_id            INTEGER NOT NULL REFERENCES suppliers(id),
            po_date                TEXT    NOT NULL,
            expected_delivery_date TEXT,
            status                 TEXT    DEFAULT 'Open',
            notes                  TEXT    DEFAULT '',
            created_at             TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS po_items (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id             INTEGER NOT NULL REFERENCES purchase_orders(id),
            sku               TEXT    NOT NULL REFERENCES parts(sku),
            ordered_quantity  INTEGER NOT NULL CHECK(ordered_quantity > 0),
            received_quantity INTEGER DEFAULT 0,
            unit_cost         REAL    NOT NULL CHECK(unit_cost >= 0)
        );

        CREATE TABLE IF NOT EXISTS receiving (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            receiving_number  TEXT    UNIQUE NOT NULL,
            po_id             INTEGER NOT NULL REFERENCES purchase_orders(id),
            po_item_id        INTEGER NOT NULL REFERENCES po_items(id),
            sku               TEXT    NOT NULL REFERENCES parts(sku),
            received_quantity INTEGER NOT NULL CHECK(received_quantity >= 0),
            damage_quantity   INTEGER DEFAULT 0 CHECK(damage_quantity >= 0),
            short_quantity    INTEGER DEFAULT 0 CHECK(short_quantity >= 0),
            received_date     TEXT    NOT NULL,
            qc_status         TEXT    NOT NULL CHECK(qc_status IN ('Pass','Fail')),
            location          TEXT    DEFAULT '',
            status            TEXT    DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Rejected')),
            approved_at       TEXT,
            notes             TEXT    DEFAULT '',
            created_at        TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS inventory (
            sku            TEXT    PRIMARY KEY REFERENCES parts(sku),
            current_stock  INTEGER DEFAULT 0 CHECK(current_stock >= 0),
            reserved_stock INTEGER DEFAULT 0 CHECK(reserved_stock >= 0),
            last_updated   TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS dispatch_orders (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            dispatch_number    TEXT    UNIQUE NOT NULL,
            customer           TEXT    NOT NULL,
            dispatch_date      TEXT    NOT NULL,
            status             TEXT    DEFAULT 'Pending',
            picking_confirmed  INTEGER DEFAULT 0,
            packing_confirmed  INTEGER DEFAULT 0,
            dispatch_confirmed INTEGER DEFAULT 0,
            notes              TEXT    DEFAULT '',
            created_at         TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS dispatch_items (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            dispatch_id      INTEGER NOT NULL REFERENCES dispatch_orders(id),
            sku              TEXT    NOT NULL REFERENCES parts(sku),
            ordered_quantity INTEGER NOT NULL CHECK(ordered_quantity > 0),
            picked_quantity  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            movement_date    TEXT    DEFAULT (datetime('now','localtime')),
            sku              TEXT    NOT NULL REFERENCES parts(sku),
            movement_type    TEXT    NOT NULL CHECK(movement_type IN ('IN','OUT')),
            reference_type   TEXT    NOT NULL,
            reference_number TEXT    NOT NULL,
            quantity         INTEGER NOT NULL,
            balance          INTEGER NOT NULL,
            notes            TEXT    DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Sample Data
# ─────────────────────────────────────────────────────────────────────────────

def seed_sample_data():
    conn = get_connection()
    if conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0] > 0:
        conn.close()
        return

    suppliers = [
        ("AutoParts Pro Ltd",     "John Smith",    "john@autopartspro.com",    "+1-555-0101"),
        ("OEM Supply Co.",        "Sarah Johnson", "sarah@oemsupply.com",      "+1-555-0102"),
        ("Genuine Parts Hub",     "Mike Davis",    "mike@genuinepartshub.com", "+1-555-0103"),
        ("TechAuto Distributors", "Emily Chen",    "emily@techauto.com",       "+1-555-0104"),
        ("Premier Auto Parts",    "Robert Wilson", "robert@premierauto.com",   "+1-555-0105"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO suppliers(name,contact,email,phone) VALUES(?,?,?,?)",
        suppliers
    )

    parts = [
        ("ENG-OIL-FLT-001", "Engine Oil Filter — Premium",      "Engine",       "EA",  20),
        ("ENG-AIR-FLT-002", "Air Filter — High Performance",     "Engine",       "EA",  15),
        ("ENG-CLT-001-003", "Engine Coolant 5L",                 "Engine",       "BTL", 25),
        ("BRK-PAD-FRN-004", "Front Brake Pads Set",              "Brakes",       "SET", 10),
        ("BRK-PAD-RER-005", "Rear Brake Pads Set",               "Brakes",       "SET", 10),
        ("BRK-DSC-FRN-006", "Front Brake Disc Rotor",            "Brakes",       "EA",   8),
        ("BRK-DSC-RER-007", "Rear Brake Disc Rotor",             "Brakes",       "EA",   8),
        ("SUS-SPR-FRN-008", "Front Coil Spring",                 "Suspension",   "EA",   5),
        ("SUS-SHK-FRN-009", "Front Shock Absorber",              "Suspension",   "EA",   5),
        ("SUS-SHK-REA-010", "Rear Shock Absorber",               "Suspension",   "EA",   5),
        ("ELC-BAT-12V-011", "12V Car Battery 60Ah",              "Electrical",   "EA",   5),
        ("ELC-ALT-001-012", "Alternator Assembly",               "Electrical",   "EA",   3),
        ("ELC-STR-001-013", "Starter Motor",                     "Electrical",   "EA",   3),
        ("ELC-FUS-BOX-014", "Fuse Box Assembly",                 "Electrical",   "EA",   5),
        ("COO-RAD-001-015", "Radiator Assembly",                 "Cooling",      "EA",   4),
        ("COO-THS-001-016", "Thermostat Housing",                "Cooling",      "EA",   8),
        ("COO-WPM-001-017", "Water Pump",                        "Cooling",      "EA",   6),
        ("TRN-OIL-FLT-018", "Transmission Oil Filter",           "Transmission", "EA",  10),
        ("TRN-CLT-KIT-019", "Clutch Kit Complete Set",           "Transmission", "SET",  5),
        ("FUL-PMP-001-020", "Fuel Pump Assembly",                "Fuel System",  "EA",   5),
        ("FUL-FLT-001-021", "Fuel Filter Canister",              "Fuel System",  "EA",  12),
        ("IGN-SRK-PLG-022", "Spark Plug Set (4 pcs)",            "Ignition",     "SET", 15),
        ("IGN-COL-001-023", "Ignition Coil Pack",                "Ignition",     "EA",   8),
        ("EXH-GKT-001-024", "Exhaust Manifold Gasket",           "Exhaust",      "EA",  10),
        ("STR-PMP-001-025", "Power Steering Pump",               "Steering",     "EA",   4),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO parts(sku,description,category,unit,reorder_level) VALUES(?,?,?,?,?)",
        parts
    )
    for p in parts:
        conn.execute(
            "INSERT OR IGNORE INTO inventory(sku,current_stock,reserved_stock) VALUES(?,0,0)",
            (p[0],)
        )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Numbering helpers
# ─────────────────────────────────────────────────────────────────────────────

def _next_number(prefix: str, table: str) -> str:
    conn = get_connection()
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] + 1
    conn.close()
    return f"{prefix}-{date.today().strftime('%Y%m')}-{n:04d}"

generate_po_number        = lambda: _next_number("PO",  "purchase_orders")
generate_receiving_number = lambda: _next_number("RCV", "receiving")
generate_dispatch_number  = lambda: _next_number("DSP", "dispatch_orders")


# ─────────────────────────────────────────────────────────────────────────────
# Suppliers
# ─────────────────────────────────────────────────────────────────────────────

def get_suppliers():
    conn = get_connection()
    rows = [dict(r) for r in conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Parts
# ─────────────────────────────────────────────────────────────────────────────

def get_parts():
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM parts ORDER BY category, sku"
    ).fetchall()]
    conn.close()
    return rows

def get_part(sku: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM parts WHERE sku=?", (sku,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Orders
# ─────────────────────────────────────────────────────────────────────────────

def create_purchase_order(supplier_id, po_date, exp_date, items, notes=""):
    """Create a PO with one or more line items. Returns (po_number, error)."""
    conn = get_connection()
    po_number = generate_po_number()
    try:
        conn.execute("BEGIN")
        cur = conn.execute(
            """INSERT INTO purchase_orders
               (po_number, supplier_id, po_date, expected_delivery_date, notes)
               VALUES(?,?,?,?,?)""",
            (po_number, supplier_id, str(po_date), str(exp_date), notes)
        )
        po_id = cur.lastrowid
        for it in items:
            conn.execute(
                "INSERT INTO po_items(po_id,sku,ordered_quantity,unit_cost) VALUES(?,?,?,?)",
                (po_id, it["sku"], it["quantity"], it["unit_cost"])
            )
        conn.commit()
        return po_number, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def get_purchase_orders(status=None):
    conn = get_connection()
    q = """
        SELECT po.id, po.po_number, po.status, po.po_date, po.expected_delivery_date,
               po.created_at, po.notes,
               s.name  AS supplier_name,
               COUNT(pi.id)                                         AS item_count,
               COALESCE(SUM(pi.ordered_quantity * pi.unit_cost), 0) AS total_value,
               COALESCE(SUM(pi.ordered_quantity), 0)                AS total_qty,
               COALESCE(SUM(pi.received_quantity), 0)               AS total_received
        FROM purchase_orders po
        JOIN  suppliers s ON s.id = po.supplier_id
        LEFT JOIN po_items pi ON pi.po_id = po.id
    """
    params = []
    if status and status != "All":
        q += " WHERE po.status = ?"
        params.append(status)
    q += " GROUP BY po.id ORDER BY po.created_at DESC"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def get_po_details(po_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT po.*, s.name AS supplier_name, s.contact, s.email, s.phone
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.id = ?
    """, (po_id,)).fetchone()
    if not row:
        conn.close()
        return None
    po = dict(row)
    po["items"] = [dict(r) for r in conn.execute("""
        SELECT pi.*, p.description, p.category, p.unit,
               (pi.ordered_quantity - pi.received_quantity) AS balance_quantity,
               (pi.ordered_quantity * pi.unit_cost)         AS line_total
        FROM po_items pi
        JOIN parts p ON p.sku = pi.sku
        WHERE pi.po_id = ?
        ORDER BY pi.id
    """, (po_id,)).fetchall()]
    conn.close()
    return po


def get_open_pos():
    """Return POs that are Open or Partial (eligible for receiving)."""
    conn = get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT po.id, po.po_number, po.status, po.expected_delivery_date,
               s.name AS supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.status IN ('Open','Partial')
        ORDER BY po.po_date DESC
    """).fetchall()]
    conn.close()
    return rows


def get_po_pending_items(po_id):
    """Return line items that still have an open balance (not fully received)."""
    conn = get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT pi.id, pi.sku, pi.ordered_quantity, pi.received_quantity, pi.unit_cost,
               p.description, p.category, p.unit,
               (pi.ordered_quantity - pi.received_quantity) AS balance_quantity
        FROM po_items pi
        JOIN parts p ON p.sku = pi.sku
        WHERE pi.po_id = ?
          AND (pi.ordered_quantity - pi.received_quantity) > 0
        ORDER BY pi.id
    """, (po_id,)).fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Inbound Receiving  (PO-based only — enforced here)
# ─────────────────────────────────────────────────────────────────────────────

def create_receiving(po_id, po_item_id, sku,
                     recv_qty, dmg_qty, short_qty,
                     recv_date, qc_status, location, notes=""):
    """
    Create a Pending receiving record linked to a PO.
    Manual (non-PO) receiving is structurally blocked — po_id is mandatory.
    """
    conn = get_connection()
    rcv_num = generate_receiving_number()
    try:
        conn.execute("BEGIN")

        # Guard: PO must exist and be open/partial
        row = conn.execute(
            "SELECT status FROM purchase_orders WHERE id=?", (po_id,)
        ).fetchone()
        if not row or row[0] not in ("Open", "Partial"):
            return None, "PO is not open for receiving"

        # Guard: received qty must not exceed open balance
        item = dict(conn.execute(
            "SELECT ordered_quantity, received_quantity FROM po_items WHERE id=?",
            (po_item_id,)
        ).fetchone())
        balance = item["ordered_quantity"] - item["received_quantity"]
        if recv_qty > balance:
            return None, (
                f"Received quantity ({recv_qty}) exceeds open balance ({balance}). "
                "Reduce or split the delivery."
            )

        conn.execute("""
            INSERT INTO receiving
                (receiving_number, po_id, po_item_id, sku,
                 received_quantity, damage_quantity, short_quantity,
                 received_date, qc_status, location, notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (rcv_num, po_id, po_item_id, sku,
              recv_qty, dmg_qty, short_qty,
              str(recv_date), qc_status, location, notes))

        conn.commit()
        return rcv_num, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def approve_receiving(rcv_id):
    """
    Approve a Pending receiving record.
    Updates PO item received qty, PO status, inventory, and records stock movement.
    Damaged units are excluded from inventory addition.
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        rcv = dict(conn.execute(
            "SELECT * FROM receiving WHERE id=?", (rcv_id,)
        ).fetchone())

        if rcv["status"] != "Pending":
            return False, f"Cannot approve: current status is '{rcv['status']}'"

        good_qty = max(0, rcv["received_quantity"] - rcv["damage_quantity"])

        # Mark receiving as Approved
        conn.execute(
            "UPDATE receiving SET status='Approved', approved_at=datetime('now','localtime') WHERE id=?",
            (rcv_id,)
        )

        if good_qty > 0:
            # Update PO item received quantity
            conn.execute(
                "UPDATE po_items SET received_quantity = received_quantity + ? WHERE id=?",
                (good_qty, rcv["po_item_id"])
            )

            # Recalculate PO status
            row = dict(conn.execute(
                "SELECT SUM(ordered_quantity) AS o, SUM(received_quantity) AS r FROM po_items WHERE po_id=?",
                (rcv["po_id"],)
            ).fetchone())
            t_ord, t_rcv = (row["o"] or 0), (row["r"] or 0)
            new_po_status = (
                "Closed"  if t_rcv >= t_ord else
                "Partial" if t_rcv  > 0     else
                "Open"
            )
            conn.execute(
                "UPDATE purchase_orders SET status=? WHERE id=?",
                (new_po_status, rcv["po_id"])
            )

            # Upsert inventory
            conn.execute("""
                INSERT INTO inventory(sku, current_stock, reserved_stock, last_updated)
                VALUES(?, ?, 0, datetime('now','localtime'))
                ON CONFLICT(sku) DO UPDATE SET
                    current_stock = current_stock + ?,
                    last_updated  = datetime('now','localtime')
            """, (rcv["sku"], good_qty, good_qty))

            # Stock movement record
            bal    = conn.execute(
                "SELECT current_stock FROM inventory WHERE sku=?", (rcv["sku"],)
            ).fetchone()[0]
            po_num = conn.execute(
                "SELECT po_number FROM purchase_orders WHERE id=?", (rcv["po_id"],)
            ).fetchone()[0]
            conn.execute("""
                INSERT INTO stock_movements
                    (sku, movement_type, reference_type, reference_number, quantity, balance, notes)
                VALUES(?,?,?,?,?,?,?)
            """, (rcv["sku"], "IN", "RECEIVING", rcv["receiving_number"],
                  good_qty, bal,
                  f"PO:{po_num} | Bin:{rcv['location']} | QC:{rcv['qc_status']}"))

        conn.commit()

        msg = f"✅ Approved — {good_qty} units added to stock."
        if rcv["damage_quantity"] > 0:
            msg += f"  ⚠️ {rcv['damage_quantity']} damaged units excluded."
        if rcv["short_quantity"] > 0:
            msg += f"  📉 {rcv['short_quantity']} units short."
        return True, msg

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def reject_receiving(rcv_id, reason=""):
    conn = get_connection()
    conn.execute("""
        UPDATE receiving
        SET status = 'Rejected',
            notes  = CASE WHEN notes='' THEN ? ELSE notes||' | Rejected: '||? END
        WHERE id=? AND status='Pending'
    """, (f"Rejected: {reason}", reason, rcv_id))
    conn.commit()
    conn.close()


def get_receiving_records(status=None, limit=300):
    conn = get_connection()
    q = """
        SELECT r.*, po.po_number, s.name AS supplier_name,
               p.description AS part_description
        FROM receiving r
        JOIN purchase_orders po ON po.id = r.po_id
        JOIN suppliers       s  ON s.id  = po.supplier_id
        JOIN parts           p  ON p.sku = r.sku
    """
    params = []
    if status and status != "All":
        q += " WHERE r.status=?"
        params.append(status)
    q += f" ORDER BY r.created_at DESC LIMIT {limit}"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Outbound Dispatch
# ─────────────────────────────────────────────────────────────────────────────

def create_dispatch_order(customer, dispatch_date, items, notes=""):
    conn = get_connection()
    dsp_num = generate_dispatch_number()
    try:
        conn.execute("BEGIN")

        # Check stock availability for every line
        for it in items:
            row = conn.execute(
                "SELECT COALESCE(current_stock,0)-COALESCE(reserved_stock,0) AS avail "
                "FROM inventory WHERE sku=?",
                (it["sku"],)
            ).fetchone()
            avail = row["avail"] if row else 0
            if avail < it["quantity"]:
                part = get_part(it["sku"])
                desc = part["description"] if part else it["sku"]
                conn.rollback()
                return None, (
                    f"Insufficient stock for '{desc}'. "
                    f"Available: {avail}, Requested: {it['quantity']}"
                )

        cur = conn.execute(
            "INSERT INTO dispatch_orders(dispatch_number,customer,dispatch_date,notes) VALUES(?,?,?,?)",
            (dsp_num, customer, str(dispatch_date), notes)
        )
        dsp_id = cur.lastrowid

        for it in items:
            conn.execute(
                "INSERT INTO dispatch_items(dispatch_id,sku,ordered_quantity) VALUES(?,?,?)",
                (dsp_id, it["sku"], it["quantity"])
            )
            # Reserve stock immediately
            conn.execute(
                "UPDATE inventory SET reserved_stock=reserved_stock+? WHERE sku=?",
                (it["quantity"], it["sku"])
            )

        conn.commit()
        return dsp_num, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def get_dispatch_orders(status=None):
    conn = get_connection()
    q = """
        SELECT do.*,
               COUNT(di.id)                           AS item_count,
               COALESCE(SUM(di.ordered_quantity), 0)  AS total_qty
        FROM dispatch_orders do
        LEFT JOIN dispatch_items di ON di.dispatch_id = do.id
    """
    params = []
    if status and status != "All":
        q += " WHERE do.status=?"
        params.append(status)
    q += " GROUP BY do.id ORDER BY do.created_at DESC"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def get_dispatch_details(dsp_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM dispatch_orders WHERE id=?", (dsp_id,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    d["items"] = [dict(r) for r in conn.execute("""
        SELECT di.*, p.description, p.unit
        FROM dispatch_items di
        JOIN parts p ON p.sku = di.sku
        WHERE di.dispatch_id = ?
    """, (dsp_id,)).fetchall()]
    conn.close()
    return d


def update_dispatch_step(dsp_id, step):
    """Advance a dispatch order through Pending → Picking → Packing → Dispatched."""
    conn = get_connection()
    d = dict(conn.execute(
        "SELECT * FROM dispatch_orders WHERE id=?", (dsp_id,)
    ).fetchone())
    try:
        conn.execute("BEGIN")

        if step == "picking":
            if d["status"] != "Pending":
                return False, "Order is not in Pending status"
            conn.execute(
                "UPDATE dispatch_orders SET picking_confirmed=1, status='Picking' WHERE id=?",
                (dsp_id,)
            )

        elif step == "packing":
            if not d["picking_confirmed"]:
                return False, "Picking must be confirmed first"
            if d["status"] != "Picking":
                return False, "Order is not in Picking status"
            conn.execute(
                "UPDATE dispatch_orders SET packing_confirmed=1, status='Packing' WHERE id=?",
                (dsp_id,)
            )

        elif step == "dispatch":
            if not d["packing_confirmed"]:
                return False, "Packing must be confirmed first"
            if d["status"] != "Packing":
                return False, "Order is not in Packing status"

            items = [dict(r) for r in conn.execute(
                "SELECT * FROM dispatch_items WHERE dispatch_id=?", (dsp_id,)
            ).fetchall()]

            for it in items:
                inv = conn.execute(
                    "SELECT current_stock FROM inventory WHERE sku=?", (it["sku"],)
                ).fetchone()
                if not inv or inv[0] < it["ordered_quantity"]:
                    conn.rollback()
                    return False, f"Insufficient stock for SKU {it['sku']}"

                # Deduct from inventory
                conn.execute("""
                    UPDATE inventory SET
                        current_stock  = current_stock - ?,
                        reserved_stock = MAX(0, reserved_stock - ?),
                        last_updated   = datetime('now','localtime')
                    WHERE sku=?
                """, (it["ordered_quantity"], it["ordered_quantity"], it["sku"]))

                bal = conn.execute(
                    "SELECT current_stock FROM inventory WHERE sku=?", (it["sku"],)
                ).fetchone()[0]
                conn.execute("""
                    INSERT INTO stock_movements
                        (sku,movement_type,reference_type,reference_number,quantity,balance,notes)
                    VALUES(?,?,?,?,?,?,?)
                """, (it["sku"], "OUT", "DISPATCH", d["dispatch_number"],
                      it["ordered_quantity"], bal, f"Customer: {d['customer']}"))

            conn.execute(
                "UPDATE dispatch_orders SET dispatch_confirmed=1, status='Dispatched' WHERE id=?",
                (dsp_id,)
            )

        conn.commit()
        return True, f"Step '{step}' confirmed successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────────────────────────────────────

def get_inventory_summary():
    conn = get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT i.sku, p.description, p.category, p.unit, p.reorder_level,
               i.current_stock,
               i.reserved_stock,
               (i.current_stock - i.reserved_stock) AS available_stock,
               COALESCE((
                   SELECT SUM(pi2.ordered_quantity - pi2.received_quantity)
                   FROM po_items pi2
                   JOIN purchase_orders po2 ON po2.id = pi2.po_id
                   WHERE pi2.sku = i.sku
                     AND po2.status IN ('Open','Partial')
                     AND (pi2.ordered_quantity - pi2.received_quantity) > 0
               ), 0) AS pending_po_qty,
               i.last_updated
        FROM inventory i
        JOIN parts p ON p.sku = i.sku
        ORDER BY p.category, i.sku
    """).fetchall()]
    conn.close()
    return rows


def get_stock_movements(sku=None, limit=300):
    conn = get_connection()
    q = """
        SELECT sm.*, p.description, p.unit
        FROM stock_movements sm
        JOIN parts p ON p.sku = sm.sku
    """
    params = []
    if sku:
        q += " WHERE sm.sku=?"
        params.append(sku)
    q += f" ORDER BY sm.movement_date DESC LIMIT {limit}"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def get_dashboard_stats():
    conn = get_connection()
    def scalar(q, *p):
        return conn.execute(q, p).fetchone()[0] or 0

    stats = dict(
        open_pos          = scalar("SELECT COUNT(*) FROM purchase_orders WHERE status='Open'"),
        partial_pos       = scalar("SELECT COUNT(*) FROM purchase_orders WHERE status='Partial'"),
        pending_receiving = scalar("SELECT COUNT(*) FROM receiving WHERE status='Pending'"),
        active_dispatches = scalar("SELECT COUNT(*) FROM dispatch_orders WHERE status NOT IN ('Dispatched')"),
        out_of_stock      = scalar("SELECT COUNT(*) FROM inventory WHERE current_stock=0"),
        low_stock         = scalar("""
            SELECT COUNT(*) FROM inventory i JOIN parts p ON p.sku=i.sku
            WHERE i.current_stock > 0 AND i.current_stock <= p.reorder_level
        """),
        damage_alerts     = scalar("SELECT COUNT(*) FROM receiving WHERE damage_quantity>0 AND status='Pending'"),
        shortage_alerts   = scalar("SELECT COUNT(*) FROM receiving WHERE short_quantity>0 AND status='Pending'"),
        total_skus        = scalar("SELECT COUNT(*) FROM parts"),
        total_units       = scalar("SELECT COALESCE(SUM(current_stock),0) FROM inventory"),
        total_dispatched  = scalar("SELECT COUNT(*) FROM dispatch_orders WHERE status='Dispatched'"),
    )
    conn.close()
    return stats
