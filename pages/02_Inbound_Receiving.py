"""
AutoWMS — Inbound Receiving Module
RULE: All receiving MUST be linked to an approved Purchase Order.
Manual receiving without a PO is structurally and visually blocked.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date

from database import (initialize_database, seed_sample_data,
                       get_open_pos, get_po_details, get_po_pending_items,
                       create_receiving, approve_receiving, reject_receiving,
                       get_receiving_records)
from utils import apply_styles, page_hero, sidebar_brand, badge, alert, workflow_html

st.set_page_config(
    page_title="Inbound Receiving — AutoWMS", page_icon="📥", layout="wide"
)
apply_styles()
initialize_database()
seed_sample_data()
sidebar_brand()

# ─── Session state ────────────────────────────────────────────────────────────
for key, default in [
    ("rcv_po_id",      None),
    ("rcv_po_item_id", None),
    ("reject_reason",  ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

page_hero("📥", "Inbound Receiving",
          "PO-controlled receiving · Damage & shortage tracking · QC inspection · Bin put-away")

# ─── Permanent policy banner ──────────────────────────────────────────────────
st.markdown("""
<div class="blocked-zone" style="margin-bottom:24px; padding:22px 32px;">
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
        <div style="font-size:36px;">🔒</div>
        <div>
            <div class="blocked-title" style="font-size:16px; margin:0 0 4px;">
                Manual Receiving is BLOCKED
            </div>
            <div class="blocked-desc" style="margin:0; font-size:13px;">
                All inbound stock must be received against an approved Purchase Order.
                Select an Open or Partial PO below to begin the receiving process.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_receive, tab_approvals, tab_history = st.tabs([
    "  📦  Receive from PO  ",
    "  ✅  Pending Approvals  ",
    "  📋  Receiving History  ",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Receive from PO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_receive:
    open_pos = get_open_pos()

    if not open_pos:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-msg">No Open Purchase Orders</div>
            <div class="empty-sub">
                Create a Purchase Order first. Only Open or Partial POs can be received against.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # ── Step 1: Select PO ─────────────────────────────────────────────────────
    st.markdown("### Step 1 — Select a Purchase Order")

    po_opts = {
        f"{p['po_number']}  |  {p['supplier_name']}  [{p['status']}]  "
        f"ETA: {p['expected_delivery_date']}": p["id"]
        for p in open_pos
    }
    sel_po_label = st.selectbox(
        "Choose an Open / Partial PO *",
        ["— Select a PO to start receiving —"] + list(po_opts.keys()),
        key="sel_po_rcv",
    )

    if sel_po_label == "— Select a PO to start receiving —":
        st.markdown(alert(
            "Select a PO above to view its pending items and begin receiving.", "info"
        ), unsafe_allow_html=True)
        st.stop()

    po_id = po_opts[sel_po_label]
    po    = get_po_details(po_id)

    # ── PO summary ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Step 2 — PO Details & Pending Items")

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Supplier",  po["supplier_name"])
    sc2.metric("PO Number", po["po_number"])
    sc3.metric("PO Status", po["status"])
    sc4.metric("Expected",  po["expected_delivery_date"] or "—")

    pending_items = get_po_pending_items(po_id)

    if not pending_items:
        st.markdown(alert("All items on this PO have been fully received. PO should be Closed.", "info"),
                    unsafe_allow_html=True)
        st.stop()

    # Show pending items table
    df_pend = pd.DataFrame(pending_items)
    disp_pend = df_pend[[
        "sku", "description", "category", "unit",
        "ordered_quantity", "received_quantity", "balance_quantity", "unit_cost"
    ]].copy()
    disp_pend.columns = [
        "SKU", "Description", "Category", "Unit",
        "Ordered", "Already Received", "Open Balance", "Unit Cost"
    ]
    disp_pend["Unit Cost"] = disp_pend["Unit Cost"].map("${:,.2f}".format)
    st.dataframe(disp_pend, use_container_width=True, hide_index=True)

    # ── Step 3: Receiving form ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Step 3 — Enter Receiving Details")

    item_opts = {
        f"[{it['sku']}]  {it['description']}  "
        f"(Balance: {it['balance_quantity']} {it['unit']})": it
        for it in pending_items
    }

    with st.form("receiving_form", clear_on_submit=True):
        sel_item_label = st.selectbox(
            "Select Line Item to Receive *",
            list(item_opts.keys()),
            key="rcv_item_sel",
        )
        sel_item = item_opts[sel_item_label]

        # Auto-populate read-only info
        ai1, ai2, ai3, ai4 = st.columns(4)
        ai1.text_input("SKU (auto)",         value=sel_item["sku"],         disabled=True)
        ai2.text_input("Description (auto)", value=sel_item["description"][:28], disabled=True)
        ai3.text_input("Category (auto)",    value=sel_item["category"],    disabled=True)
        ai4.text_input("Open Balance (auto)", value=str(sel_item["balance_quantity"]), disabled=True)

        st.markdown("**Enter Received Quantities:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            recv_qty  = st.number_input(
                "Received Quantity *",
                min_value=0, max_value=sel_item["balance_quantity"],
                value=min(10, sel_item["balance_quantity"]), step=1
            )
        with c2:
            dmg_qty   = st.number_input(
                "Damage Quantity",
                min_value=0, max_value=sel_item["balance_quantity"],
                value=0, step=1
            )
        with c3:
            short_qty = st.number_input(
                "Short Quantity",
                min_value=0, max_value=sel_item["balance_quantity"],
                value=0, step=1
            )

        st.markdown("**Inspection & Location:**")
        d1, d2, d3 = st.columns(3)
        with d1:
            recv_date = st.date_input("Received Date *", value=date.today())
        with d2:
            qc_status = st.selectbox("QC Status *", ["Pass", "Fail"])
        with d3:
            location  = st.text_input(
                "Put-Away Rack / Bin *",
                placeholder="e.g. A1-B3-S2"
            )

        notes = st.text_area(
            "Notes / Remarks",
            placeholder="Supplier reference, condition notes, etc.",
            height=70
        )

        submitted = st.form_submit_button(
            "📥  Submit for Approval", type="primary", use_container_width=True
        )

    if submitted:
        errs = []
        if recv_qty <= 0:
            errs.append("Received Quantity must be greater than 0.")
        if dmg_qty > recv_qty:
            errs.append("Damage Quantity cannot exceed Received Quantity.")
        if short_qty > (sel_item["balance_quantity"] - recv_qty):
            errs.append("Short Quantity seems inconsistent with balance.")
        if not location.strip():
            errs.append("Put-Away location (Rack/Bin) is required.")
        if recv_qty + dmg_qty > sel_item["balance_quantity"]:
            errs.append(
                f"Total of Received ({recv_qty}) + Damage ({dmg_qty}) "
                f"exceeds open balance ({sel_item['balance_quantity']})."
            )

        if errs:
            for e in errs:
                st.error(e)
        else:
            good_qty = recv_qty - dmg_qty
            rcv_num, err = create_receiving(
                po_id, sel_item["id"], sel_item["sku"],
                recv_qty, dmg_qty, short_qty,
                recv_date, qc_status, location.strip(), notes
            )
            if rcv_num:
                st.success(
                    f"✅  Receiving record **{rcv_num}** submitted for approval.  "
                    f"Good units pending inventory update: **{good_qty}**."
                )
                if dmg_qty > 0:
                    st.markdown(
                        alert(f"⚠️  {dmg_qty} damaged units recorded — these will be excluded from inventory on approval.", "warn"),
                        unsafe_allow_html=True
                    )
                if short_qty > 0:
                    st.markdown(
                        alert(f"📉  {short_qty} short quantity recorded — supplier may need to be contacted.", "warn"),
                        unsafe_allow_html=True
                    )
            else:
                st.error(f"Failed to create receiving record: {err}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Pending Approvals
# ═══════════════════════════════════════════════════════════════════════════════
with tab_approvals:
    pending = get_receiving_records(status="Pending")

    if not pending:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">✅</div>
            <div class="empty-msg">No Pending Approvals</div>
            <div class="empty-sub">All receiving records have been processed.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert alert-warn">
            ⚠️&nbsp; <strong>{len(pending)} receiving record(s) awaiting approval.</strong>
            Inventory is NOT updated until a record is Approved.
        </div>
        """, unsafe_allow_html=True)

        for rec in pending:
            good_qty = max(0, rec["received_quantity"] - rec["damage_quantity"])

            with st.expander(
                f"🔶  {rec['receiving_number']}  ·  {rec['sku']}  "
                f"·  {rec['part_description'][:30]}  ·  Recv: {rec['received_quantity']}",
                expanded=False
            ):
                c_info, c_qty, c_action = st.columns([3, 2, 2], gap="medium")

                with c_info:
                    st.markdown(f"""
                    <div class="info-box">
                        <div class="info-row"><span class="info-key">PO Number</span>
                            <span class="info-val">{rec['po_number']}</span></div>
                        <div class="info-row"><span class="info-key">Supplier</span>
                            <span class="info-val">{rec['supplier_name']}</span></div>
                        <div class="info-row"><span class="info-key">SKU</span>
                            <span class="info-val">{rec['sku']}</span></div>
                        <div class="info-row"><span class="info-key">Part</span>
                            <span class="info-val">{rec['part_description']}</span></div>
                        <div class="info-row"><span class="info-key">Received Date</span>
                            <span class="info-val">{rec['received_date']}</span></div>
                        <div class="info-row"><span class="info-key">Location</span>
                            <span class="info-val">{rec['location'] or '—'}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                with c_qty:
                    qc_badge = badge(rec["qc_status"])
                    st.markdown(f"""
                    <div class="info-box">
                        <div class="info-row"><span class="info-key">Received</span>
                            <span class="info-val" style="color:#58a6ff;">{rec['received_quantity']}</span></div>
                        <div class="info-row"><span class="info-key">Damage</span>
                            <span class="info-val" style="color:#f85149;">{rec['damage_quantity']}</span></div>
                        <div class="info-row"><span class="info-key">Short</span>
                            <span class="info-val" style="color:#d29922;">{rec['short_quantity']}</span></div>
                        <div class="info-row"><span class="info-key">Good Units</span>
                            <span class="info-val" style="color:#3fb950; font-weight:700;">{good_qty}</span></div>
                        <div class="info-row"><span class="info-key">QC Status</span>
                            <span class="info-val">{qc_badge}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                with c_action:
                    st.markdown("**Approval Action:**")
                    st.markdown(f"""
                    <div class="alert alert-info" style="font-size:12px;">
                        Approving will add <strong>{good_qty} units</strong>
                        of {rec['sku']} to inventory.
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        "✅  Approve", key=f"appr_{rec['id']}",
                        type="primary", use_container_width=True
                    ):
                        ok, msg = approve_receiving(rec["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                    st.markdown("<br>", unsafe_allow_html=True)
                    rej_reason = st.text_input(
                        "Rejection reason:", key=f"rej_r_{rec['id']}",
                        placeholder="e.g. Wrong part delivered"
                    )
                    if st.button(
                        "❌  Reject", key=f"rej_{rec['id']}",
                        use_container_width=True
                    ):
                        reject_receiving(rec["id"], rej_reason)
                        st.warning(f"Receiving {rec['receiving_number']} rejected.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Receiving History
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    hf1, hf2 = st.columns([2, 4])
    with hf1:
        hist_filter = st.selectbox(
            "Filter by Status",
            ["All", "Approved", "Pending", "Rejected"],
            key="rcv_hist_filter"
        )

    history = get_receiving_records(status=hist_filter if hist_filter != "All" else None)

    if not history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <div class="empty-msg">No receiving records found</div>
            <div class="empty-sub">Records will appear here as goods are received.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Summary
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Records",  len(history))
        m2.metric("✅ Approved",    sum(1 for r in history if r["status"] == "Approved"))
        m3.metric("⏳ Pending",     sum(1 for r in history if r["status"] == "Pending"))
        m4.metric("❌ Rejected",    sum(1 for r in history if r["status"] == "Rejected"))

        st.markdown("---")

        df_hist = pd.DataFrame(history)
        disp = df_hist[[
            "receiving_number", "po_number", "supplier_name", "sku",
            "part_description", "received_quantity", "damage_quantity",
            "short_quantity", "qc_status", "received_date", "location",
            "status", "approved_at", "created_at"
        ]].copy()
        disp.columns = [
            "RCV Number", "PO Number", "Supplier", "SKU",
            "Part", "Received", "Damaged",
            "Short", "QC", "Recv Date", "Location",
            "Status", "Approved At", "Created"
        ]
        st.dataframe(disp, use_container_width=True, height=500, hide_index=True)
