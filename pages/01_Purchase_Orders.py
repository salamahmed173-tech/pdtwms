"""
AutoWMS — Purchase Order Module
Create and manage supplier purchase orders.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import (initialize_database, seed_sample_data,
                       get_suppliers, get_parts,
                       create_purchase_order, get_purchase_orders, get_po_details)
from utils import apply_styles, page_hero, sidebar_brand, badge, info_box

st.set_page_config(page_title="Purchase Orders — AutoWMS", page_icon="📦", layout="wide")
apply_styles()
initialize_database()
seed_sample_data()
sidebar_brand()

# ─── Session state ────────────────────────────────────────────────────────────
if "po_items" not in st.session_state:
    st.session_state.po_items = []

page_hero("📦", "Purchase Orders",
          "Create supplier purchase orders · View order status · Track line-item fulfilment")

tab_create, tab_view, tab_detail = st.tabs([
    "  ➕  Create PO  ",
    "  📋  View All POs  ",
    "  🔍  PO Detail  ",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Create PO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_create:
    suppliers = get_suppliers()
    parts     = get_parts()

    if not suppliers:
        st.error("No suppliers found. Ensure the database is seeded.")
        st.stop()

    supplier_map = {s["name"]: s["id"] for s in suppliers}
    parts_map    = {f"[{p['sku']}]  {p['description']}  ({p['category']})": p for p in parts}

    col_form, col_preview = st.columns([1, 1], gap="large")

    # ── Left: form ────────────────────────────────────────────────────────────
    with col_form:
        st.markdown("#### 📋 PO Header")

        with st.form("create_po_form", clear_on_submit=False):
            supplier_name = st.selectbox("Supplier *", list(supplier_map.keys()), key="po_sup")
            c1, c2 = st.columns(2)
            with c1:
                po_date = st.date_input("PO Date *", value=date.today())
            with c2:
                exp_date = st.date_input(
                    "Expected Delivery *",
                    value=date.today() + timedelta(days=14)
                )
            notes = st.text_area("Notes / Remarks", placeholder="Optional notes…", height=68)

            st.markdown("---")
            st.markdown("#### 🔩 Add Line Item")

            part_key  = st.selectbox("Part *", ["— Select a part —"] + list(parts_map.keys()))
            cq, cc    = st.columns(2)
            with cq:
                item_qty  = st.number_input("Ordered Quantity *", min_value=1, value=10, step=1)
            with cc:
                item_cost = st.number_input("Unit Cost (USD) *", min_value=0.01,
                                             value=25.00, step=0.01, format="%.2f")

            b1, b2 = st.columns(2)
            with b1:
                add_clicked    = st.form_submit_button("➕  Add Item", use_container_width=True)
            with b2:
                create_clicked = st.form_submit_button("✅  Create PO",
                                                        type="primary", use_container_width=True)

        # ── Handle form actions ────────────────────────────────────────────────
        if add_clicked:
            if part_key == "— Select a part —":
                st.error("Please select a part before adding.")
            else:
                p = parts_map[part_key]
                existing = [i["sku"] for i in st.session_state.po_items]
                if p["sku"] in existing:
                    st.warning(f"SKU **{p['sku']}** is already in the list. "
                               "Remove it first to change the quantity.")
                else:
                    st.session_state.po_items.append({
                        "sku":        p["sku"],
                        "description": p["description"],
                        "category":   p["category"],
                        "unit":       p["unit"],
                        "quantity":   item_qty,
                        "unit_cost":  item_cost,
                        "line_total": round(item_qty * item_cost, 2),
                    })
                    st.rerun()

        if create_clicked:
            errs = []
            if not st.session_state.po_items:
                errs.append("Add at least one line item.")
            if exp_date < po_date:
                errs.append("Expected delivery date cannot be before PO date.")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                po_num, err = create_purchase_order(
                    supplier_map[supplier_name], po_date, exp_date,
                    st.session_state.po_items, notes
                )
                if po_num:
                    st.session_state.po_items = []
                    st.success(f"🎉  Purchase Order **{po_num}** created successfully!")
                    st.balloons()
                else:
                    st.error(f"Failed to create PO: {err}")

    # ── Right: items preview ───────────────────────────────────────────────────
    with col_preview:
        st.markdown("#### 🛒 Line Items Preview")

        if st.session_state.po_items:
            df_prev = pd.DataFrame(st.session_state.po_items)

            disp = df_prev[["sku", "description", "category", "unit",
                             "quantity", "unit_cost", "line_total"]].copy()
            disp.columns = ["SKU", "Description", "Category", "Unit",
                             "Qty", "Unit Cost", "Line Total"]
            disp["Unit Cost"]  = disp["Unit Cost"].map("${:,.2f}".format)
            disp["Line Total"] = disp["Line Total"].map("${:,.2f}".format)
            st.dataframe(disp, use_container_width=True, hide_index=True)

            tot_qty = sum(i["quantity"]   for i in st.session_state.po_items)
            tot_val = sum(i["line_total"] for i in st.session_state.po_items)

            st.markdown(info_box([
                ("Lines",          str(len(st.session_state.po_items))),
                ("Total Quantity", f"{tot_qty:,} units"),
                ("Total PO Value", f'<span style="color:#3fb950; font-size:16px; font-weight:700;">'
                                   f"${tot_val:,.2f}</span>"),
            ]), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Individual remove buttons
            st.markdown("**Remove an item:**")
            for idx, it in enumerate(st.session_state.po_items):
                if st.button(f"🗑️  {it['sku']} — {it['description'][:30]}",
                             key=f"del_{idx}", use_container_width=True):
                    st.session_state.po_items.pop(idx)
                    st.rerun()

            if st.button("🗑️  Clear All Items", use_container_width=True):
                st.session_state.po_items = []
                st.rerun()
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-msg">No items added yet</div>
                <div class="empty-sub">Select a part and click ➕ Add Item on the left</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — View All POs
# ═══════════════════════════════════════════════════════════════════════════════
with tab_view:
    fc, _ = st.columns([2, 4])
    with fc:
        status_f = st.selectbox(
            "Filter by Status", ["All", "Open", "Partial", "Closed"], key="po_view_filter"
        )

    pos = get_purchase_orders(status_f)

    if not pos:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📦</div>
            <div class="empty-msg">No purchase orders found</div>
            <div class="empty-sub">Create your first PO using the "Create PO" tab</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Summary tiles
        open_n    = sum(1 for p in pos if p["status"] == "Open")
        partial_n = sum(1 for p in pos if p["status"] == "Partial")
        closed_n  = sum(1 for p in pos if p["status"] == "Closed")
        total_val = sum(p["total_value"] for p in pos)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total POs",    len(pos))
        m2.metric("🟢 Open",      open_n)
        m3.metric("🟡 Partial",   partial_n)
        m4.metric("⚫ Closed",    closed_n)
        m5.metric("💰 Total Value", f"${total_val:,.0f}")

        st.markdown("---")

        df = pd.DataFrame(pos)
        df["Fulfilment %"] = (
            df["total_received"] / df["total_qty"].replace(0, 1) * 100
        ).round(1).astype(str) + " %"

        disp = df[[
            "po_number", "supplier_name", "po_date",
            "expected_delivery_date", "item_count",
            "total_qty", "total_received", "Fulfilment %",
            "total_value", "status"
        ]].copy()
        disp.columns = [
            "PO Number", "Supplier", "PO Date",
            "Expected Delivery", "Lines",
            "Ordered", "Received", "Fulfilment",
            "Value ($)", "Status"
        ]
        disp["Value ($)"] = disp["Value ($)"].map("${:,.2f}".format)

        st.dataframe(disp, use_container_width=True, height=500, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PO Detail
# ═══════════════════════════════════════════════════════════════════════════════
with tab_detail:
    all_pos = get_purchase_orders()
    if not all_pos:
        st.info("No purchase orders available. Create one first.")
    else:
        po_opts = {
            f"{p['po_number']}  ·  {p['supplier_name']}  [{p['status']}]": p["id"]
            for p in all_pos
        }
        sel = st.selectbox("Select Purchase Order", list(po_opts.keys()))

        if sel:
            po = get_po_details(po_opts[sel])
            if po:
                col_l, col_r = st.columns([3, 2], gap="large")

                with col_l:
                    st.markdown("#### 🏢 PO Information")
                    st.markdown(info_box([
                        ("PO Number",       f'<span style="color:#58a6ff; font-weight:700;">'
                                            f'{po["po_number"]}</span>'),
                        ("Supplier",        po["supplier_name"]),
                        ("Contact Person",  po["contact"] or "—"),
                        ("Email",           po["email"] or "—"),
                        ("Phone",           po["phone"] or "—"),
                        ("PO Date",         po["po_date"]),
                        ("Expected Delivery", po["expected_delivery_date"] or "—"),
                        ("Notes",           po["notes"] or "—"),
                    ]), unsafe_allow_html=True)

                with col_r:
                    st.markdown("#### 📊 Summary")
                    tot_ord = sum(i["ordered_quantity"]  for i in po["items"])
                    tot_rcv = sum(i["received_quantity"] for i in po["items"])
                    tot_bal = sum(i["balance_quantity"]  for i in po["items"])
                    tot_val = sum(i["line_total"]         for i in po["items"])

                    st.markdown(info_box([
                        ("Status",   badge(po["status"])),
                        ("Lines",    str(len(po["items"]))),
                        ("Ordered",  f"{tot_ord:,} units"),
                        ("Received", f'<span style="color:#58a6ff;">{tot_rcv:,} units</span>'),
                        ("Balance",  f'<span style="color:#d29922;">{tot_bal:,} units</span>'),
                        ("Value",    f'<span style="color:#3fb950; font-weight:700;">'
                                     f"${tot_val:,.2f}</span>"),
                    ]), unsafe_allow_html=True)

                    if tot_ord > 0:
                        pct = min(tot_rcv / tot_ord, 1.0)
                        st.progress(pct, text=f"Receiving Progress: {pct:.0%}")

                st.markdown("---")
                st.markdown("#### 🔩 Line Items")

                items_df = pd.DataFrame(po["items"])
                if not items_df.empty:
                    disp = items_df[[
                        "sku", "description", "category", "unit",
                        "ordered_quantity", "received_quantity",
                        "balance_quantity", "unit_cost", "line_total"
                    ]].copy()
                    disp.columns = [
                        "SKU", "Description", "Category", "Unit",
                        "Ordered", "Received", "Balance",
                        "Unit Cost", "Line Total"
                    ]
                    disp["Unit Cost"]  = disp["Unit Cost"].map("${:,.2f}".format)
                    disp["Line Total"] = disp["Line Total"].map("${:,.2f}".format)
                    st.dataframe(disp, use_container_width=True, hide_index=True)
