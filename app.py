"""
AutoWMS — Home / Dashboard
Automotive Spare Parts Warehouse Management System
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import (initialize_database, seed_sample_data,
                       get_dashboard_stats, get_inventory_summary,
                       get_stock_movements)
from utils import apply_styles, page_hero, sidebar_brand

st.set_page_config(
    page_title="AutoWMS — Warehouse Management",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()
initialize_database()
seed_sample_data()

sidebar_brand()

page_hero(
    "🏭",
    "AutoWMS Dashboard",
    "Automotive Spare Parts · Warehouse Management System · PO-controlled receiving · Real-time inventory"
)

# ─── KPI Row 1 ───────────────────────────────────────────────────────────────
stats = get_dashboard_stats()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📦 Open POs",          stats["open_pos"],
          delta=f"+{stats['partial_pos']} Partial", delta_color="normal")
c2.metric("📥 Pending Receiving", stats["pending_receiving"],
          delta="Awaiting Approval", delta_color="off")
c3.metric("📤 Active Dispatches", stats["active_dispatches"],
          delta="In Progress", delta_color="off")
c4.metric("🗃️ Total SKUs",        stats["total_skus"],
          delta=f"{stats['total_units']:,} Units in Stock", delta_color="normal")
c5.metric("✅ Dispatched",         stats["total_dispatched"],
          delta="All Time", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Alert Row ───────────────────────────────────────────────────────────────
a1, a2, a3, a4 = st.columns(4)

def _colored_metric(col, label, value, sub):
    with col:
        st.metric(label, value, delta=sub, delta_color="off")

_colored_metric(a1,
    f"{'🔴' if stats['out_of_stock']   > 0 else '🟢'} Out of Stock",
    stats["out_of_stock"], "SKUs")
_colored_metric(a2,
    f"{'🟡' if stats['low_stock']       > 0 else '🟢'} Low Stock Alert",
    stats["low_stock"], "Below Reorder Level")
_colored_metric(a3,
    f"{'🟠' if stats['damage_alerts']   > 0 else '🟢'} Damage Alerts",
    stats["damage_alerts"], "Pending Review")
_colored_metric(a4,
    f"{'🟠' if stats['shortage_alerts'] > 0 else '🟢'} Shortage Alerts",
    stats["shortage_alerts"], "Pending Review")

st.markdown("---")

# ─── Main content: Inventory table + Recent movements + Chart ────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### 📦 Live Inventory Snapshot")

    inv = get_inventory_summary()
    if inv:
        df = pd.DataFrame(inv)

        def stock_status(row):
            if row["current_stock"] == 0:
                return "🔴 Out of Stock"
            elif row["current_stock"] <= row["reorder_level"]:
                return "🟡 Low Stock"
            else:
                return "🟢 In Stock"

        df["Status"] = df.apply(stock_status, axis=1)
        display = df[["sku", "description", "category", "unit",
                       "current_stock", "available_stock",
                       "reserved_stock", "pending_po_qty", "Status"]].copy()
        display.columns = ["SKU", "Description", "Category", "Unit",
                            "On Hand", "Available", "Reserved", "PO Pending", "Status"]
        st.dataframe(display, use_container_width=True, height=400, hide_index=True)

        # Mini bar chart — top 10 by available stock
        st.markdown("#### Top 10 Available Parts")
        top10 = df.nlargest(10, "available_stock")[["sku", "available_stock", "category"]]
        fig = px.bar(
            top10, x="available_stock", y="sku", orientation="h",
            color="category",
            labels={"available_stock": "Available Units", "sku": "SKU"},
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#8b949e",
            yaxis=dict(categoryorder="total ascending"),
            legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1),
            margin=dict(l=0, r=0, t=0, b=0),
            height=260,
        )
        fig.update_xaxes(gridcolor="#21262d")
        fig.update_yaxes(gridcolor="#21262d")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No inventory data yet. Create a PO, receive goods, and stock will appear here.")

with col_right:
    st.markdown("### 🔄 Recent Stock Movements")
    movements = get_stock_movements(limit=20)

    if movements:
        for m in movements:
            is_in   = m["movement_type"] == "IN"
            qty_cls = "mv-qty-in" if is_in else "mv-qty-out"
            sign    = "+" if is_in else "−"
            icon    = "📥" if is_in else "📤"
            st.markdown(f"""
            <div class="mv-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div class="mv-ref">{m['reference_number']} &nbsp;·&nbsp; {m['movement_date'][:16]}</div>
                        <div class="mv-desc">{icon} {m['description'][:38]}</div>
                        <div class="mv-ref">{m['sku']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="{qty_cls}">{sign}{m['quantity']}</div>
                        <div class="mv-bal">Bal: {m['balance']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-msg">No movements yet</div>
            <div class="empty-sub">Create a PO → Receive goods → Dispatch to customers</div>
        </div>
        """, unsafe_allow_html=True)

# ─── System rules banner ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex; gap:12px; flex-wrap:wrap; margin:4px 0 16px;">
    <div class="alert alert-danger" style="flex:1; min-width:200px;">
        🚫&nbsp; <strong>Manual Receiving Blocked</strong> — All inbound stock requires an approved Purchase Order
    </div>
    <div class="alert alert-info" style="flex:1; min-width:200px;">
        ℹ️&nbsp; <strong>No Negative Stock</strong> — Dispatch is blocked when available stock is insufficient
    </div>
    <div class="alert alert-warn" style="flex:1; min-width:200px;">
        ⚠️&nbsp; <strong>Inventory locked on Dispatch Create</strong> — Stock is reserved immediately upon order creation
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    AutoWMS v1.0 &nbsp;·&nbsp; Automotive Spare Parts Warehouse Management System &nbsp;·&nbsp;
    SQLite · Streamlit · Python
</div>
""", unsafe_allow_html=True)
