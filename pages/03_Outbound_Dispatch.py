"""
AutoWMS — Outbound Dispatch Module
Create dispatch orders, confirm picking / packing / dispatch workflow.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date

from database import (initialize_database, seed_sample_data,
                       get_inventory_summary, get_parts,
                       create_dispatch_order, get_dispatch_orders, get_dispatch_details,
                       update_dispatch_step)
from utils import apply_styles, page_hero, sidebar_brand, badge, alert, workflow_html

st.set_page_config(
    page_title="Outbound Dispatch — AutoWMS", page_icon="📤", layout="wide"
)
apply_styles()
initialize_database()
seed_sample_data()
sidebar_brand()

# ─── Session state ────────────────────────────────────────────────────────────
if "dsp_items" not in st.session_state:
    st.session_state.dsp_items = []

page_hero("📤", "Outbound Dispatch",
          "Create dispatch orders · Confirm picking → packing → dispatch · Real-time stock deduction")

tab_create, tab_active, tab_history = st.tabs([
    "  ➕  Create Dispatch Order  ",
    "  🔄  Active Orders  ",
    "  📋  Dispatch History  ",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Create Dispatch Order
# ═══════════════════════════════════════════════════════════════════════════════
with tab_create:
    inv = get_inventory_summary()

    # Only parts with available stock
    in_stock = [i for i in inv if (i["current_stock"] - i["reserved_stock"]) > 0]

    if not in_stock:
        st.markdown(alert(
            "No parts currently in stock. Receive goods via an approved PO first.", "warn"
        ), unsafe_allow_html=True)
    else:
        col_form, col_prev = st.columns([1, 1], gap="large")

        # ── Left: form ─────────────────────────────────────────────────────────
        with col_form:
            st.markdown("#### 🚚 Dispatch Order Header")

            with st.form("create_dsp_form", clear_on_submit=False):
                customer = st.text_input(
                    "Customer / Recipient *",
                    placeholder="e.g. Apex Auto Repairs Ltd."
                )
                dsp_date = st.date_input("Dispatch Date *", value=date.today())
                notes    = st.text_area("Notes", placeholder="Delivery instructions…", height=68)

                st.markdown("---")
                st.markdown("#### 📦 Add Line Item")

                avail_opts = {
                    f"[{i['sku']}]  {i['description']}  "
                    f"(Avail: {i['current_stock'] - i['reserved_stock']} {i['unit']})": i
                    for i in in_stock
                }
                part_key = st.selectbox(
                    "Part *",
                    ["— Select —"] + list(avail_opts.keys())
                )

                # Show available qty hint
                if part_key != "— Select —":
                    chosen = avail_opts[part_key]
                    avail_now = chosen["current_stock"] - chosen["reserved_stock"]
                    st.markdown(
                        alert(f"Available quantity: **{avail_now} {chosen['unit']}**", "info"),
                        unsafe_allow_html=True
                    )
                    max_qty = avail_now
                else:
                    max_qty = 9999

                dsp_qty = st.number_input(
                    "Quantity *", min_value=1,
                    max_value=max_qty if max_qty > 0 else 1,
                    value=min(1, max_qty), step=1
                )

                b1, b2 = st.columns(2)
                with b1:
                    add_clicked    = st.form_submit_button("➕  Add Item", use_container_width=True)
                with b2:
                    create_clicked = st.form_submit_button(
                        "📤  Create Dispatch Order", type="primary", use_container_width=True
                    )

            # ── Handle actions ─────────────────────────────────────────────────
            if add_clicked:
                if part_key == "— Select —":
                    st.error("Please select a part.")
                else:
                    chosen = avail_opts[part_key]
                    avail_now = chosen["current_stock"] - chosen["reserved_stock"]
                    existing_skus = [i["sku"] for i in st.session_state.dsp_items]

                    if chosen["sku"] in existing_skus:
                        st.warning(f"SKU **{chosen['sku']}** already added.")
                    elif dsp_qty > avail_now:
                        st.error(
                            f"Requested {dsp_qty} but only {avail_now} available for {chosen['sku']}."
                        )
                    else:
                        st.session_state.dsp_items.append({
                            "sku":         chosen["sku"],
                            "description": chosen["description"],
                            "unit":        chosen["unit"],
                            "quantity":    dsp_qty,
                            "available":   avail_now,
                        })
                        st.rerun()

            if create_clicked:
                errs = []
                if not customer.strip():
                    errs.append("Customer name is required.")
                if not st.session_state.dsp_items:
                    errs.append("Add at least one line item.")
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    dsp_num, err = create_dispatch_order(
                        customer.strip(), dsp_date,
                        st.session_state.dsp_items, notes
                    )
                    if dsp_num:
                        st.session_state.dsp_items = []
                        st.success(
                            f"🎉  Dispatch Order **{dsp_num}** created! "
                            "Stock has been reserved. Proceed to confirm picking."
                        )
                        st.balloons()
                    else:
                        st.error(f"Failed: {err}")

        # ── Right: preview ─────────────────────────────────────────────────────
        with col_prev:
            st.markdown("#### 🛒 Order Preview")

            if st.session_state.dsp_items:
                df_prev = pd.DataFrame(st.session_state.dsp_items)
                disp = df_prev[["sku", "description", "unit", "quantity", "available"]].copy()
                disp.columns = ["SKU", "Description", "Unit", "Dispatch Qty", "Available"]
                st.dataframe(disp, use_container_width=True, hide_index=True)

                st.markdown(f"""
                <div class="info-box" style="margin-top:12px;">
                    <div class="info-row">
                        <span class="info-key">Total Lines</span>
                        <span class="info-val">{len(st.session_state.dsp_items)}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-key">Total Units</span>
                        <span class="info-val">{sum(i['quantity'] for i in st.session_state.dsp_items):,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Remove buttons
                for idx, it in enumerate(st.session_state.dsp_items):
                    if st.button(f"🗑️  {it['sku']} — {it['description'][:30]}",
                                  key=f"dsp_del_{idx}", use_container_width=True):
                        st.session_state.dsp_items.pop(idx)
                        st.rerun()

                if st.button("🗑️  Clear All Items", use_container_width=True):
                    st.session_state.dsp_items = []
                    st.rerun()
            else:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-icon">🚚</div>
                    <div class="empty-msg">No items added yet</div>
                    <div class="empty-sub">Select a part with available stock and click ➕ Add Item</div>
                </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Active Orders
# ═══════════════════════════════════════════════════════════════════════════════
with tab_active:
    active_orders = [o for o in get_dispatch_orders()
                     if o["status"] not in ("Dispatched",)]

    if not active_orders:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-msg">No Active Dispatch Orders</div>
            <div class="empty-sub">Create a dispatch order from the first tab.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert alert-info">
            ℹ️&nbsp; <strong>{len(active_orders)} active order(s)</strong>
            in progress. Confirm each step to advance.
        </div>
        """, unsafe_allow_html=True)

        for order in active_orders:
            status = order["status"]

            # Workflow state
            step_states = {
                "Pending":  [("Create", "done"),  ("Pick",   "active"), ("Pack", "todo"),  ("Dispatch", "todo")],
                "Picking":  [("Create", "done"),  ("Pick",   "done"),   ("Pack", "active"),("Dispatch", "todo")],
                "Packing":  [("Create", "done"),  ("Pick",   "done"),   ("Pack", "done"),  ("Dispatch", "active")],
            }
            steps = step_states.get(status, [("Create","done"),("Pick","done"),("Pack","done"),("Dispatch","done")])

            with st.expander(
                f"🚚  {order['dispatch_number']}  ·  {order['customer']}  "
                f"·  {order['item_count']} lines  ·  [{status}]",
                expanded=True
            ):
                # Workflow track
                st.markdown(workflow_html(steps), unsafe_allow_html=True)

                # Detail grid
                d = get_dispatch_details(order["id"])

                col_info, col_items, col_actions = st.columns([2, 3, 2], gap="medium")

                with col_info:
                    st.markdown(f"""
                    <div class="info-box">
                        <div class="info-row"><span class="info-key">Dispatch #</span>
                            <span class="info-val">{d['dispatch_number']}</span></div>
                        <div class="info-row"><span class="info-key">Customer</span>
                            <span class="info-val">{d['customer']}</span></div>
                        <div class="info-row"><span class="info-key">Date</span>
                            <span class="info-val">{d['dispatch_date']}</span></div>
                        <div class="info-row"><span class="info-key">Status</span>
                            <span class="info-val">{badge(status)}</span></div>
                        <div class="info-row"><span class="info-key">Picking</span>
                            <span class="info-val">{'✅' if d['picking_confirmed'] else '⏳'}</span></div>
                        <div class="info-row"><span class="info-key">Packing</span>
                            <span class="info-val">{'✅' if d['packing_confirmed'] else '⏳'}</span></div>
                        <div class="info-row"><span class="info-key">Dispatch</span>
                            <span class="info-val">{'✅' if d['dispatch_confirmed'] else '⏳'}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_items:
                    items_df = pd.DataFrame(d["items"])
                    if not items_df.empty:
                        disp_it = items_df[["sku", "description", "unit", "ordered_quantity"]].copy()
                        disp_it.columns = ["SKU", "Description", "Unit", "Qty"]
                        st.dataframe(disp_it, use_container_width=True, hide_index=True, height=200)

                with col_actions:
                    st.markdown("**Confirm Next Step:**")

                    if status == "Pending":
                        if st.button("📋  Confirm Picking",
                                      key=f"pick_{order['id']}", type="primary",
                                      use_container_width=True):
                            ok, msg = update_dispatch_step(order["id"], "picking")
                            if ok:
                                st.success("Picking confirmed!")
                                st.rerun()
                            else:
                                st.error(msg)

                    elif status == "Picking":
                        st.markdown(alert("✅ Picking done. Confirm packing.", "success"),
                                    unsafe_allow_html=True)
                        if st.button("📦  Confirm Packing",
                                      key=f"pack_{order['id']}", type="primary",
                                      use_container_width=True):
                            ok, msg = update_dispatch_step(order["id"], "packing")
                            if ok:
                                st.success("Packing confirmed!")
                                st.rerun()
                            else:
                                st.error(msg)

                    elif status == "Packing":
                        st.markdown(alert("✅ Packing done. Confirm dispatch.", "success"),
                                    unsafe_allow_html=True)
                        st.markdown(
                            alert("⚠️ This will deduct stock from inventory!", "warn"),
                            unsafe_allow_html=True
                        )
                        if st.button("🚚  Confirm Dispatch",
                                      key=f"dsp_{order['id']}", type="primary",
                                      use_container_width=True):
                            ok, msg = update_dispatch_step(order["id"], "dispatch")
                            if ok:
                                st.success("🎉 Order dispatched! Inventory updated.")
                                st.rerun()
                            else:
                                st.error(msg)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Dispatch History
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    hf1, _ = st.columns([2, 4])
    with hf1:
        hist_f = st.selectbox(
            "Filter by Status",
            ["All", "Dispatched", "Packing", "Picking", "Pending"],
            key="dsp_hist_filter"
        )

    orders = get_dispatch_orders(status=hist_f if hist_f != "All" else None)

    if not orders:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <div class="empty-msg">No dispatch orders found</div>
            <div class="empty-sub">Dispatch orders appear here as they are created.</div>
        </div>""", unsafe_allow_html=True)
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Orders",   len(orders))
        m2.metric("✅ Dispatched",  sum(1 for o in orders if o["status"] == "Dispatched"))
        m3.metric("🔄 In Progress", sum(1 for o in orders if o["status"] not in ("Dispatched", "Pending")))
        m4.metric("⏳ Pending",     sum(1 for o in orders if o["status"] == "Pending"))

        st.markdown("---")

        df_ord = pd.DataFrame(orders)
        disp = df_ord[[
            "dispatch_number", "customer", "dispatch_date",
            "item_count", "total_qty",
            "picking_confirmed", "packing_confirmed", "dispatch_confirmed",
            "status", "created_at"
        ]].copy()
        disp.columns = [
            "Dispatch #", "Customer", "Date",
            "Lines", "Total Qty",
            "Picking ✓", "Packing ✓", "Dispatched ✓",
            "Status", "Created"
        ]
        disp["Picking ✓"]    = disp["Picking ✓"].map({0: "—", 1: "✅"})
        disp["Packing ✓"]    = disp["Packing ✓"].map({0: "—", 1: "✅"})
        disp["Dispatched ✓"] = disp["Dispatched ✓"].map({0: "—", 1: "✅"})

        st.dataframe(disp, use_container_width=True, height=500, hide_index=True)
