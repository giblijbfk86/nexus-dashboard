import streamlit as st
import psycopg2
import pandas as pd
import datetime

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Nexus Cloud ☁️",
    page_icon="🦷",
    layout="centered"
)

# 2. رابط الداتابيز
DB_URL = "postgresql://postgres.thiulhrlurohmfkmxwqw:Mr.junior1966@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)

# --- CSS للتجميل ---
st.markdown("""
<style>
    .stMetric {
        background-color: #2b2b2b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #444;
    }
    div[data-testid="stDateInput"] {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- العنوان ---
st.title("🦷 Nexus Cloud Dashboard")

# 🟢 1. فلتر التاريخ (Date Filter)
col_date, col_btn = st.columns([2, 1])
with col_date:
    selected_date = st.date_input("📅 Select Date to View", datetime.date.today())
with col_btn:
    st.write("") # spacing
    st.write("") # spacing
    if st.button("🔄 Refresh", type="primary", use_container_width=True):
        st.rerun()

try:
    conn = get_connection()
    
    # ==========================================
    # 💰 2. الماليات (حسب التاريخ المختار)
    # ==========================================
    st.header(f"💵 Financials: {selected_date}")
    
    # الدخل (Income)
    sql_inc = "SELECT SUM(amount) FROM income WHERE date::DATE = %s"
    df_inc = pd.read_sql(sql_inc, conn, params=(selected_date,))
    inc_val = df_inc.iloc[0,0] if not df_inc.empty and df_inc.iloc[0,0] else 0
    
    # المصروفات (Orders)
    sql_exp = "SELECT SUM(total_cost) FROM orders WHERE date::DATE = %s"
    df_exp = pd.read_sql(sql_exp, conn, params=(selected_date,))
    exp_val = df_exp.iloc[0,0] if not df_exp.empty and df_exp.iloc[0,0] else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Income", f"{inc_val:,.0f}", delta="selected day")
    c2.metric("Expense", f"{exp_val:,.0f}", delta_color="inverse")
    c3.metric("Profit", f"{inc_val - exp_val:,.0f}")

    st.markdown("---")

    # ==========================================
    # 🏆 3. الأكثر استهلاكاً (All Time)
    # ==========================================
    # خليناها لكل الوقت عشان تضمن إن فيه داتا تظهر
    st.subheader("🏆 Top Consumed Materials (All Time)")
    
    top_sql = """
        SELECT item, SUM(qty) as total_qty 
        FROM orders 
        GROUP BY item 
        ORDER BY total_qty DESC 
        LIMIT 7
    """
    df_top = pd.read_sql(top_sql, conn)
    
    if not df_top.empty:
        # رسم بياني أحمر
        st.bar_chart(df_top, x="item", y="total_qty", color="#FF4B4B")
    else:
        st.info("No materials consumed yet.")

    # ==========================================
    # 📉 4. تحليل الدخل (آخر 7 أيام)
    # ==========================================
    st.subheader("📊 Income Trend (Last 7 Days)")
    chart_sql = """
        SELECT date, SUM(amount) as total 
        FROM income 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    """
    df_chart = pd.read_sql(chart_sql, conn)
    if not df_chart.empty:
        df_chart = df_chart.sort_values("date")
        st.area_chart(df_chart, x="date", y="total", color="#2ECC71")

    # ==========================================
    # 📦 5. النواقص (Alerts)
    # ==========================================
    st.subheader("🚨 Stock Alerts (< 10)")
    stock_sql = """
        SELECT item_name, quantity, branch_name 
        FROM branch_stock 
        WHERE quantity < 10 
        ORDER BY quantity ASC 
        LIMIT 10
    """
    df_stock = pd.read_sql(stock_sql, conn)
    if not df_stock.empty:
        st.dataframe(
            df_stock,
            column_config={
                "item_name": "Item",
                "quantity": st.column_config.NumberColumn("Qty", format="%d 📦"),
                "branch_name": "Branch"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("✅ Stock is healthy.")

    conn.close()

except Exception as e:
    st.error(f"Error: {e}")