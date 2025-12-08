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
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# --- العنوان ---
st.title("🦷 Nexus Dashboard")

# ==========================================
# 🎛️ الفلتر الذكي (Smart Filter)
# ==========================================
st.write("### 🔍 View Mode")
# أزرار اختيار نوع العرض
filter_type = st.radio(
    "Select Period:", 
    ["Daily 📅", "Monthly 🗓️", "Yearly 📆", "All Time ♾️"], 
    horizontal=True,
    label_visibility="collapsed"
)

# متغيرات هنستخدمها في الـ SQL
query_condition = ""
query_params = []
display_label = ""

col_opt1, col_opt2 = st.columns(2)

# منطق الفلتر
if filter_type == "Daily 📅":
    with col_opt1:
        sel_date = st.date_input("Select Date", datetime.date.today())
    query_condition = "WHERE date::DATE = %s"
    query_params = [sel_date]
    display_label = f"Daily Report: {sel_date}"

elif filter_type == "Monthly 🗓️":
    with col_opt1:
        # قائمة الشهور
        months = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
                  7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
        sel_month = st.selectbox("Month", list(months.keys()), format_func=lambda x: months[x], index=datetime.date.today().month-1)
    with col_opt2:
        sel_year = st.number_input("Year", min_value=2024, max_value=2030, value=datetime.date.today().year)
    
    # فلتر بالسنة والشهر
    query_condition = "WHERE EXTRACT(MONTH FROM date::DATE) = %s AND EXTRACT(YEAR FROM date::DATE) = %s"
    query_params = [sel_month, sel_year]
    display_label = f"Monthly Report: {months[sel_month]} {sel_year}"

elif filter_type == "Yearly 📆":
    with col_opt1:
        sel_year_only = st.number_input("Select Year", min_value=2024, max_value=2030, value=datetime.date.today().year)
    query_condition = "WHERE EXTRACT(YEAR FROM date::DATE) = %s"
    query_params = [sel_year_only]
    display_label = f"Yearly Report: {sel_year_only}"

else: # All Time
    query_condition = "" # مفيش شرط = هات كله
    query_params = []
    display_label = "All Time Report (Grand Total)"

# زرار التحديث
if st.button("🔄 Update View", type="primary", use_container_width=True):
    st.rerun()

try:
    conn = get_connection()
    
    # ==========================================
    # 💰 1. الماليات (ديناميك حسب الفلتر)
    # ==========================================
    st.markdown(f"#### 💵 {display_label}")
    
    # حساب الدخل
    sql_inc = f"SELECT SUM(amount) FROM income {query_condition}"
    df_inc = pd.read_sql(sql_inc, conn, params=query_params)
    inc_val = df_inc.iloc[0,0] if not df_inc.empty and df_inc.iloc[0,0] else 0
    
    # حساب المصروفات
    sql_exp = f"SELECT SUM(total_cost) FROM orders {query_condition}"
    df_exp = pd.read_sql(sql_exp, conn, params=query_params)
    exp_val = df_exp.iloc[0,0] if not df_exp.empty and df_exp.iloc[0,0] else 0
    
    # عرض الأرقام
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"{inc_val:,.0f}", delta="QAR")
    c2.metric("Total Expenses", f"{exp_val:,.0f}", delta_color="inverse", delta="QAR")
    
    profit = inc_val - exp_val
    c3.metric("Net Profit", f"{profit:,.0f}", delta_color="normal" if profit >=0 else "inverse")

    st.markdown("---")

    # ==========================================
    # 🏆 2. الأكثر استهلاكاً (ديناميك برضو!)
    # ==========================================
    st.subheader("🏆 Top Consumed Materials")
    st.caption(f"Based on: {display_label}")
    
    # بنستخدم نفس الفلتر عشان نعرف استهلكنا إيه في الشهر ده بالذات
    top_sql = f"""
        SELECT item, SUM(qty) as total_qty 
        FROM orders 
        {query_condition}
        GROUP BY item 
        ORDER BY total_qty DESC 
        LIMIT 7
    """
    df_top = pd.read_sql(top_sql, conn, params=query_params)
    
    if not df_top.empty:
        st.bar_chart(df_top, x="item", y="total_qty", color="#FF4B4B")
    else:
        st.info("No consumption data for this period.")

    # ==========================================
    # 📦 3. النواقص (دايماً شغالة)
    # ==========================================
    st.markdown("---")
    st.subheader("🚨 Current Low Stock Alerts")
    stock_sql = """
        SELECT item_name, quantity, branch_name 
        FROM branch_stock 
        WHERE quantity < 10 
        ORDER BY quantity ASC 
        LIMIT 5
    """
    df_stock = pd.read_sql(stock_sql, conn)
    if not df_stock.empty:
        st.dataframe(
            df_stock, 
            column_config={
                "item_name": "Item",
                "quantity": st.column_config.NumberColumn("Qty", format="%d 📦")
            }, 
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.success("✅ Inventory healthy.")

    conn.close()

except Exception as e:
    st.error(f"Error: {e}")
