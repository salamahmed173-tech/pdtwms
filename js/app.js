/* ============================================================
   AutoWMS — Application Logic & UI Rendering
   ============================================================ */

/* ── State ── */
let pendingPOItems  = [];
let pendingDspItems = [];

/* ── Utility: UI ── */
function $(id) { return document.getElementById(id); }
function html(el, h) { if (el) el.innerHTML = h; }

function badge(status) {
  const s = (status||'').toLowerCase().replace(/\s/g,'-');
  return `<span class="badge badge-${s}">${status}</span>`;
}

function alertBox(msg, type='info') {
  return `<div class="alert alert-${type}">${msg}</div>`;
}

function formatCur(n) { return '$' + (+n||0).toLocaleString('en-US', {minimumFractionDigits:2,maximumFractionDigits:2}); }
function formatNum(n)  { return (+n||0).toLocaleString('en-US'); }
function today()       { return new Date().toISOString().split('T')[0]; }
function futureDate(d) { const dt=new Date(); dt.setDate(dt.getDate()+d); return dt.toISOString().split('T')[0]; }

function toast(msg, type='success') {
  const el = document.createElement('div');
  el.className = `toast-item toast-${type}`;
  el.textContent = msg;
  $('toast').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function empty(icon, msg, sub='') {
  return `<div class="empty"><div class="empty-icon">${icon}</div>
    <div class="empty-msg">${msg}</div><div class="empty-sub">${sub}</div></div>`;
}

function mkTable(rows, cols) {
  if (!rows || !rows.length) return empty('📋','No records found','');
  const head = cols.map(c => `<th>${c.label}</th>`).join('');
  const body = rows.map(r => '<tr>' + cols.map(c => {
    let v = r[c.key] !== undefined ? r[c.key] : '—';
    if (c.fmt) v = c.fmt(v, r);
    return `<td>${v}</td>`;
  }).join('') + '</tr>').join('');
  return `<div class="tbl-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function mkInfoBox(rows) {
  return '<div class="info-box">' + rows.map(([k,v]) =>
    `<div class="info-row"><span class="info-key">${k}</span><span class="info-val">${v}</span></div>`
  ).join('') + '</div>';
}

function mkMetric(label, value, sub='') {
  return `<div class="metric-card">
    <div class="metric-lbl">${label}</div>
    <div class="metric-val">${value}</div>
    <div class="metric-sub">${sub}</div>
  </div>`;
}

function wfHtml(steps) {
  let h = '<div class="wf-track">';
  steps.forEach(([label, state], i) => {
    const icon = state === 'done' ? '✓' : i + 1;
    h += `<div class="wf-step wf-${state}"><div class="wf-circle">${icon}</div><div class="wf-lbl">${label}</div></div>`;
    if (i < steps.length - 1) h += `<div class="wf-line wf-${state}"></div>`;
  });
  return h + '</div>';
}

/* ── Navigation ── */
function showPage(page) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const el = $('page-' + page);
  if (el) el.style.display = 'block';
  const nav = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (nav) nav.classList.add('active');
  renderPage(page);
}

function showTab(group, tab) {
  document.querySelectorAll(`.tab-btn[data-group="${group}"]`).forEach(b => b.classList.remove('active'));
  document.querySelectorAll(`.tab-pane[data-group="${group}"]`).forEach(p => p.classList.remove('active'));
  const btn = document.querySelector(`.tab-btn[data-group="${group}"][data-tab="${tab}"]`);
  if (btn) btn.classList.add('active');
  const pane = document.querySelector(`.tab-pane[data-group="${group}"][data-tab="${tab}"]`);
  if (pane) pane.classList.add('active');
}

function tabs(group, items, defaultTab) {
  const btns  = items.map(([tab, label]) =>
    `<button class="tab-btn${tab===defaultTab?' active':''}" data-group="${group}" data-tab="${tab}" onclick="showTab('${group}','${tab}')">${label}</button>`
  ).join('');
  const panes = items.map(([tab]) =>
    `<div class="tab-pane${tab===defaultTab?' active':''}" data-group="${group}" data-tab="${tab}" id="${group}-tab-${tab}"></div>`
  ).join('');
  return `<div class="tabs">${btns}</div>${panes}`;
}

function renderPage(page) {
  const fns = {
    dashboard:         renderDashboard,
    'purchase-orders': renderPurchaseOrders,
    'inbound-receiving': renderReceiving,
    'outbound-dispatch': renderDispatch,
    inventory:         renderInventory,
  };
  if (fns[page]) fns[page]();
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD
══════════════════════════════════════════════════════════ */
function renderDashboard() {
  const stats = getDashboardStats();
  const inv   = getInventorySummary();
  const mvs   = getStockMovements(null).slice(0, 15);

  // Top 10 available
  const top10 = [...inv].sort((a,b)=>b.available_stock-a.available_stock).slice(0,10);

  const metricsRow1 = `<div class="metrics metrics-5">
    ${mkMetric('📦 Open POs',          stats.openPos,         `+${stats.partialPos} Partial`)}
    ${mkMetric('📥 Pending Receiving', stats.pendingReceiving, 'Awaiting Approval')}
    ${mkMetric('📤 Active Dispatches', stats.activeDispatch,   'In Progress')}
    ${mkMetric('🗃️ Total SKUs',        stats.totalSkus,        formatNum(stats.totalUnits)+' Units')}
    ${mkMetric('✅ Dispatched',         stats.totalDispatched,  'All Time')}
  </div>`;

  const metricsRow2 = `<div class="metrics metrics-4">
    ${mkMetric(stats.outOfStock>0?'🔴 Out of Stock':'🟢 Out of Stock', stats.outOfStock, 'SKUs')}
    ${mkMetric(stats.lowStock>0?'🟡 Low Stock':'🟢 Low Stock', stats.lowStock, 'Below Reorder')}
    ${mkMetric(stats.damageAlerts>0?'🟠 Damage Alerts':'🟢 Damage Alerts', stats.damageAlerts, 'Pending Review')}
    ${mkMetric(stats.shortageAlerts>0?'🟠 Shortage Alerts':'🟢 Shortage Alerts', stats.shortageAlerts, 'Pending Review')}
  </div>`;

  // Movements feed
  const mvFeed = mvs.length ? mvs.map(m => {
    const isIn = m.movement_type === 'IN';
    return `<div class="mv-card">
      <div><div class="mv-ref">${m.reference_number} · ${(m.movement_date||'').slice(0,16)}</div>
        <div class="mv-desc">${isIn?'📥':'📤'} ${(m.description||'').slice(0,38)}</div>
        <div class="mv-ref">${m.sku}</div>
      </div>
      <div style="text-align:right">
        <div class="${isIn?'mv-in':'mv-out'}">${isIn?'+':'−'}${m.quantity}</div>
        <div class="mv-bal">Bal: ${m.balance}</div>
      </div>
    </div>`;
  }).join('') : empty('📊','No movements yet','Create a PO → Receive → Dispatch');

  // Rules banner
  const rules = `
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;">
      ${alertBox('🚫 <strong>Manual Receiving Blocked</strong> — All inbound stock requires an approved Purchase Order','danger')}
      ${alertBox('ℹ️ <strong>No Negative Stock</strong> — Dispatch is blocked when available stock is insufficient','info')}
      ${alertBox('⚠️ <strong>Stock Reserved on Create</strong> — Deducted only after Dispatch confirmation','warn')}
    </div>`;

  html($('page-dashboard'), `
    <div class="hero">
      <div class="hero-icon">🏭</div>
      <div class="hero-title">AutoWMS Dashboard</div>
      <div class="hero-sub">Automotive Spare Parts · Warehouse Management · PO-controlled receiving · Real-time inventory</div>
    </div>
    ${metricsRow1}${metricsRow2}
    <hr>
    <div class="two-col">
      <div>
        <div class="section-title">📦 Live Inventory Snapshot</div>
        ${mkTable(inv.slice(0,15), [
          {key:'sku',label:'SKU'},
          {key:'description',label:'Description',fmt:v=>v.slice(0,30)},
          {key:'category',label:'Category'},
          {key:'current_stock',label:'On Hand'},
          {key:'available_stock',label:'Available'},
          {key:'reserved_stock',label:'Reserved'},
          {key:'pending_po_qty',label:'PO Pending'},
          {key:'current_stock',label:'Status',fmt:(v,r)=>{
            if(v==0) return badge('Out');
            if(v<=r.reorder_level) return badge('Low');
            return badge('In Stock');
          }},
        ])}
        <div id="dash-chart" style="margin-top:16px;"></div>
      </div>
      <div>
        <div class="section-title">🔄 Recent Stock Movements</div>
        ${mvFeed}
      </div>
    </div>
    ${rules}
    <div class="footer">AutoWMS v1.0 · Automotive Spare Parts WMS · SQLite (WASM) · Netlify</div>
  `);

  // Plotly bar chart — top 10 available
  if (top10.length && typeof Plotly !== 'undefined') {
    Plotly.newPlot('dash-chart', [{
      x: top10.map(i=>i.available_stock), y: top10.map(i=>i.sku), type:'bar', orientation:'h',
      marker:{ color: top10.map((_,idx)=>`hsl(${200+idx*15},70%,55%)`), },
    }], {
      paper_bgcolor:'#0d1117', plot_bgcolor:'#161b22', font:{color:'#8b949e'},
      xaxis:{gridcolor:'#21262d',title:'Available Units'}, yaxis:{gridcolor:'#21262d',categoryorder:'total ascending'},
      margin:{l:130,r:10,t:10,b:40}, height:260,
      title:{text:'Top 10 Parts by Available Stock',font:{color:'#c9d1d9',size:13}},
    }, {responsive:true, displayModeBar:false});
  }
}

/* ══════════════════════════════════════════════════════════
   PURCHASE ORDERS
══════════════════════════════════════════════════════════ */
function renderPurchaseOrders() {
  const suppliers = getSuppliers();
  const parts     = getParts();

  html($('page-purchase-orders'), `
    <div class="hero">
      <div class="hero-icon">📦</div>
      <div class="hero-title">Purchase Orders</div>
      <div class="hero-sub">Create supplier POs · Track line-item fulfilment · Auto status updates</div>
    </div>
    ${tabs('po', [['create','  ➕ Create PO  '],['view','  📋 View All POs  '],['detail','  🔍 PO Detail  ']], 'create')}
  `);

  // ── Create PO tab ──
  const supOpts = suppliers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  const partOpts = ['<option value="">— Select a part —</option>',
    ...parts.map(p => `<option value="${p.sku}">[${p.sku}] ${p.description} (${p.category})</option>`)
  ].join('');

  html($('po-tab-create'), `
    <div class="two-col-eq">
      <div>
        <div class="section-title">📋 PO Header</div>
        <div class="form-grid" style="gap:12px;">
          <div class="form-group">
            <label class="form-label">Supplier *</label>
            <select id="po-supplier" class="form-select">${supOpts}</select>
          </div>
          <div class="form-grid form-grid-2">
            <div class="form-group"><label class="form-label">PO Date *</label>
              <input id="po-date" type="date" class="form-input" value="${today()}"></div>
            <div class="form-group"><label class="form-label">Expected Delivery *</label>
              <input id="po-expdate" type="date" class="form-input" value="${futureDate(14)}"></div>
          </div>
          <div class="form-group"><label class="form-label">Notes</label>
            <textarea id="po-notes" class="form-textarea" placeholder="Optional notes…"></textarea></div>
          <hr>
          <div class="section-title">🔩 Add Line Item</div>
          <div class="form-group"><label class="form-label">Part *</label>
            <select id="po-part" class="form-select">${partOpts}</select></div>
          <div class="form-grid form-grid-2">
            <div class="form-group"><label class="form-label">Qty *</label>
              <input id="po-qty" type="number" class="form-input" value="10" min="1"></div>
            <div class="form-group"><label class="form-label">Unit Cost (USD) *</label>
              <input id="po-cost" type="number" class="form-input" value="25.00" min="0.01" step="0.01"></div>
          </div>
          <div class="form-grid form-grid-2">
            <button class="btn btn-full" onclick="poAddItem()">➕ Add Item</button>
            <button class="btn btn-primary btn-full" onclick="poCreate()">✅ Create PO</button>
          </div>
        </div>
      </div>
      <div>
        <div class="section-title">🛒 Line Items Preview</div>
        <div id="po-preview"></div>
      </div>
    </div>
  `);
  renderPOPreview();

  // ── View POs tab ──
  renderViewPOs();

  // ── Detail tab ──
  renderPODetailTab();
}

function renderPOPreview() {
  const el = $('po-preview');
  if (!el) return;
  if (!pendingPOItems.length) {
    html(el, empty('📋','No items added yet','Select a part and click ➕ Add Item'));
    return;
  }
  const totalQty = pendingPOItems.reduce((a,i)=>a+i.quantity,0);
  const totalVal = pendingPOItems.reduce((a,i)=>a+i.line_total,0);
  const tbl = mkTable(pendingPOItems, [
    {key:'sku',label:'SKU'},
    {key:'description',label:'Description',fmt:v=>v.slice(0,25)},
    {key:'quantity',label:'Qty'},
    {key:'unit_cost',label:'Unit Cost',fmt:formatCur},
    {key:'line_total',label:'Total',fmt:formatCur},
    {key:'sku',label:'',fmt:(_,r)=>`<button class="btn btn-sm btn-danger" onclick="poRemoveItem('${r.sku}')">🗑</button>`},
  ]);
  html(el, tbl + mkInfoBox([
    ['Lines', pendingPOItems.length],
    ['Total Qty', formatNum(totalQty) + ' units'],
    ['PO Value', `<span style="color:var(--green);font-weight:700;">${formatCur(totalVal)}</span>`],
  ]) + `<br><button class="btn btn-danger btn-full" onclick="poClearItems()">🗑 Clear All</button>`);
}

function poAddItem() {
  const sku  = $('po-part')?.value;
  const qty  = parseInt($('po-qty')?.value);
  const cost = parseFloat($('po-cost')?.value);
  if (!sku) { toast('Please select a part', 'error'); return; }
  if (isNaN(qty)||qty<1) { toast('Quantity must be ≥ 1','error'); return; }
  if (pendingPOItems.find(i=>i.sku===sku)) { toast('SKU already in list','warn'); return; }
  const parts = getParts();
  const part  = parts.find(p=>p.sku===sku);
  pendingPOItems.push({ sku, description:part.description, category:part.category, unit:part.unit, quantity:qty, unit_cost:cost, line_total:qty*cost });
  renderPOPreview();
}

function poRemoveItem(sku) {
  pendingPOItems = pendingPOItems.filter(i=>i.sku!==sku);
  renderPOPreview();
}

function poClearItems() { pendingPOItems = []; renderPOPreview(); }

function poCreate() {
  if (!pendingPOItems.length) { toast('Add at least one item','error'); return; }
  const supId  = $('po-supplier')?.value;
  const poDate = $('po-date')?.value;
  const expDate= $('po-expdate')?.value;
  const notes  = $('po-notes')?.value||'';
  if (expDate < poDate) { toast('Delivery date cannot be before PO date','error'); return; }
  const res = createPurchaseOrder(supId, poDate, expDate, pendingPOItems, notes);
  if (res.ok) {
    pendingPOItems = [];
    toast(`🎉 PO ${res.poNum} created!`,'success');
    renderPOPreview();
    renderViewPOs();
  } else {
    toast('Error: ' + res.error, 'error');
  }
}

function renderViewPOs() {
  const el = $('po-tab-view');
  if (!el) return;
  const pos = getPurchaseOrders();
  const openN = pos.filter(p=>p.status==='Open').length;
  const partN = pos.filter(p=>p.status==='Partial').length;
  const closN = pos.filter(p=>p.status==='Closed').length;
  const totV  = pos.reduce((a,p)=>a+p.total_value,0);
  const metrics = pos.length ? `<div class="metrics metrics-5">
    ${mkMetric('Total POs',  pos.length)}
    ${mkMetric('🟢 Open',    openN)}
    ${mkMetric('🟡 Partial', partN)}
    ${mkMetric('⚫ Closed',  closN)}
    ${mkMetric('💰 Value',   formatCur(totV))}
  </div><hr>` : '';
  html(el, metrics + mkTable(pos, [
    {key:'po_number',  label:'PO Number'},
    {key:'supplier_name',label:'Supplier'},
    {key:'po_date',    label:'PO Date'},
    {key:'expected_delivery_date',label:'Expected'},
    {key:'item_count', label:'Lines'},
    {key:'total_qty',  label:'Ordered',fmt:formatNum},
    {key:'total_received',label:'Received',fmt:formatNum},
    {key:'total_value',label:'Value',fmt:formatCur},
    {key:'status',     label:'Status',fmt:badge},
    {key:'id',         label:'Detail',fmt:(_,r)=>`<button class="btn btn-sm" onclick="showPODetail(${r.id})">🔍 View</button>`},
  ]));
}

function renderPODetailTab() {
  const el = $('po-tab-detail');
  if (!el) return;
  const pos = getPurchaseOrders();
  if (!pos.length) { html(el, empty('📦','No POs yet','Create one in the Create PO tab')); return; }
  const opts = pos.map(p=>`<option value="${p.id}">${p.po_number} · ${p.supplier_name} [${p.status}]</option>`).join('');
  html(el, `<div class="form-group" style="max-width:450px;margin-bottom:16px;">
    <label class="form-label">Select Purchase Order</label>
    <select class="form-select" onchange="showPODetail(this.value)">${opts}</select>
  </div><div id="po-detail-content"></div>`);
  showPODetail(pos[0].id);
}

function showPODetail(id) {
  showTab('po','detail');
  const po = getPoDetails(+id);
  if (!po) return;
  const el = $('po-detail-content');
  const totOrd = po.items.reduce((a,i)=>a+i.ordered_quantity,0);
  const totRcv = po.items.reduce((a,i)=>a+i.received_quantity,0);
  const totBal = po.items.reduce((a,i)=>a+i.balance_quantity,0);
  const totVal = po.items.reduce((a,i)=>a+i.line_total,0);
  const pct    = totOrd>0 ? Math.min(totRcv/totOrd,1) : 0;
  html(el, `
    <div class="two-col-eq" style="margin-bottom:16px;">
      <div>
        <div class="section-title">🏢 PO Information</div>
        ${mkInfoBox([
          ['PO Number',`<span style="color:var(--blue3);font-weight:700;">${po.po_number}</span>`],
          ['Supplier',po.supplier_name],['Contact',po.contact||'—'],['Email',po.email||'—'],
          ['PO Date',po.po_date],['Expected',po.expected_delivery_date||'—'],['Notes',po.notes||'—'],
        ])}
      </div>
      <div>
        <div class="section-title">📊 Summary</div>
        ${mkInfoBox([
          ['Status',badge(po.status)],['Lines',po.items.length],
          ['Ordered',formatNum(totOrd)+' units'],
          ['Received',`<span style="color:var(--blue3);">${formatNum(totRcv)} units</span>`],
          ['Balance',`<span style="color:var(--yellow);">${formatNum(totBal)} units</span>`],
          ['Value',`<span style="color:var(--green);font-weight:700;">${formatCur(totVal)}</span>`],
        ])}
        <div class="progress-bar" style="margin-top:12px;"><div class="progress-fill" style="width:${Math.round(pct*100)}%"></div></div>
        <div style="font-size:11px;color:var(--text4);margin-top:4px;">Receiving Progress: ${Math.round(pct*100)}%</div>
      </div>
    </div>
    <div class="section-title">🔩 Line Items</div>
    ${mkTable(po.items, [
      {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,30)},
      {key:'category',label:'Category'},{key:'unit',label:'Unit'},
      {key:'ordered_quantity',label:'Ordered',fmt:formatNum},
      {key:'received_quantity',label:'Received',fmt:formatNum},
      {key:'balance_quantity',label:'Balance',fmt:formatNum},
      {key:'unit_cost',label:'Unit Cost',fmt:formatCur},
      {key:'line_total',label:'Line Total',fmt:formatCur},
    ])}
  `);
}

/* ══════════════════════════════════════════════════════════
   INBOUND RECEIVING
══════════════════════════════════════════════════════════ */
function renderReceiving() {
  html($('page-inbound-receiving'), `
    <div class="hero">
      <div class="hero-icon">📥</div>
      <div class="hero-title">Inbound Receiving</div>
      <div class="hero-sub">PO-controlled receiving · Damage & shortage tracking · QC inspection · Bin put-away</div>
    </div>
    <div class="blocked-banner">
      <div class="blocked-icon">🔒</div>
      <div><div class="blocked-title">Manual Receiving is BLOCKED</div>
        <div class="blocked-desc">All inbound stock must be received against an approved Purchase Order. Select an Open or Partial PO below to begin the receiving process.</div>
      </div>
    </div>
    ${tabs('rcv',[['receive','  📦 Receive from PO  '],['approvals','  ✅ Pending Approvals  '],['history','  📋 History  ']],'receive')}
  `);
  renderReceiveFromPO();
  renderPendingApprovals();
  renderReceivingHistory();
}

function renderReceiveFromPO() {
  const el = $('rcv-tab-receive');
  if (!el) return;
  const openPos = getOpenPos();
  if (!openPos.length) {
    html(el, empty('📭','No Open Purchase Orders','Create a Purchase Order first. Only Open or Partial POs can be received against.'));
    return;
  }
  const poOpts = ['<option value="">— Select a PO to start receiving —</option>',
    ...openPos.map(p=>`<option value="${p.id}">${p.po_number} | ${p.supplier_name} [${p.status}] ETA: ${p.expected_delivery_date||'—'}</option>`)
  ].join('');

  html(el, `
    <div class="section-title">Step 1 — Select a Purchase Order</div>
    <div class="form-group" style="max-width:550px;margin-bottom:20px;">
      <label class="form-label">Open / Partial PO *</label>
      <select id="rcv-po-sel" class="form-select" onchange="onRcvPoChange()">${poOpts}</select>
    </div>
    <div id="rcv-po-detail"></div>
  `);
}

function onRcvPoChange() {
  const poId = +$('rcv-po-sel')?.value;
  const el   = $('rcv-po-detail');
  if (!poId) { html(el, alertBox('Select a PO above to view its pending items.','info')); return; }
  const po   = getPoDetails(poId);
  const pend = getPoPendingItems(poId);

  if (!pend.length) {
    html(el, alertBox('All items on this PO have been fully received.','info'));
    return;
  }

  const itemOpts = pend.map(it=>
    `<option value="${it.id}|${it.sku}">[${it.sku}] ${it.description} (Balance: ${it.balance_quantity} ${it.unit})</option>`
  ).join('');

  html(el, `
    <hr>
    <div class="metrics metrics-4" style="margin-bottom:16px;">
      ${mkMetric('Supplier', po.supplier_name)}
      ${mkMetric('PO Number', po.po_number)}
      ${mkMetric('Status', badge(po.status))}
      ${mkMetric('Expected', po.expected_delivery_date||'—')}
    </div>
    <div class="section-title">Pending Line Items</div>
    ${mkTable(pend,[
      {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,30)},
      {key:'category',label:'Cat.'},{key:'unit',label:'Unit'},
      {key:'ordered_quantity',label:'Ordered'},{key:'received_quantity',label:'Received'},
      {key:'balance_quantity',label:'Balance',fmt:v=>`<strong style="color:var(--yellow);">${v}</strong>`},
    ])}
    <hr>
    <div class="section-title">Step 3 — Enter Receiving Details</div>
    <div class="form-grid" style="gap:12px;max-width:700px;">
      <div class="form-group"><label class="form-label">Select Line Item *</label>
        <select id="rcv-item-sel" class="form-select" onchange="onRcvItemChange(${poId})">${itemOpts}</select></div>
      <div class="form-grid form-grid-3">
        <div class="form-group"><label class="form-label">SKU (auto)</label>
          <input id="rcv-sku" class="form-input" disabled></div>
        <div class="form-group"><label class="form-label">Description (auto)</label>
          <input id="rcv-desc" class="form-input" disabled></div>
        <div class="form-group"><label class="form-label">Open Balance (auto)</label>
          <input id="rcv-bal" class="form-input" disabled></div>
      </div>
      <div class="form-grid form-grid-3">
        <div class="form-group"><label class="form-label">Received Qty *</label>
          <input id="rcv-qty" type="number" class="form-input" value="1" min="0"></div>
        <div class="form-group"><label class="form-label">Damage Qty</label>
          <input id="rcv-dmg" type="number" class="form-input" value="0" min="0"></div>
        <div class="form-group"><label class="form-label">Short Qty</label>
          <input id="rcv-short" type="number" class="form-input" value="0" min="0"></div>
      </div>
      <div class="form-grid form-grid-3">
        <div class="form-group"><label class="form-label">Received Date *</label>
          <input id="rcv-date" type="date" class="form-input" value="${today()}"></div>
        <div class="form-group"><label class="form-label">QC Status *</label>
          <select id="rcv-qc" class="form-select"><option>Pass</option><option>Fail</option></select></div>
        <div class="form-group"><label class="form-label">Put-Away Bin *</label>
          <input id="rcv-loc" class="form-input" placeholder="e.g. A1-B3-S2"></div>
      </div>
      <div class="form-group"><label class="form-label">Notes</label>
        <textarea id="rcv-notes" class="form-textarea" placeholder="Supplier ref, condition notes…"></textarea></div>
      <button class="btn btn-primary" onclick="submitReceiving(${poId})">📥 Submit for Approval</button>
    </div>
  `);
  onRcvItemChange(poId);
}

function onRcvItemChange(poId) {
  const sel  = $('rcv-item-sel')?.value;
  if (!sel) return;
  const [itemId, sku] = sel.split('|');
  const items = getPoPendingItems(poId);
  const item  = items.find(i=>i.id==+itemId);
  if (!item) return;
  if ($('rcv-sku'))  $('rcv-sku').value  = item.sku;
  if ($('rcv-desc')) $('rcv-desc').value = item.description.slice(0,30);
  if ($('rcv-bal'))  $('rcv-bal').value  = item.balance_quantity;
  if ($('rcv-qty'))  $('rcv-qty').max    = item.balance_quantity;
}

function submitReceiving(poId) {
  const sel    = $('rcv-item-sel')?.value;
  if (!sel) { toast('Select a line item','error'); return; }
  const [itemId, sku] = sel.split('|');
  const recvQty  = parseInt($('rcv-qty')?.value)||0;
  const dmgQty   = parseInt($('rcv-dmg')?.value)||0;
  const shortQty = parseInt($('rcv-short')?.value)||0;
  const date     = $('rcv-date')?.value;
  const qc       = $('rcv-qc')?.value;
  const loc      = $('rcv-loc')?.value?.trim();
  const notes    = $('rcv-notes')?.value||'';

  if (recvQty <= 0) { toast('Received qty must be > 0','error'); return; }
  if (!loc) { toast('Put-Away Bin location is required','error'); return; }
  if (dmgQty > recvQty) { toast('Damage qty cannot exceed received qty','error'); return; }

  const res = createReceiving(poId, +itemId, sku, recvQty, dmgQty, shortQty, date, qc, loc, notes);
  if (res.ok) {
    toast(`✅ ${res.num} submitted for approval`,'success');
    if (dmgQty>0) toast(`⚠️ ${dmgQty} damaged units recorded`,'warn');
    if (shortQty>0) toast(`📉 ${shortQty} units short`,'warn');
    renderReceiving();
  } else {
    toast('Error: ' + res.error,'error');
  }
}

function renderPendingApprovals() {
  const el   = $('rcv-tab-approvals');
  if (!el) return;
  const pend = getReceivingRecords('Pending');
  if (!pend.length) {
    html(el, empty('✅','No Pending Approvals','All records have been processed'));
    return;
  }
  html(el, alertBox(`⚠️ <strong>${pend.length} record(s)</strong> awaiting approval. Inventory is NOT updated until Approved.`,'warn') +
    pend.map(r => {
      const good = Math.max(0, r.received_quantity - r.damage_quantity);
      return `<div class="card" style="margin-bottom:12px;">
        <div style="display:grid;grid-template-columns:3fr 2fr 2fr;gap:16px;align-items:start;">
          <div>
            ${mkInfoBox([
              ['RCV Number',`<strong>${r.receiving_number}</strong>`],
              ['PO Number',r.po_number],['Supplier',r.supplier_name],
              ['SKU',r.sku],['Part',r.part_description?.slice(0,30)],
              ['Recv Date',r.received_date],['Bin',r.location||'—'],
            ])}
          </div>
          <div>
            ${mkInfoBox([
              ['Received',`<span style="color:var(--blue3);">${r.received_quantity}</span>`],
              ['Damaged',`<span style="color:var(--red);">${r.damage_quantity}</span>`],
              ['Short',`<span style="color:var(--yellow);">${r.short_quantity}</span>`],
              ['Good Units',`<strong style="color:var(--green);">${good}</strong>`],
              ['QC',badge(r.qc_status)],
            ])}
          </div>
          <div>
            ${alertBox(`Approving adds <strong>${good} units</strong> of ${r.sku} to inventory.`,'info')}
            <button class="btn btn-success btn-full" style="margin-bottom:8px;" onclick="doApprove(${r.id})">✅ Approve</button>
            <input id="rej-reason-${r.id}" class="form-input" style="margin-bottom:6px;" placeholder="Rejection reason…">
            <button class="btn btn-danger btn-full" onclick="doReject(${r.id})">❌ Reject</button>
          </div>
        </div>
      </div>`;
    }).join('')
  );
}

function doApprove(id) {
  const res = approveReceiving(id);
  if (res.ok) { toast(res.msg,'success'); renderReceiving(); }
  else toast('Error: '+res.error,'error');
}

function doReject(id) {
  const reason = $(`rej-reason-${id}`)?.value||'';
  rejectReceiving(id, reason);
  toast('Record rejected','warn');
  renderReceiving();
}

function renderReceivingHistory() {
  const el = $('rcv-tab-history');
  if (!el) return;
  const recs = getReceivingRecords();
  const appr = recs.filter(r=>r.status==='Approved').length;
  const pend = recs.filter(r=>r.status==='Pending').length;
  const rej  = recs.filter(r=>r.status==='Rejected').length;
  const metrics = recs.length ? `<div class="metrics metrics-4">
    ${mkMetric('Total',recs.length)}${mkMetric('✅ Approved',appr)}
    ${mkMetric('⏳ Pending',pend)}${mkMetric('❌ Rejected',rej)}
  </div><hr>` : '';
  html(el, metrics + mkTable(recs, [
    {key:'receiving_number',label:'RCV #'},{key:'po_number',label:'PO #'},
    {key:'supplier_name',label:'Supplier'},{key:'sku',label:'SKU'},
    {key:'received_quantity',label:'Recv'},{key:'damage_quantity',label:'Dmg'},
    {key:'short_quantity',label:'Short'},{key:'qc_status',label:'QC',fmt:badge},
    {key:'received_date',label:'Date'},{key:'location',label:'Bin'},
    {key:'status',label:'Status',fmt:badge},
  ]));
}

/* ══════════════════════════════════════════════════════════
   OUTBOUND DISPATCH
══════════════════════════════════════════════════════════ */
function renderDispatch() {
  html($('page-outbound-dispatch'), `
    <div class="hero">
      <div class="hero-icon">📤</div>
      <div class="hero-title">Outbound Dispatch</div>
      <div class="hero-sub">Create dispatch orders · Pick → Pack → Dispatch workflow · Real-time stock deduction</div>
    </div>
    ${tabs('dsp',[['create','  ➕ Create Order  '],['active','  🔄 Active Orders  '],['history','  📋 History  ']],'create')}
  `);
  renderCreateDispatch();
  renderActiveDispatch();
  renderDispatchHistory();
}

function renderCreateDispatch() {
  const el  = $('dsp-tab-create');
  if (!el) return;
  const inv = getInventorySummary().filter(i=>i.available_stock>0);
  if (!inv.length) {
    html(el, alertBox('⚠️ No parts currently in stock. Receive goods via an approved PO first.','warn'));
    return;
  }
  const partOpts = ['<option value="">— Select —</option>',
    ...inv.map(i=>`<option value="${i.sku}">[${i.sku}] ${i.description} (Avail: ${i.available_stock} ${i.unit})</option>`)
  ].join('');

  html(el, `
    <div class="two-col-eq">
      <div>
        <div class="section-title">🚚 Dispatch Order Header</div>
        <div class="form-grid" style="gap:12px;">
          <div class="form-group"><label class="form-label">Customer / Recipient *</label>
            <input id="dsp-customer" class="form-input" placeholder="e.g. Apex Auto Repairs Ltd."></div>
          <div class="form-group"><label class="form-label">Dispatch Date *</label>
            <input id="dsp-date" type="date" class="form-input" value="${today()}"></div>
          <div class="form-group"><label class="form-label">Notes</label>
            <textarea id="dsp-notes" class="form-textarea" placeholder="Delivery instructions…"></textarea></div>
          <hr>
          <div class="section-title">📦 Add Line Item</div>
          <div class="form-group"><label class="form-label">Part *</label>
            <select id="dsp-part" class="form-select" onchange="onDspPartChange()">${partOpts}</select></div>
          <div id="dsp-avail-hint"></div>
          <div class="form-group"><label class="form-label">Quantity *</label>
            <input id="dsp-qty" type="number" class="form-input" value="1" min="1"></div>
          <div class="form-grid form-grid-2">
            <button class="btn btn-full" onclick="dspAddItem()">➕ Add Item</button>
            <button class="btn btn-primary btn-full" onclick="dspCreate()">📤 Create Order</button>
          </div>
        </div>
      </div>
      <div>
        <div class="section-title">🛒 Order Preview</div>
        <div id="dsp-preview"></div>
      </div>
    </div>
  `);
  renderDspPreview();
}

function onDspPartChange() {
  const sku = $('dsp-part')?.value;
  const el  = $('dsp-avail-hint');
  if (!el) return;
  if (!sku) { html(el,''); return; }
  const inv = getInventorySummary().find(i=>i.sku===sku);
  if (inv) {
    html(el, alertBox(`Available quantity: <strong>${inv.available_stock} ${inv.unit}</strong>`,'info'));
    if ($('dsp-qty')) { $('dsp-qty').max = inv.available_stock; $('dsp-qty').value = Math.min(1, inv.available_stock); }
  }
}

function renderDspPreview() {
  const el = $('dsp-preview');
  if (!el) return;
  if (!pendingDspItems.length) {
    html(el, empty('🚚','No items added yet','Select a part and click ➕ Add Item'));
    return;
  }
  const totQty = pendingDspItems.reduce((a,i)=>a+i.quantity,0);
  const tbl = mkTable(pendingDspItems, [
    {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,25)},
    {key:'unit',label:'Unit'},{key:'quantity',label:'Qty'},{key:'available',label:'Available'},
    {key:'sku',label:'',fmt:(_,r)=>`<button class="btn btn-sm btn-danger" onclick="dspRemoveItem('${r.sku}')">🗑</button>`},
  ]);
  html(el, tbl + mkInfoBox([['Lines',pendingDspItems.length],['Total Units',formatNum(totQty)]]) +
    `<br><button class="btn btn-danger btn-full" onclick="dspClearItems()">🗑 Clear All</button>`
  );
}

function dspAddItem() {
  const sku = $('dsp-part')?.value;
  const qty = parseInt($('dsp-qty')?.value);
  if (!sku) { toast('Please select a part','error'); return; }
  if (isNaN(qty)||qty<1) { toast('Quantity must be ≥ 1','error'); return; }
  if (pendingDspItems.find(i=>i.sku===sku)) { toast('SKU already in order','warn'); return; }
  const inv = getInventorySummary().find(i=>i.sku===sku);
  if (!inv || qty > inv.available_stock) { toast(`Insufficient stock. Available: ${inv?.available_stock||0}`,'error'); return; }
  pendingDspItems.push({ sku, description:inv.description, unit:inv.unit, quantity:qty, available:inv.available_stock });
  renderDspPreview();
}

function dspRemoveItem(sku) { pendingDspItems = pendingDspItems.filter(i=>i.sku!==sku); renderDspPreview(); }
function dspClearItems()    { pendingDspItems = []; renderDspPreview(); }

function dspCreate() {
  const customer = $('dsp-customer')?.value?.trim();
  const date     = $('dsp-date')?.value;
  const notes    = $('dsp-notes')?.value||'';
  if (!customer) { toast('Customer name is required','error'); return; }
  if (!pendingDspItems.length) { toast('Add at least one item','error'); return; }
  const res = createDispatchOrder(customer, date, pendingDspItems, notes);
  if (res.ok) {
    pendingDspItems = [];
    toast(`🎉 ${res.num} created! Stock reserved.`,'success');
    renderDspPreview();
    renderActiveDispatch();
  } else {
    toast('Error: '+res.error,'error');
  }
}

function renderActiveDispatch() {
  const el     = $('dsp-tab-active');
  if (!el) return;
  const orders = getDispatchOrders().filter(o=>o.status!=='Dispatched');
  if (!orders.length) {
    html(el, empty('📭','No Active Dispatch Orders','Create a dispatch order from the first tab'));
    return;
  }
  html(el, orders.map(o => {
    const d     = getDispatchDetails(o.id);
    const st    = o.status;
    const steps = {
      'Pending': [['Create','done'],['Pick','active'],['Pack','todo'],['Dispatch','todo']],
      'Picking': [['Create','done'],['Pick','done'],['Pack','active'],['Dispatch','todo']],
      'Packing': [['Create','done'],['Pick','done'],['Pack','done'],['Dispatch','active']],
    };
    const wf   = wfHtml(steps[st]||[['Create','done'],['Pick','done'],['Pack','done'],['Dispatch','done']]);
    let actionBtn = '';
    if (st==='Pending') actionBtn = `<button class="btn btn-primary btn-full" onclick="dspStep(${o.id},'picking')">📋 Confirm Picking</button>`;
    else if (st==='Picking') actionBtn = `${alertBox('✅ Picking done.','success')}<button class="btn btn-primary btn-full" onclick="dspStep(${o.id},'packing')">📦 Confirm Packing</button>`;
    else if (st==='Packing') actionBtn = `${alertBox('✅ Packing done. Stock will be deducted!','warn')}<button class="btn btn-primary btn-full" onclick="dspStep(${o.id},'dispatch')">🚚 Confirm Dispatch</button>`;

    return `<div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div><strong style="color:var(--text);">${o.dispatch_number}</strong> &nbsp;·&nbsp; ${o.customer} &nbsp;·&nbsp; ${badge(st)}</div>
      </div>
      ${wf}
      <div style="display:grid;grid-template-columns:2fr 3fr 2fr;gap:16px;">
        <div>${mkInfoBox([
          ['Dispatch #',d.dispatch_number],['Customer',d.customer],['Date',d.dispatch_date],
          ['Picking',d.picking_confirmed?'✅':'⏳'],['Packing',d.packing_confirmed?'✅':'⏳'],
          ['Dispatched',d.dispatch_confirmed?'✅':'⏳'],
        ])}</div>
        <div>${mkTable(d.items,[
          {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,28)},
          {key:'ordered_quantity',label:'Qty'},
        ])}</div>
        <div>${actionBtn}</div>
      </div>
    </div>`;
  }).join(''));
}

function dspStep(id, step) {
  const res = updateDispatchStep(id, step);
  if (res.ok) {
    toast(step==='dispatch'?'🎉 Order dispatched! Inventory updated.':'Step confirmed!','success');
    renderDispatch();
  } else {
    toast('Error: '+res.error,'error');
  }
}

function renderDispatchHistory() {
  const el     = $('dsp-tab-history');
  if (!el) return;
  const orders = getDispatchOrders();
  const disp   = orders.filter(o=>o.status==='Dispatched').length;
  const prog   = orders.filter(o=>!['Dispatched','Pending'].includes(o.status)).length;
  const pend   = orders.filter(o=>o.status==='Pending').length;
  const metrics= orders.length?`<div class="metrics metrics-4">
    ${mkMetric('Total',orders.length)}${mkMetric('✅ Dispatched',disp)}
    ${mkMetric('🔄 In Progress',prog)}${mkMetric('⏳ Pending',pend)}
  </div><hr>`:'';
  html(el, metrics + mkTable(orders,[
    {key:'dispatch_number',label:'DSP #'},{key:'customer',label:'Customer'},
    {key:'dispatch_date',label:'Date'},{key:'item_count',label:'Lines'},
    {key:'total_qty',label:'Qty',fmt:formatNum},
    {key:'picking_confirmed',label:'Pick',fmt:v=>v?'✅':'—'},
    {key:'packing_confirmed',label:'Pack',fmt:v=>v?'✅':'—'},
    {key:'dispatch_confirmed',label:'Dispatch',fmt:v=>v?'✅':'—'},
    {key:'status',label:'Status',fmt:badge},
  ]));
}

/* ══════════════════════════════════════════════════════════
   INVENTORY
══════════════════════════════════════════════════════════ */
function renderInventory() {
  html($('page-inventory'), `
    <div class="hero">
      <div class="hero-icon">📊</div>
      <div class="hero-title">Inventory Management</div>
      <div class="hero-sub">Live stock levels · PO pending · Reserved stock · Movement history · Reorder alerts</div>
    </div>
    ${tabs('inv',[['overview','  📦 Stock Overview  '],['movements','  🔄 Movements  '],['alerts','  🔔 Reorder Alerts  '],['analytics','  📈 Analytics  ']],'overview')}
  `);
  renderStockOverview();
  renderMovements();
  renderAlerts();
  renderAnalytics();
}

function renderStockOverview() {
  const el  = $('inv-tab-overview');
  if (!el) return;
  const inv = getInventorySummary();
  const inSt  = inv.filter(i=>i.current_stock>i.reorder_level).length;
  const low   = inv.filter(i=>i.current_stock>0&&i.current_stock<=i.reorder_level).length;
  const oos   = inv.filter(i=>i.current_stock===0).length;
  const totU  = inv.reduce((a,i)=>a+i.current_stock,0);
  const totA  = inv.reduce((a,i)=>a+i.available_stock,0);
  html(el, `<div class="metrics metrics-5">
    ${mkMetric('Total SKUs',inv.length)}${mkMetric('🟢 In Stock',inSt)}
    ${mkMetric('🟡 Low Stock',low)}${mkMetric('🔴 Out of Stock',oos)}
    ${mkMetric('📦 Total Units',formatNum(totU),`${formatNum(totA)} Available`)}
  </div><hr>` +
  mkTable(inv,[
    {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,30)},
    {key:'category',label:'Category'},{key:'unit',label:'Unit'},
    {key:'reorder_level',label:'Reorder'},
    {key:'current_stock',label:'On Hand',fmt:formatNum},
    {key:'reserved_stock',label:'Reserved',fmt:formatNum},
    {key:'available_stock',label:'Available',fmt:formatNum},
    {key:'pending_po_qty',label:'PO Pending',fmt:formatNum},
    {key:'current_stock',label:'Status',fmt:(v,r)=>{
      if(v===0) return badge('Out');
      if(v<=r.reorder_level) return badge('Low');
      return badge('In Stock');
    }},
  ]));
}

function renderMovements() {
  const el  = $('inv-tab-movements');
  if (!el) return;
  const mvs = getStockMovements();
  const inT = mvs.filter(m=>m.movement_type==='IN').reduce((a,m)=>a+m.quantity,0);
  const outT= mvs.filter(m=>m.movement_type==='OUT').reduce((a,m)=>a+m.quantity,0);
  const metrics= mvs.length?`<div class="metrics metrics-3">
    ${mkMetric('Total Movements',mvs.length)}
    ${mkMetric('📥 Total Received','+'+formatNum(inT))}
    ${mkMetric('📤 Total Dispatched','−'+formatNum(outT))}
  </div><hr>`:'';
  html(el, metrics + mkTable(mvs,[
    {key:'movement_date',label:'Date/Time',fmt:v=>(v||'').slice(0,16)},
    {key:'sku',label:'SKU'},
    {key:'description',label:'Description',fmt:v=>(v||'').slice(0,28)},
    {key:'movement_type',label:'Type',fmt:v=>v==='IN'?'📥 IN':'📤 OUT'},
    {key:'reference_number',label:'Reference'},
    {key:'quantity',label:'Qty',fmt:(v,r)=>r.movement_type==='IN'?`<span style="color:var(--green);">+${v}</span>`:`<span style="color:var(--red);">−${v}</span>`},
    {key:'balance',label:'Balance'},
    {key:'notes',label:'Notes',fmt:v=>(v||'').slice(0,30)},
  ]));
}

function renderAlerts() {
  const el  = $('inv-tab-alerts');
  if (!el) return;
  const inv = getInventorySummary();
  const oos = inv.filter(i=>i.current_stock===0);
  const low = inv.filter(i=>i.current_stock>0&&i.current_stock<=i.reorder_level);
  const ok  = inv.filter(i=>i.current_stock>i.reorder_level);

  const oosSec = `<div class="section-title">🔴 Out of Stock</div>
    ${oos.length ? alertBox(`🚨 ${oos.length} part(s) out of stock — action required!`,'danger') + mkTable(oos,[
      {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,35)},
      {key:'category',label:'Category'},{key:'reorder_level',label:'Reorder Lvl'},
      {key:'pending_po_qty',label:'PO Pending'},
    ]) : alertBox('✅ No parts are out of stock.','success')}`;

  const lowSec = `<hr><div class="section-title">🟡 Low Stock — At or Below Reorder Level</div>
    ${low.length ? alertBox(`⚠️ ${low.length} part(s) below reorder level.`,'warn') + mkTable(low,[
      {key:'sku',label:'SKU'},{key:'description',label:'Description',fmt:v=>v.slice(0,35)},
      {key:'category',label:'Category'},{key:'current_stock',label:'On Hand'},
      {key:'reorder_level',label:'Reorder Lvl'},{key:'pending_po_qty',label:'PO Pending'},
    ]) : alertBox('✅ No parts below reorder level.','success')}`;

  html(el, oosSec + lowSec + `<hr><div class="section-title">🟢 In Stock — ${ok.length} part(s) above reorder level</div>`);
}

function renderAnalytics() {
  const el  = $('inv-tab-analytics');
  if (!el) return;
  html(el, `
    <div class="two-col-eq">
      <div>
        <div class="section-title">📊 Stock by Category</div>
        <div id="chart-category" style="height:300px;"></div>
        <div class="section-title" style="margin-top:20px;">🍩 Category Distribution</div>
        <div id="chart-donut" style="height:280px;"></div>
      </div>
      <div>
        <div class="section-title">🏆 Top 15 Parts by On-Hand Stock</div>
        <div id="chart-top15" style="height:380px;"></div>
        <div class="section-title" style="margin-top:20px;">💊 Stock Health</div>
        <div id="chart-health" style="height:200px;"></div>
      </div>
    </div>
  `);

  if (typeof Plotly === 'undefined') return;
  const inv   = getInventorySummary();
  const cats  = [...new Set(inv.map(i=>i.category))];
  const layout = { paper_bgcolor:'#0d1117', plot_bgcolor:'#161b22', font:{color:'#8b949e'}, margin:{l:20,r:20,t:20,b:40}, legend:{bgcolor:'#161b22',bordercolor:'#21262d'} };

  // Category bar
  const catData = cats.map(cat => {
    const items = inv.filter(i=>i.category===cat);
    return { name:cat, x:[cat], y:[items.reduce((a,i)=>a+i.current_stock,0)], type:'bar' };
  });
  Plotly.newPlot('chart-category', catData, {...layout, barmode:'group', xaxis:{gridcolor:'#21262d'}, yaxis:{gridcolor:'#21262d'}, height:300, showlegend:true}, {responsive:true,displayModeBar:false});

  // Donut
  const catAvail = cats.map(cat => inv.filter(i=>i.category===cat).reduce((a,i)=>a+i.available_stock,0));
  Plotly.newPlot('chart-donut', [{values:catAvail,labels:cats,type:'pie',hole:.55,textposition:'inside',textinfo:'percent+label'}],
    {...layout, height:280}, {responsive:true,displayModeBar:false});

  // Top 15
  const top15 = [...inv].sort((a,b)=>b.current_stock-a.current_stock).slice(0,15);
  Plotly.newPlot('chart-top15', [{x:top15.map(i=>i.current_stock),y:top15.map(i=>i.sku),type:'bar',orientation:'h',
    marker:{color:'#388bfd'}}],
    {...layout, xaxis:{gridcolor:'#21262d',title:'On Hand'}, yaxis:{gridcolor:'#21262d',categoryorder:'total ascending'}, height:380}, {responsive:true,displayModeBar:false});

  // Health gauge
  const total = inv.length||1;
  const pOk   = inv.filter(i=>i.current_stock>i.reorder_level).length;
  const pLow  = inv.filter(i=>i.current_stock>0&&i.current_stock<=i.reorder_level).length;
  const pOos  = inv.filter(i=>i.current_stock===0).length;
  Plotly.newPlot('chart-health', [{
    x:[+(pOk/total*100).toFixed(1), +(pLow/total*100).toFixed(1), +(pOos/total*100).toFixed(1)],
    y:['🟢 In Stock','🟡 Low Stock','🔴 Out of Stock'],
    type:'bar', orientation:'h',
    marker:{color:['#3fb950','#d29922','#f85149']},
    text:[pOk/total*100+'%',pLow/total*100+'%',pOos/total*100+'%'],
    textposition:'auto',
  }], {...layout, xaxis:{gridcolor:'#21262d',title:'% of SKUs'}, yaxis:{gridcolor:'#21262d'}, height:200, showlegend:false}, {responsive:true,displayModeBar:false});
}

/* ── Init ── */
window.addEventListener('DOMContentLoaded', async () => {
  try {
    await initDB();
    $('loading').style.display = 'none';
    document.querySelectorAll('.page').forEach(p => p.style.display='none');
    $('page-dashboard').style.display = 'block';
    renderDashboard();
  } catch(e) {
    console.error('Init error:', e);
    html($('loading'), `<div style="color:var(--red);text-align:center;"><div style="font-size:32px;">⚠️</div><br><strong>Failed to initialize database</strong><br><small>${e.message}</small></div>`);
  }
});

document.querySelectorAll && document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => showPage(item.dataset.page));
  });
});
