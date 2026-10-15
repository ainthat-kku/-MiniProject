from __future__ import annotations

import csv
import io
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "budget_tracker.sqlite3"
CATEGORIES = {
    "รายจ่าย": ["อาหาร", "เดินทาง", "การเรียน", "ของใช้", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"],
    "รายรับ": ["เงินจากผู้ปกครอง", "ทุนการศึกษา", "งานพิเศษ", "เงินคืน", "อื่น ๆ"],
}
MONTHS_TH = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

st.set_page_config(page_title="Student Budget Tracker", page_icon="💸", layout="wide")


def add_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Noto Sans Thai', sans-serif; }
        .stApp { background: #f4f8f7; color: #163449; }
        [data-testid="stSidebar"] { background: #102a43; }
        [data-testid="stSidebar"] * { color: #eef8f6; }
        .hero { background: #102a43; padding: 1.25rem 1.5rem; border-radius: 18px; color: white; margin-bottom: 1rem; }
        .hero-kicker { color: #9edfd2; font-size: .85rem; margin: 0 0 .3rem; }
        .hero h1 { color: white; margin: 0; font-size: 2rem; }
        .hero p { color: #c4d9df; margin: .35rem 0 0; }
        div[data-testid="stMetric"] { background: white; padding: 1rem 1.15rem; border: 1px solid #e3eeea; border-radius: 14px; box-shadow: 0 8px 24px #102a4309; }
        div[data-testid="stMetric"] label { color: #708595; }
        div[data-testid="stMetricValue"] { color: #102a43; font-weight: 700; }
        .section-title { font-size: 1.15rem; color: #102a43; font-weight: 700; margin: .5rem 0 .2rem; }
        .section-help { color: #708595; font-size: .85rem; margin: 0 0 .9rem; }
        .stButton>button[kind="primary"], .stFormSubmitButton>button { background: #54d6bd; color: #102a43; border: 0; font-weight: 700; border-radius: 9px; }
        .stButton>button[kind="primary"]:hover, .stFormSubmitButton>button:hover { background: #3cc5a9; color: #102a43; }
        .notice { padding: .8rem 1rem; background: #e4f8f3; border-left: 4px solid #54d6bd; border-radius: 8px; color: #183f5d; }
        .privacy { color: #b7cbd5; font-size: .76rem; line-height: 1.7; }
        hr { border-color: #e3eeea; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('รายรับ','รายจ่าย')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS budgets (
                workspace_id TEXT NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                PRIMARY KEY(workspace_id, month)
            )"""
        )


def workspace_id() -> str:
    if "workspace_id" not in st.session_state:
        st.session_state.workspace_id = uuid.uuid4().hex
    return st.session_state.workspace_id


def load_transactions(workspace: str, month: str) -> pd.DataFrame:
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, kind, amount, category, transaction_date, note
               FROM transactions
               WHERE workspace_id = ? AND substr(transaction_date, 1, 7) = ?
               ORDER BY transaction_date DESC, created_at DESC""",
            (workspace, month),
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows], columns=[
        "id", "kind", "amount", "category", "transaction_date", "note"
    ])


def get_budget(workspace: str, month: str) -> float | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT amount FROM budgets WHERE workspace_id = ? AND month = ?",
            (workspace, month),
        ).fetchone()
    return float(row["amount"]) if row else None


def save_budget(workspace: str, month: str, amount: float) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO budgets(workspace_id, month, amount) VALUES (?, ?, ?)
               ON CONFLICT(workspace_id, month) DO UPDATE SET amount = excluded.amount""",
            (workspace, month, amount),
        )


def save_transaction(workspace: str, kind: str, amount: float, category: str, when: date, note: str) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO transactions
               (id, workspace_id, kind, amount, category, transaction_date, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (uuid.uuid4().hex, workspace, kind, amount, category, when.isoformat(), note.strip(), datetime.now().isoformat(timespec="seconds")),
        )


def delete_transaction(workspace: str, transaction_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ? AND workspace_id = ?",
            (transaction_id, workspace),
        )


def baht(value: float) -> str:
    return f"฿{value:,.2f}" if value % 1 else f"฿{value:,.0f}"


def month_options() -> tuple[list[str], dict[str, str]]:
    today = date.today().replace(day=1)
    values: list[str] = []
    labels: dict[str, str] = {}
    year, month = today.year, today.month
    for _ in range(18):
        key = f"{year:04d}-{month:02d}"
        values.append(key)
        labels[key] = f"{MONTHS_TH[month-1]} {year+543}"
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    return values, labels


def render_budget(expenses: float, budget: float | None) -> None:
    st.markdown('<div class="section-title">งบรายจ่ายต่อเดือน</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-help">ตั้งงบเพื่อช่วยติดตามการใช้เงิน</div>', unsafe_allow_html=True)
    if budget:
        ratio = expenses / budget
        st.progress(min(ratio, 1.0))
        left, right = st.columns(2)
        left.caption(f"ใช้ไป {baht(expenses)}")
        right.caption(f"งบ {baht(budget)}")
        if ratio >= 1:
            st.error(f"รายจ่ายเกินงบ {baht(expenses-budget)} ลองทบทวนรายการในเดือนนี้")
        elif ratio >= .8:
            st.warning(f"ใกล้ถึงงบแล้ว เหลืองบ {baht(budget-expenses)}")
        else:
            st.success(f"เหลืองบ {baht(budget-expenses)}")
    else:
        st.info("ยังไม่ได้ตั้งงบรายจ่ายของเดือนนี้")

    with st.form("budget_form", clear_on_submit=False):
        amount = st.number_input("กำหนดงบรายจ่าย (บาท)", min_value=0.0, step=500.0, value=float(budget or 0), format="%.2f")
        submitted = st.form_submit_button("บันทึกงบ", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("กรุณาใส่งบมากกว่า 0 บาท")
            else:
                save_budget(workspace_id(), st.session_state.selected_month, amount)
                st.success("บันทึกงบรายเดือนแล้ว")
                st.rerun()


def render_transaction_form() -> None:
    st.markdown('<div class="section-title">บันทึกรายการ</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-help">เพิ่มรายรับหรือรายจ่ายของคุณ</div>', unsafe_allow_html=True)
    with st.form("transaction_form", clear_on_submit=True):
        kind = st.radio("ประเภทรายการ", ["รายจ่าย", "รายรับ"], horizontal=True)
        amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=10.0, format="%.2f")
        category = st.selectbox("หมวดหมู่", CATEGORIES[kind])
        when = st.date_input("วันที่", value=date.today())
        note = st.text_input("บันทึกช่วยจำ (ไม่บังคับ)", max_chars=70, placeholder="เช่น ข้าวกลางวัน")
        submitted = st.form_submit_button("＋ เพิ่มรายการ", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("กรุณาใส่จำนวนเงินมากกว่า 0 บาท")
            else:
                save_transaction(workspace_id(), kind, amount, category, when, note)
                st.success("เพิ่มรายการเรียบร้อย")
                st.rerun()


def render_categories(items: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">รายจ่ายตามหมวด</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-help">สรุปการใช้เงินเดือนนี้</div>', unsafe_allow_html=True)
    expenses = items[items["kind"] == "รายจ่าย"] if not items.empty else items
    if expenses.empty:
        st.caption("ยังไม่มีรายจ่ายในเดือนนี้")
        return
    summary = expenses.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    chart = summary.set_index("category")["amount"]
    st.bar_chart(chart, color="#54d6bd", height=min(300, 90 + 35*len(summary)))
    for _, row in summary.iterrows():
        st.caption(f"{row['category']}  ·  {baht(float(row['amount']))}")


def render_transactions(items: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">รายการล่าสุด</div>', unsafe_allow_html=True)
    if items.empty:
        st.info("ยังไม่มีรายการในเดือนนี้ เพิ่มรายการแรกเพื่อเริ่มดูภาพรวมการเงิน")
        return
    kinds = st.multiselect("กรองรายการ", ["รายจ่าย", "รายรับ"], default=["รายจ่าย", "รายรับ"], label_visibility="collapsed")
    shown = items[items["kind"].isin(kinds)]
    if shown.empty:
        st.caption("ไม่พบรายการตามตัวกรอง")
        return
    for _, row in shown.iterrows():
        left, category_col, date_col, amount_col, action_col = st.columns([3.4, 1.5, 1.4, 1.6, .55])
        note = str(row["note"]).strip()
        left.markdown(f"**{'↙' if row['kind']=='รายรับ' else '↗'}  {note or row['category']}**")
        if note:
            left.caption(str(row["category"]))
        category_col.write(str(row["category"]))
        date_col.write(datetime.fromisoformat(str(row["transaction_date"])).strftime("%d/%m/%Y"))
        prefix = "+" if row["kind"] == "รายรับ" else "−"
        amount_col.markdown(f"**{prefix}{baht(float(row['amount']))}**")
        if action_col.button("×", key=f"delete_{row['id']}", help="ลบรายการ"):
            delete_transaction(workspace_id(), str(row["id"]))
            st.rerun()
        st.divider()


def main() -> None:
    add_styles()
    init_db()
    workspace = workspace_id()
    month_values, month_labels = month_options()
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = month_values[0]

    with st.sidebar:
        st.markdown("## 💸 Student Budget<br><span style='color:#9edfd2'>Tracker</span>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**ภาพรวมการเงิน**")
        st.markdown("บันทึกรายรับรายจ่าย แล้วดูยอดคงเหลือและงบประมาณได้ในหน้าเดียว")
        st.markdown("---")
        st.markdown('<div class="privacy">ต้นแบบนี้ไม่มีระบบบัญชีผู้ใช้ ข้อมูลแบ่งตามเซสชันของเบราว์เซอร์ และเก็บใน SQLite บนเครื่องที่รันแอป</div>', unsafe_allow_html=True)

    st.markdown(
        "<div class='hero'><p class='hero-kicker'>จัดการเงินของคุณ</p><h1>Student Budget Tracker</h1><p>รู้ทันรายจ่าย วางแผนเงินได้ทุกวัน</p></div>",
        unsafe_allow_html=True,
    )
    top_left, top_right = st.columns([3, 1])
    top_left.markdown("### ภาพรวมการเงิน")
    selected = top_right.selectbox(
        "เลือกเดือน", month_values, index=month_values.index(st.session_state.selected_month),
        format_func=lambda value: month_labels[value], label_visibility="collapsed",
    )
    st.session_state.selected_month = selected
    items = load_transactions(workspace, selected)
    income = float(items.loc[items["kind"] == "รายรับ", "amount"].sum()) if not items.empty else 0.0
    expenses = float(items.loc[items["kind"] == "รายจ่าย", "amount"].sum()) if not items.empty else 0.0
    st.divider()

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("ยอดคงเหลือ", baht(income-expenses), help="รายรับลบรายจ่ายในเดือนที่เลือก")
    metric_b.metric("รายรับ", baht(income))
    metric_c.metric("รายจ่าย", baht(expenses))

    st.markdown("")
    budget_col, entry_col = st.columns([1, 1.2], gap="large")
    with budget_col:
        render_budget(expenses, get_budget(workspace, selected))
    with entry_col:
        render_transaction_form()

    st.divider()
    category_col, _ = st.columns([1, 1])
    with category_col:
        render_categories(items)

    st.divider()
    render_transactions(items)
    if not items.empty:
        export = items.drop(columns=["id"]).copy()
        export["จำนวนเงิน"] = export["amount"].map(baht)
        export = export.rename(columns={"kind":"ประเภท", "category":"หมวดหมู่", "transaction_date":"วันที่", "note":"บันทึก"})
        csv_data = export.to_csv(index=False, quoting=csv.QUOTE_MINIMAL).encode("utf-8-sig")
        st.download_button("ดาวน์โหลดรายการเดือนนี้เป็น CSV", data=csv_data, file_name=f"budget-{selected}.csv", mime="text/csv")
    st.caption("Student Budget Tracker · ทุกบาทมีความหมาย เริ่มต้นวางแผนได้ตั้งแต่วันนี้")


main()
