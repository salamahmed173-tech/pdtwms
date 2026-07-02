/* ============================================================
   AutoWMS — Database Layer (sql.js / IndexedDB)
   ============================================================ */

const DB_IDB_NAME = 'autowms_v1';
let db = null;

/* ── Init ── */
async function initDB() {
  const SQL = await initSqlJs({
    locateFile: f => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.2/${f}`
  });
  const saved = await idbLoad();
  if (saved) {
    db = new SQL.Database(saved);
  } else {
    db = new SQL.Database();
    dbCreateSchema();
    dbSeedData();
    await idbSave();
  }
}

/* ── IndexedDB helpers ── */
function idbSave() {
  return new Promise((res, rej) => {
    const data = db.export();
    const req  = indexedDB.open(DB_IDB_NAME, 1);
    req.onupgradeneeded = e => e.target.result.createObjectStore('kv', { keyPath: 'k' });
    req.onsuccess = e => {
      const tx = e.target.result.transaction('kv', 'readwrite');
      tx.objectStore('kv').put({ k: 'db', v: data });
      tx.oncomplete = res;
      tx.onerror    = rej;
    };
    req.onerror = rej;
  });
}

function idbLoad() {
  return new Promise(res => {
    const req = indexedDB.open(DB_IDB_NAME, 1);
    req.onupgradeneeded = e => e.target.result.createObjectStore('kv', { keyPath: 'k' });
    req.onsuccess = e => {
      const store = e.target.result.transaction('kv', 'readonly').objectStore('kv');
      const get   = store.get('db');
      get.onsuccess = () => res(get.result ? get.result.v : null);
      get.onerror   = () => res(null);
    };
    req.onerror = () => res(null);
  });
}

/* ── Query helpers ── */
function dbRun(sql, params = []) {
  db.run(sql, params);
  idbSave();
}

function dbQuery(sql, params = []) {
  try {
    const stmt = db.prepare(sql);
    if (params.length) stmt.bind(params);
    const rows = [];
    while (stmt.step()) rows.push(stmt.getAsObject());
    stmt.free();
    return rows;
  } catch(e) { console.error('dbQuery', e, sql); return []; }
}

function dbOne(sql, params = []) {
  const r = dbQuery(sql, params);
  return r.length ? r[0] : null;
}

function dbScalar(sql, params = []) {
  const r = dbOne(sql, params);
  return r ? Object.values(r)[0] || 0 : 0;
}

/* ── Numbering ── */
function nextNum(prefix, table) {
  const n   = (dbScalar(`SELECT COUNT(*) as c FROM ${table}`) + 1).toString().padStart(4,'0');
  const ym  = new Date().toISOString().slice(0,7).replace('-','');
  return `${prefix}-${ym}-${n}`;
}

/* ── Schema ── */
function dbCreateSchema() {
  db.run(`
    CREATE TABLE IF NOT EXISTS suppliers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL, contact TEXT DEFAULT '', email TEXT DEFAULT '', phone TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS parts (
      sku TEXT PRIMARY KEY, description TEXT NOT NULL,
      category TEXT DEFAULT 'General', unit TEXT DEFAULT 'EA', reorder_level INTEGER DEFAULT 10
    );
    CREATE TABLE IF NOT EXISTS purchase_orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      po_number TEXT UNIQUE NOT NULL, supplier_id INTEGER NOT NULL,
      po_date TEXT NOT NULL, expected_delivery_date TEXT, status TEXT DEFAULT 'Open',
      notes TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS po_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      po_id INTEGER NOT NULL, sku TEXT NOT NULL,
      ordered_quantity INTEGER NOT NULL, received_quantity INTEGER DEFAULT 0,
      unit_cost REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS receiving (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      receiving_number TEXT UNIQUE NOT NULL,
      po_id INTEGER NOT NULL, po_item_id INTEGER NOT NULL, sku TEXT NOT NULL,
      received_quantity INTEGER NOT NULL, damage_quantity INTEGER DEFAULT 0,
      short_quantity INTEGER DEFAULT 0, received_date TEXT NOT NULL,
      qc_status TEXT NOT NULL, location TEXT DEFAULT '',
      status TEXT DEFAULT 'Pending', approved_at TEXT, notes TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS inventory (
      sku TEXT PRIMARY KEY, current_stock INTEGER DEFAULT 0,
      reserved_stock INTEGER DEFAULT 0,
      last_updated TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS dispatch_orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      dispatch_number TEXT UNIQUE NOT NULL, customer TEXT NOT NULL,
      dispatch_date TEXT NOT NULL, status TEXT DEFAULT 'Pending',
      picking_confirmed INTEGER DEFAULT 0, packing_confirmed INTEGER DEFAULT 0,
      dispatch_confirmed INTEGER DEFAULT 0, notes TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS dispatch_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      dispatch_id INTEGER NOT NULL, sku TEXT NOT NULL, ordered_quantity INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS stock_movements (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      movement_date TEXT DEFAULT (datetime('now','localtime')),
      sku TEXT NOT NULL, movement_type TEXT NOT NULL,
      reference_type TEXT NOT NULL, reference_number TEXT NOT NULL,
      quantity INTEGER NOT NULL, balance INTEGER NOT NULL, notes TEXT DEFAULT ''
    );
  `);
}

/* ── Seed ── */
function dbSeedData() {
  const suppliers = [
    ['AutoParts Pro Ltd','John Smith','john@autopartspro.com','+1-555-0101'],
    ['OEM Supply Co.','Sarah Johnson','sarah@oemsupply.com','+1-555-0102'],
    ['Genuine Parts Hub','Mike Davis','mike@genuinepartshub.com','+1-555-0103'],
    ['TechAuto Distributors','Emily Chen','emily@techauto.com','+1-555-0104'],
    ['Premier Auto Parts','Robert Wilson','robert@premierauto.com','+1-555-0105'],
  ];
  suppliers.forEach(s => db.run(
    'INSERT OR IGNORE INTO suppliers(name,contact,email,phone) VALUES(?,?,?,?)', s
  ));

  const parts = [
    ['ENG-OIL-FLT-001','Engine Oil Filter — Premium','Engine','EA',20],
    ['ENG-AIR-FLT-002','Air Filter — High Performance','Engine','EA',15],
    ['ENG-CLT-001-003','Engine Coolant 5L','Engine','BTL',25],
    ['BRK-PAD-FRN-004','Front Brake Pads Set','Brakes','SET',10],
    ['BRK-PAD-RER-005','Rear Brake Pads Set','Brakes','SET',10],
    ['BRK-DSC-FRN-006','Front Brake Disc Rotor','Brakes','EA',8],
    ['BRK-DSC-RER-007','Rear Brake Disc Rotor','Brakes','EA',8],
    ['SUS-SPR-FRN-008','Front Coil Spring','Suspension','EA',5],
    ['SUS-SHK-FRN-009','Front Shock Absorber','Suspension','EA',5],
    ['SUS-SHK-REA-010','Rear Shock Absorber','Suspension','EA',5],
    ['ELC-BAT-12V-011','12V Car Battery 60Ah','Electrical','EA',5],
    ['ELC-ALT-001-012','Alternator Assembly','Electrical','EA',3],
    ['ELC-STR-001-013','Starter Motor','Electrical','EA',3],
    ['ELC-FUS-BOX-014','Fuse Box Assembly','Electrical','EA',5],
    ['COO-RAD-001-015','Radiator Assembly','Cooling','EA',4],
    ['COO-THS-001-016','Thermostat Housing','Cooling','EA',8],
    ['COO-WPM-001-017','Water Pump','Cooling','EA',6],
    ['TRN-OIL-FLT-018','Transmission Oil Filter','Transmission','EA',10],
    ['TRN-CLT-KIT-019','Clutch Kit Complete Set','Transmission','SET',5],
    ['FUL-PMP-001-020','Fuel Pump Assembly','Fuel System','EA',5],
    ['FUL-FLT-001-021','Fuel Filter Canister','Fuel System','EA',12],
    ['IGN-SRK-PLG-022','Spark Plug Set (4 pcs)','Ignition','SET',15],
    ['IGN-COL-001-023','Ignition Coil Pack','Ignition','EA',8],
    ['EXH-GKT-001-024','Exhaust Manifold Gasket','Exhaust','EA',10],
    ['STR-PMP-001-025','Power Steering Pump','Steering','EA',4],
  ];
  parts.forEach(p => {
    db.run('INSERT OR IGNORE INTO parts(sku,description,category,unit,reorder_level) VALUES(?,?,?,?,?)', p);
    db.run('INSERT OR IGNORE INTO inventory(sku,current_stock,reserved_stock) VALUES(?,0,0)', [p[0]]);
  });
  idbSave();
}

/* ═══════════════════════════════════════════════════════════
   SUPPLIERS
═══════════════════════════════════════════════════════════ */
function getSuppliers() {
  return dbQuery('SELECT * FROM suppliers ORDER BY name');
}

/* ═══════════════════════════════════════════════════════════
   PARTS
═══════════════════════════════════════════════════════════ */
function getParts() {
  return dbQuery('SELECT * FROM parts ORDER BY category, sku');
}

/* ═══════════════════════════════════════════════════════════
   PURCHASE ORDERS
═══════════════════════════════════════════════════════════ */
function createPurchaseOrder(supplierId, poDate, expDate, items, notes) {
  try {
    const poNum = nextNum('PO', 'purchase_orders');
    db.run(
      'INSERT INTO purchase_orders(po_number,supplier_id,po_date,expected_delivery_date,notes) VALUES(?,?,?,?,?)',
      [poNum, supplierId, poDate, expDate, notes]
    );
    const poId = dbScalar('SELECT last_insert_rowid() as id');
    items.forEach(it => db.run(
      'INSERT INTO po_items(po_id,sku,ordered_quantity,unit_cost) VALUES(?,?,?,?)',
      [poId, it.sku, it.quantity, it.unit_cost]
    ));
    idbSave();
    return { ok: true, poNum };
  } catch(e) { return { ok: false, error: e.message }; }
}

function getPurchaseOrders(status) {
  let sql = `
    SELECT po.id, po.po_number, po.status, po.po_date, po.expected_delivery_date, po.created_at,
           s.name AS supplier_name,
           COUNT(pi.id) AS item_count,
           COALESCE(SUM(pi.ordered_quantity*pi.unit_cost),0) AS total_value,
           COALESCE(SUM(pi.ordered_quantity),0) AS total_qty,
           COALESCE(SUM(pi.received_quantity),0) AS total_received
    FROM purchase_orders po
    JOIN suppliers s ON s.id=po.supplier_id
    LEFT JOIN po_items pi ON pi.po_id=po.id
  `;
  const params = [];
  if (status && status !== 'All') { sql += ' WHERE po.status=?'; params.push(status); }
  sql += ' GROUP BY po.id ORDER BY po.created_at DESC';
  return dbQuery(sql, params);
}

function getPoDetails(poId) {
  const po = dbOne(`
    SELECT po.*, s.name AS supplier_name, s.contact, s.email, s.phone
    FROM purchase_orders po JOIN suppliers s ON s.id=po.supplier_id WHERE po.id=?`, [poId]);
  if (!po) return null;
  po.items = dbQuery(`
    SELECT pi.*, p.description, p.category, p.unit,
           (pi.ordered_quantity - pi.received_quantity) AS balance_quantity,
           (pi.ordered_quantity * pi.unit_cost) AS line_total
    FROM po_items pi JOIN parts p ON p.sku=pi.sku WHERE pi.po_id=? ORDER BY pi.id`, [poId]);
  return po;
}

function getOpenPos() {
  return dbQuery(`
    SELECT po.id, po.po_number, po.status, po.expected_delivery_date, s.name AS supplier_name
    FROM purchase_orders po JOIN suppliers s ON s.id=po.supplier_id
    WHERE po.status IN ('Open','Partial') ORDER BY po.po_date DESC`);
}

function getPoPendingItems(poId) {
  return dbQuery(`
    SELECT pi.id, pi.sku, pi.ordered_quantity, pi.received_quantity, pi.unit_cost,
           p.description, p.category, p.unit,
           (pi.ordered_quantity - pi.received_quantity) AS balance_quantity
    FROM po_items pi JOIN parts p ON p.sku=pi.sku
    WHERE pi.po_id=? AND (pi.ordered_quantity-pi.received_quantity)>0 ORDER BY pi.id`, [poId]);
}

/* ═══════════════════════════════════════════════════════════
   RECEIVING  (PO-enforced)
═══════════════════════════════════════════════════════════ */
function createReceiving(poId, poItemId, sku, recvQty, dmgQty, shortQty, date, qcStatus, location, notes) {
  const po = dbOne('SELECT status FROM purchase_orders WHERE id=?', [poId]);
  if (!po || !['Open','Partial'].includes(po.status))
    return { ok: false, error: 'PO is not open for receiving' };
  const item = dbOne('SELECT ordered_quantity,received_quantity FROM po_items WHERE id=?', [poItemId]);
  const bal  = item.ordered_quantity - item.received_quantity;
  if (recvQty > bal)
    return { ok: false, error: `Received (${recvQty}) exceeds open balance (${bal})` };
  const num = nextNum('RCV', 'receiving');
  db.run(`INSERT INTO receiving
    (receiving_number,po_id,po_item_id,sku,received_quantity,damage_quantity,short_quantity,
     received_date,qc_status,location,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)`,
    [num, poId, poItemId, sku, recvQty, dmgQty, shortQty, date, qcStatus, location, notes]);
  idbSave();
  return { ok: true, num };
}

function approveReceiving(rcvId) {
  const rcv = dbOne('SELECT * FROM receiving WHERE id=?', [rcvId]);
  if (!rcv || rcv.status !== 'Pending') return { ok: false, error: 'Cannot approve: wrong status' };
  const good = Math.max(0, rcv.received_quantity - rcv.damage_quantity);
  db.run("UPDATE receiving SET status='Approved', approved_at=datetime('now','localtime') WHERE id=?", [rcvId]);
  if (good > 0) {
    db.run('UPDATE po_items SET received_quantity=received_quantity+? WHERE id=?', [good, rcv.po_item_id]);
    const tot  = dbOne('SELECT SUM(ordered_quantity) as o, SUM(received_quantity) as r FROM po_items WHERE po_id=?', [rcv.po_id]);
    const newSt = tot.r >= tot.o ? 'Closed' : tot.r > 0 ? 'Partial' : 'Open';
    db.run('UPDATE purchase_orders SET status=? WHERE id=?', [newSt, rcv.po_id]);
    db.run(`INSERT INTO inventory(sku,current_stock,reserved_stock,last_updated)
      VALUES(?,?,0,datetime('now','localtime'))
      ON CONFLICT(sku) DO UPDATE SET current_stock=current_stock+?, last_updated=datetime('now','localtime')`,
      [rcv.sku, good, good]);
    const bal = dbScalar('SELECT current_stock FROM inventory WHERE sku=?', [rcv.sku]);
    const poNum = dbScalar('SELECT po_number FROM purchase_orders WHERE id=?', [rcv.po_id]);
    db.run(`INSERT INTO stock_movements(sku,movement_type,reference_type,reference_number,quantity,balance,notes)
      VALUES(?,?,?,?,?,?,?)`,
      [rcv.sku,'IN','RECEIVING',rcv.receiving_number,good,bal,`PO:${poNum}|Bin:${rcv.location}|QC:${rcv.qc_status}`]);
  }
  idbSave();
  let msg = `✅ Approved — ${good} units added to stock.`;
  if (rcv.damage_quantity > 0)  msg += ` ⚠️ ${rcv.damage_quantity} damaged excluded.`;
  if (rcv.short_quantity  > 0)  msg += ` 📉 ${rcv.short_quantity} units short.`;
  return { ok: true, msg };
}

function rejectReceiving(rcvId, reason) {
  db.run("UPDATE receiving SET status='Rejected', notes=notes||' | Rejected: '||? WHERE id=? AND status='Pending'",
    [reason, rcvId]);
  idbSave();
}

function getReceivingRecords(status) {
  let sql = `
    SELECT r.*, po.po_number, s.name AS supplier_name, p.description AS part_description
    FROM receiving r
    JOIN purchase_orders po ON po.id=r.po_id
    JOIN suppliers s ON s.id=po.supplier_id
    JOIN parts p ON p.sku=r.sku
  `;
  const params = [];
  if (status && status !== 'All') { sql += ' WHERE r.status=?'; params.push(status); }
  sql += ' ORDER BY r.created_at DESC LIMIT 200';
  return dbQuery(sql, params);
}

/* ═══════════════════════════════════════════════════════════
   DISPATCH
═══════════════════════════════════════════════════════════ */
function createDispatchOrder(customer, date, items, notes) {
  for (const it of items) {
    const inv = dbOne('SELECT current_stock-reserved_stock AS avail FROM inventory WHERE sku=?', [it.sku]);
    const avail = inv ? inv.avail : 0;
    if (avail < it.quantity) {
      const part = dbOne('SELECT description FROM parts WHERE sku=?', [it.sku]);
      return { ok: false, error: `Insufficient stock for "${part ? part.description : it.sku}". Available: ${avail}, Requested: ${it.quantity}` };
    }
  }
  const num = nextNum('DSP', 'dispatch_orders');
  db.run('INSERT INTO dispatch_orders(dispatch_number,customer,dispatch_date,notes) VALUES(?,?,?,?)',
    [num, customer, date, notes]);
  const dspId = dbScalar('SELECT last_insert_rowid() as id');
  items.forEach(it => {
    db.run('INSERT INTO dispatch_items(dispatch_id,sku,ordered_quantity) VALUES(?,?,?)', [dspId, it.sku, it.quantity]);
    db.run('UPDATE inventory SET reserved_stock=reserved_stock+? WHERE sku=?', [it.quantity, it.sku]);
  });
  idbSave();
  return { ok: true, num };
}

function getDispatchOrders(status) {
  let sql = `
    SELECT do.*, COUNT(di.id) AS item_count, COALESCE(SUM(di.ordered_quantity),0) AS total_qty
    FROM dispatch_orders do LEFT JOIN dispatch_items di ON di.dispatch_id=do.id
  `;
  const params = [];
  if (status && status !== 'All') { sql += ' WHERE do.status=?'; params.push(status); }
  sql += ' GROUP BY do.id ORDER BY do.created_at DESC';
  return dbQuery(sql, params);
}

function getDispatchDetails(dspId) {
  const d = dbOne('SELECT * FROM dispatch_orders WHERE id=?', [dspId]);
  if (!d) return null;
  d.items = dbQuery('SELECT di.*, p.description, p.unit FROM dispatch_items di JOIN parts p ON p.sku=di.sku WHERE di.dispatch_id=?', [dspId]);
  return d;
}

function updateDispatchStep(dspId, step) {
  const d = dbOne('SELECT * FROM dispatch_orders WHERE id=?', [dspId]);
  if (!d) return { ok: false, error: 'Order not found' };
  if (step === 'picking') {
    if (d.status !== 'Pending') return { ok: false, error: 'Not in Pending status' };
    db.run("UPDATE dispatch_orders SET picking_confirmed=1, status='Picking' WHERE id=?", [dspId]);
  } else if (step === 'packing') {
    if (!d.picking_confirmed) return { ok: false, error: 'Picking must be confirmed first' };
    db.run("UPDATE dispatch_orders SET packing_confirmed=1, status='Packing' WHERE id=?", [dspId]);
  } else if (step === 'dispatch') {
    if (!d.packing_confirmed) return { ok: false, error: 'Packing must be confirmed first' };
    const items = dbQuery('SELECT * FROM dispatch_items WHERE dispatch_id=?', [dspId]);
    for (const it of items) {
      const inv = dbOne('SELECT current_stock FROM inventory WHERE sku=?', [it.sku]);
      if (!inv || inv.current_stock < it.ordered_quantity)
        return { ok: false, error: `Insufficient stock for ${it.sku}` };
      db.run(`UPDATE inventory SET current_stock=current_stock-?, reserved_stock=MAX(0,reserved_stock-?), last_updated=datetime('now','localtime') WHERE sku=?`,
        [it.ordered_quantity, it.ordered_quantity, it.sku]);
      const bal = dbScalar('SELECT current_stock FROM inventory WHERE sku=?', [it.sku]);
      db.run('INSERT INTO stock_movements(sku,movement_type,reference_type,reference_number,quantity,balance,notes) VALUES(?,?,?,?,?,?,?)',
        [it.sku,'OUT','DISPATCH',d.dispatch_number,it.ordered_quantity,bal,`Customer:${d.customer}`]);
    }
    db.run("UPDATE dispatch_orders SET dispatch_confirmed=1, status='Dispatched' WHERE id=?", [dspId]);
  }
  idbSave();
  return { ok: true };
}

/* ═══════════════════════════════════════════════════════════
   INVENTORY
═══════════════════════════════════════════════════════════ */
function getInventorySummary() {
  return dbQuery(`
    SELECT i.sku, p.description, p.category, p.unit, p.reorder_level,
           i.current_stock, i.reserved_stock,
           (i.current_stock - i.reserved_stock) AS available_stock,
           COALESCE((
             SELECT SUM(pi2.ordered_quantity - pi2.received_quantity)
             FROM po_items pi2 JOIN purchase_orders po2 ON po2.id=pi2.po_id
             WHERE pi2.sku=i.sku AND po2.status IN ('Open','Partial')
               AND (pi2.ordered_quantity-pi2.received_quantity)>0
           ),0) AS pending_po_qty,
           i.last_updated
    FROM inventory i JOIN parts p ON p.sku=i.sku ORDER BY p.category, i.sku`);
}

function getStockMovements(sku) {
  let sql = 'SELECT sm.*, p.description, p.unit FROM stock_movements sm JOIN parts p ON p.sku=sm.sku';
  const params = [];
  if (sku) { sql += ' WHERE sm.sku=?'; params.push(sku); }
  sql += ' ORDER BY sm.movement_date DESC LIMIT 200';
  return dbQuery(sql, params);
}

function getDashboardStats() {
  return {
    openPos:         dbScalar("SELECT COUNT(*) FROM purchase_orders WHERE status='Open'"),
    partialPos:      dbScalar("SELECT COUNT(*) FROM purchase_orders WHERE status='Partial'"),
    pendingReceiving:dbScalar("SELECT COUNT(*) FROM receiving WHERE status='Pending'"),
    activeDispatch:  dbScalar("SELECT COUNT(*) FROM dispatch_orders WHERE status NOT IN ('Dispatched')"),
    outOfStock:      dbScalar('SELECT COUNT(*) FROM inventory WHERE current_stock=0'),
    lowStock:        dbScalar('SELECT COUNT(*) FROM inventory i JOIN parts p ON p.sku=i.sku WHERE i.current_stock>0 AND i.current_stock<=p.reorder_level'),
    totalSkus:       dbScalar('SELECT COUNT(*) FROM parts'),
    totalUnits:      dbScalar('SELECT COALESCE(SUM(current_stock),0) FROM inventory'),
    totalDispatched: dbScalar("SELECT COUNT(*) FROM dispatch_orders WHERE status='Dispatched'"),
    damageAlerts:    dbScalar("SELECT COUNT(*) FROM receiving WHERE damage_quantity>0 AND status='Pending'"),
    shortageAlerts:  dbScalar("SELECT COUNT(*) FROM receiving WHERE short_quantity>0 AND status='Pending'"),
  };
}

function resetDatabase() {
  return new Promise((res) => {
    const req = indexedDB.open(DB_IDB_NAME, 1);
    req.onsuccess = e => {
      const tx = e.target.result.transaction('kv', 'readwrite');
      tx.objectStore('kv').delete('db');
      tx.oncomplete = () => location.reload();
    };
    req.onerror = () => location.reload();
  });
}
