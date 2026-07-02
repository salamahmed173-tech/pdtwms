"""
AutoWMS — Inventory View Module
Live stock levels, movement history, reorder alerts, and analytics.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import (initialize_database, seed_sample_data,
                       get_inventory_summary, get_stock_movements, get_parts)
from utils import apply_styles, page_hero, sidebar_brand, badge

st.set_page_config(
    page_title="Inventory — AutoWMS", page_icon="📊", layout="wide"
)
apply_styles()
initialize_database()
seed_sample_data()
sidebar_brand()

page_hero("📊", "Inventory Management",
          "Live stock levels · PO pending · Reserved stock · Movement history · Reorder alerts")

inv = get_inventory_summary()

if not inv:
    st.info("No inventory data. Receive goods via approved POs to see stock here.")
    st.stop()

df_inv = pd.DataFrame(inv)

# ─── Quick KPIs ───────────────────────────────────────────────────────────────
total_skus   = len(df_inv)
in_stock     = (df_inv["current_stock"] > 0).sum()
out_stock    = (df_inv["current_stock"] == 0).sum()
low_stock    = ((df_inv["current_stock"] > 0) &
                (df_inv["current_stock"] <= df_inv["reorder_level"])).sum()
total_units  = int(df_inv["current_stock"].sum())
total_avail  = int(df_inv["available_stock"].sum())
total_res    = int(df_inv["reserved_stock"].sum())
pending_po   = int(df_inv["pending_po_qty"].sum())

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📦 Total SKUs",       total_skus)
k2.metric("🟢 In Stock",         in_stock)
k3.metric("🔴 Out of Stock",     out_stock)
k4.metric("🟡 Low Stock Alert",  low_stock)
k5.metric("📊 Total Units",      f"{total_units:,}")
k6.metric("📥 PO Pending",       f"{pending_po:,}")

st.markdown("---")

tab_stock, tab_movement, tab_alerts, tab_analytics = st.tabs([
    "  📦  Stock Overview  ",
    "  🔄  Stock Movements  ",
    "  🔔  Reorder Alerts  ",
    "  📈  Analytics  ",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Stock Overview
# ═══════════════════════════════════════════════════════════════════════════════
with tab_stock:
    f1, f2, _ = st.columns([2, 2, 3])
    with f1:
        cat_opts = ["All Categories"] + sorted(df_inv["category"].unique().tolist())
        cat_filter = st.selectbox("Category", cat_opts, key="inv_cat")
    with f2:
        status_opts = ["All", "In Stock", "Low Stock", "Out of Stock"]
        status_filter = st.selectbox("Stock Status", status_opts, key="inv_status")

    # Apply filters
    df_view = df_inv.copy()
    if cat_filter != "All Categories":
        df_view = df_view[df_view["category"] == cat_filter]
    if status_filter == "In Stock":
        df_view = df_view[df_view["current_stock"] > df_view["reorder_level"]]
    elif status_filter == "Low Stock":
        df_view = df_view[
            (df_view["current_stock"] > 0) &
            (df_view["current_stock"] <= df_view["reorder_level"])
        ]
    elif status_filter == "Out of Stock":
        df_view = df_view[df_view["current_stock"] == 0]

    def stock_status_label(row):
        if row["current_stock"] == 0:
            return "🔴 Out of Stock"
        elif row["current_stock"] <= row["reorder_level"]:
            return "🟡 Low Stock"
        else:
            return "🟢 In Stock"

    df_view = df_view.copy()
    df_view["Stock Status"] = df_view.apply(stock_status_label, axis=1)
    df_view["Reorder Alert"] = df_view.apply(
        lambda r: "⚠️ Yes" if 0 < r["current_stock"] <= r["reorder_level"] else
                  ("🚨 OOS" if r["current_stock"] == 0 else "—"),
        axis=1
    )

    disp = df_view[[
        "sku", "description", "category", "unit", "reorder_level",
        "current_stock", "reserved_stock", "available_stock",
        "pending_po_qty", "Stock Status", "Reorder Alert", "last_updated"
    ]].copy()
    disp.columns = [
        "SKU", "Description", "Category", "Unit", "Reorder Lvl",
        "On Hand", "Reserved", "Available",
        "PO Pending", "Status", "Reorder Alert", "Last Updated"
    ]

    st.dataframe(disp, use_container_width=True, height=600, hide_index=True)

    # Download button
    csv = disp.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Export to CSV", data=csv,
        file_name="inventory_snapshot.csv", mime="text/csv"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Stock Movements
# ═══════════════════════════════════════════════════════════════════════════════
with tab_movement:
    mf1, mf2, _ = st.columns([2, 2, 3])
    with mf1:
        sku_opts = ["All SKUs"] + sorted(df_inv["sku"].tolist())
        sku_filter = st.selectbox("Filter by SKU", sku_opts, key="mv_sku")
    with mf2:
        mv_type_opts = ["All", "IN (Receiving)", "OUT (Dispatch)"]
        mv_type = st.selectbox("Movement Type", mv_type_opts, key="mv_type")

    movements = get_stock_movements(
        sku=sku_filter if sku_filter != "All SKUs" else None,
        limit=500
    )

    if not movements:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔄</div>
            <div class="empty-msg">No stock movements recorded yet</div>
            <div class="empty-sub">Movements are recorded when receiving is approved or goods are dispatched.</div>
        </div>""", unsafe_allow_html=True)
    else:
        df_mv = pd.DataFrame(movements)

        # Filter by type
        if mv_type == "IN (Receiving)":
            df_mv = df_mv[df_mv["movement_type"] == "IN"]
        elif mv_type == "OUT (Dispatch)":
            df_mv = df_mv[df_mv["movement_type"] == "OUT"]

        # Totals
        in_total  = int(df_mv[df_mv["movement_type"] == "IN"]["quantity"].sum())
        out_total = int(df_mv[df_mv["movement_type"] == "OUT"]["quantity"].sum())

        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("Total Movements", len(df_mv))
        sm2.metric("📥 Total Received", f"+{in_total:,}")
        sm3.metric("📤 Total Dispatched", f"−{out_total:,}")

        st.markdown("---")

        df_mv["Type"] = df_mv["movement_type"].map({"IN": "📥 IN", "OUT": "📤 OUT"})
        df_mv["Qty Display"] = df_mv.apply(
            lambda r: f"+{r['quantity']}" if r["movement_type"] == "IN" else f"−{r['quantity']}",
            axis=1
        )

        disp_mv = df_mv[[
            "movement_date", "sku", "description", "Type",
            "reference_type", "reference_number",
            "Qty Display", "balance", "notes"
        ]].copy()
        disp_mv.columns = [
            "Date/Time", "SKU", "Description", "Type",
            "Ref Type", "Reference #",
            "Quantity", "Balance", "Notes"
        ]
        st.dataframe(disp_mv, use_container_width=True, height=500, hide_index=True)

        # Running balance chart (if single SKU selected)
        if sku_filter != "All SKUs" and not df_mv.empty:
            st.markdown(f"#### 📈 Balance Trend — {sku_filter}")
            chart_df = df_mv.sort_values("movement_date")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=chart_df["movement_date"],
                y=chart_df["balance"],
                mode="lines+markers",
                line=dict(color="#58a6ff", width=2.5),
                marker=dict(color=[
                    "#3fb950" if t == "IN" else "#f85149"
                    for t in chart_df["movement_type"]
                ], size=8),
                name="Balance",
            ))
            fig.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                font_color="#8b949e",
                xaxis=dict(gridcolor="#21262d"),
                yaxis=dict(gridcolor="#21262d", rangemode="tozero"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Reorder Alerts
# ═══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    oos  = df_inv[df_inv["current_stock"] == 0]
    low  = df_inv[(df_inv["current_stock"] > 0) &
                   (df_inv["current_stock"] <= df_inv["reorder_level"])]
    ok   = df_inv[df_inv["current_stock"] > df_inv["reorder_level"]]

    # Out of Stock
    st.markdown("### 🔴 Out of Stock")
    if oos.empty:
        st.markdown('<div class="alert alert-success">✅&nbsp; No parts are out of stock.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert alert-danger">🚨&nbsp; {len(oos)} part(s) out of stock — action required!</div>',
                    unsafe_allow_html=True)
        disp_oos = oos[["sku", "description", "category", "unit",
                         "reorder_level", "pending_po_qty"]].copy()
        disp_oos.columns = ["SKU", "Description", "Category", "Unit",
                             "Reorder Level", "PO Pending"]
        st.dataframe(disp_oos, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Low Stock
    st.markdown("### 🟡 Low Stock — At or Below Reorder Level")
    if low.empty:
        st.markdown('<div class="alert alert-success">✅&nbsp; No parts are below reorder level.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert alert-warn">⚠️&nbsp; {len(low)} part(s) below reorder level.</div>',
                    unsafe_allow_html=True)
        disp_low = low[[
            "sku", "description", "category", "unit",
            "current_stock", "reorder_level", "pending_po_qty"
        ]].copy()
        disp_low.columns = ["SKU", "Description", "Category", "Unit",
                              "On Hand", "Reorder Level", "PO Pending"]
        st.dataframe(disp_low, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown(f"### 🟢 In Stock — {len(ok)} part(s) above reorder level")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Analytics
# ═══════════════════════════════════════════════════════════════════════════════
with tab_analytics:
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        # Stock by category (bar)
        st.markdown("#### On-Hand Stock by Category")
        cat_df = df_inv.groupby("category").agg(
            on_hand=("current_stock", "sum"),
            available=("available_stock", "sum"),
            reserved=("reserved_stock", "sum"),
        ).reset_index()

        fig_cat = px.bar(
            cat_df, x="category", y=["on_hand", "available", "reserved"],
            barmode="group",
            labels={"value": "Units", "category": "Category", "variable": ""},
            color_discrete_map={
                "on_hand":   "#58a6ff",
                "available": "#3fb950",
                "reserved":  "#d29922",
            }
        )
        fig_cat.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#8b949e",
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#21262d"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=320,
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        # Category distribution donut
        st.markdown("#### Category Distribution (Available Units)")
        cat_avail = df_inv.groupby("category")["available_stock"].sum().reset_index()
        fig_pie = px.pie(
            cat_avail, values="available_stock", names="category",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig_pie.update_layout(
            paper_bgcolor="#0d1117",
            font_color="#8b949e",
            legend=dict(bgcolor="#161b22", bordercolor="#21262d"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        # Top 15 parts by on-hand stock
        st.markdown("#### Top 15 Parts by On-Hand Stock")
        top15 = df_inv.nlargest(15, "current_stock")[
            ["sku", "description", "current_stock", "available_stock", "reserved_stock", "category"]
        ]
        fig_top = px.bar(
            top15, x="current_stock", y="sku",
            orientation="h",
            color="category",
            hover_data={"description": True, "available_stock": True},
            labels={"current_stock": "On Hand", "sku": "SKU"},
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig_top.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#8b949e",
            yaxis=dict(categoryorder="total ascending", gridcolor="#21262d"),
            xaxis=dict(gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#21262d"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=420,
        )
        st.plotly_chart(fig_top, use_container_width=True)

        # Stock health gauge summary
        st.markdown("#### Stock Health Summary")
        total = len(df_inv)
        pct_ok  = round(len(ok)  / total * 100, 1)
        pct_low = round(len(low) / total * 100, 1)
        pct_oos = round(len(oos) / total * 100, 1)

        fig_health = go.Figure(go.Bar(
            x=[pct_ok, pct_low, pct_oos],
            y=["🟢 In Stock", "🟡 Low Stock", "🔴 Out of Stock"],
            orientation="h",
            marker_color=["#3fb950", "#d29922", "#f85149"],
            text=[f"{pct_ok}%", f"{pct_low}%", f"{pct_oos}%"],
            textposition="auto",
        ))
        fig_health.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#8b949e",
            xaxis=dict(gridcolor="#21262d", title="% of SKUs"),
            yaxis=dict(gridcolor="#21262d"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=220,
        )
        st.plotly_chart(fig_health, use_container_width=True)

st.markdown("""
<div class="footer">
    AutoWMS v1.0 &nbsp;·&nbsp; Inventory data is updated in real-time upon receiving approval and dispatch confirmation
</div>
""", unsafe_allow_html=True)
