# AutoWMS — Automotive Spare Parts Warehouse Management System

A professional warehouse management system built with **Python**, **Streamlit**, and **SQLite**.

## 🏭 Features

### 📦 Purchase Order Module
- Create POs with multiple line items (SKU, qty, unit cost)
- Supplier management with 5 pre-loaded suppliers
- PO status tracking: Open → Partial → Closed
- Expected delivery date tracking

### 📥 Inbound Receiving (PO-Based Only)
- **Manual receiving is BLOCKED** — all stock must come via an approved PO
- Auto-populated supplier, SKU, and ordered qty from selected PO
- Damage quantity, short quantity, and QC status tracking
- Put-away rack/bin location assignment
- Two-step approval workflow: Submit → Approve/Reject
- Inventory updates ONLY after receiving approval

### 📤 Outbound Dispatch
- Create dispatch orders with real-time availability check
- Stock reserved immediately on order creation
- Three-step workflow: Picking → Packing → Dispatch
- Inventory deducted only on final dispatch confirmation

### 📊 Inventory View
- Live stock overview: On Hand, Available, Reserved, PO Pending
- Color-coded stock status (In Stock / Low Stock / Out of Stock)
- Stock movement history with running balance
- Reorder alerts dashboard
- Analytics with Plotly charts (by category, top parts, health gauge)

## 🚀 Business Rules Enforced
- ✅ No receiving without an approved Purchase Order
- ✅ No negative stock — dispatch blocked if insufficient available qty
- ✅ Damaged units excluded from inventory on approval
- ✅ Stock reserved on dispatch creation, deducted on dispatch confirmation
- ✅ PO status auto-updates (Open → Partial → Closed)
- ✅ Shortage and damage alerts on pending approvals

## 🛠️ Tech Stack
- **Frontend**: Streamlit 1.58
- **Database**: SQLite (local) / compatible with cloud DBs
- **Charts**: Plotly
- **Language**: Python 3.x

## 📦 Sample Data
25 automotive spare parts pre-loaded across 9 categories:
Engine, Brakes, Suspension, Electrical, Cooling, Transmission, Fuel System, Ignition, Steering, Exhaust

5 suppliers pre-loaded: AutoParts Pro Ltd, OEM Supply Co., Genuine Parts Hub, TechAuto Distributors, Premier Auto Parts

## ⚙️ Local Setup

```bash
# Clone the repo
git clone https://github.com/salamahmed173-tech/pdtwms.git
cd pdtwms

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m streamlit run app.py
```

App opens at **http://localhost:8501**

## ☁️ Deploy on Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app** → select this repo
5. Set **Main file path**: `app.py`
6. Click **Deploy** — live in ~2 minutes!

---
*Built with ❤️ for automotive spare parts warehouse operations*
