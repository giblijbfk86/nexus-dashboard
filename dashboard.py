import streamlit as st
import psycopg2
import pandas as pd
import datetime
import altair as alt

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Nexus Cloud ☁️",
    page_icon="🦷",
    layout="wide" # 🟢 خليناها Wide عشان تاخد راحتها على شاشات الكمبيوتر وبرضو الموبايل بيلمها
)

# 2. رابط الداتابيز
DB_URL = "postgresql://postgres.thiulhrlurohmfkmxwqw:Mr.junior1966@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)

# --- CSS للتجميل ---
st.markdown("""
<style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    }
    .css-1d391kg {padding-top: 1rem;} /* تظبيط مسافات */
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🖌️ دالة الرسم الاحترافي
# ==========================================
def plot_with_labels(df, x_col, y_col, color, x_title, y_title):
    base = alt.Chart(df).encode(
        x=alt.X(x_col, sort='-y', axis=alt.Axis(title=x_title, labelAngle=-45)),
        y=alt.Y(y_col, axis=alt.Axis(title=y_title)),
        tooltip=[x_col, y_col]
    )
    bars = base.mark_bar(color=color).encode(y=alt.Y(y_col))
    text = base.mark_text(align='center', baseline='bottom', dy=-5, color='white').encode(
        text=alt.Text(y_col, format=',.0f')
    )
    st.altair_chart(bars + text, use_container_width=True)

# ==========================================
# 🎛️ القائمة الجانبية (Sidebar Filters) 🟢 جديد
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=50) # أيقونة سنة
    st.title("Nexus Controls")
    
    st.write("### 📅 Time Filter")
    filter_type = st.radio(
        "Select Period:", 
        ["Daily", "Monthly", "Yearly", "All Time"], 
    )

    query_condition = ""
    query_params = []
    display_label = ""

    if filter_type == "Daily":
        sel_date = st.date_input("Select Date", datetime.date.today())
        query_condition = "WHERE date::DATE = %s"
        query_params = [sel_date]
        display_label = f"Daily: {sel_date}"

    elif filter_type == "Monthly":
        months = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
                  7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
        sel_month = st.selectbox("Month", list(months.keys()), format_func=lambda x: months[x], index=datetime.date.today().month-1)
        sel_year = st.number_input("Year", 2024, 2030, datetime.date.today().year)
        query_condition = "WHERE EXTRACT(MONTH FROM date::DATE) = %s AND EXTRACT(YEAR FROM date::DATE) = %s"
        query_params = [sel_month, sel_year]
        display_label = f"Monthly: {months[sel_month]} {sel_year}"

    elif filter_type == "Yearly":
        sel_year_only = st.number_input("Year", 2024, 2030, datetime.date.today().year)
        query_condition = "WHERE EXTRACT(YEAR FROM date::DATE) = %s"
        query_params = [sel_year_only]
        display_label = f"Yearly: {sel_year_only}"

    else:
        query_condition = ""
        query_params = []
        display_label = "All Time History"

    st.write("---")
    if st.button("🔄 Refresh Data", type="primary"):
        st.rerun()
    st.caption("v5.0 Pro | Cloud Connected")

# ==========================================
# 🏠 المتن الرئيسي (Main Dashboard)
# ==========================================
st.title("🦷 Nexus Cloud Dashboard")
st.markdown(f"**Report for:** `{display_label}`")

try:
    conn = get_connection()
    
    # 💰 1. KPIs
    sql_inc = f"SELECT SUM(amount) FROM income {query_condition}"
    df_inc = pd.read_sql(sql_inc, conn, params=query_params)
    inc_val = df_inc.iloc[0,0] if not df_inc.empty and df_inc.iloc[0,0] else 0
    
    sql_exp = f"SELECT SUM(total_cost) FROM orders {query_condition}"
    df_exp = pd.read_sql(sql_exp, conn, params=query_params)
    exp_val = df_exp.iloc[0,0] if not df_exp.empty and df_exp.iloc[0,0] else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"{inc_val:,.0f}", delta="QAR")
    c2.metric("Total Expenses", f"{exp_val:,.0f}", delta_color="inverse", delta="QAR")
    profit = inc_val - exp_val
    c3.metric("Net Profit", f"{profit:,.0f}", delta_color="normal" if profit >=0 else "inverse")

    st.divider()

    # ⚖️ 2. مقارنة الفروع
    st.subheader("⚖️ Branch Analytics")
    tab1, tab2 = st.tabs(["💰 Income Breakdown", "📉 Consumption Breakdown"])

    with tab1:
        sql_inc_br = f"SELECT branch_name, SUM(amount) as total FROM income {query_condition} GROUP BY branch_name"
        df_inc_br = pd.read_sql(sql_inc_br, conn, params=query_params)
        if not df_inc_br.empty:
            plot_with_labels(df_inc_br, "branch_name", "total", "#2ECC71", "Branch", "Income")
            # 🟢 زرار تحميل الإكسيل
            st.download_button("📥 Download Excel", df_inc_br.to_csv(index=False), "income_report.csv", "text/csv")
        else:
            st.info("No data.")

    with tab2:
        sql_exp_br = f"SELECT requester as branch, SUM(total_cost) as total FROM orders {query_condition} GROUP BY requester"
        df_exp_br = pd.read_sql(sql_exp_br, conn, params=query_params)
        if not df_exp_br.empty:
            plot_with_labels(df_exp_br, "branch", "total", "#FF4B4B", "Branch", "Expense")
             # 🟢 زرار تحميل الإكسيل
            st.download_button("📥 Download Excel", df_exp_br.to_csv(index=False), "expense_report.csv", "text/csv")
        else:
            st.info("No data.")

    # 🏆 3. الأكثر استهلاكاً
    col_l, col_r = st.columns([2,1]) # تقسيم الشاشة: رسم كبير وجدول صغير
    
    with col_l:
        st.subheader("🏆 Top Materials")
        top_sql = f"SELECT item, SUM(qty) as total_qty FROM orders {query_condition} GROUP BY item ORDER BY total_qty DESC LIMIT 7"
        df_top = pd.read_sql(top_sql, conn, params=query_params)
        if not df_top.empty:
            st.bar_chart(df_top, x="item", y="total_qty", color="#8E44AD", horizontal=True)
        else:
            st.info("No data.")

    with col_r:
        st.subheader("🚨 Low Stock")
        stock_sql = "SELECT item_name, quantity FROM branch_stock WHERE quantity < 10 ORDER BY quantity ASC LIMIT 5"
        df_stock = pd.read_sql(stock_sql, conn)
        if not df_stock.empty:
            st.dataframe(df_stock, hide_index=True, use_container_width=True)
        else:
            st.success("Healthy Stock.")

    conn.close()

except Exception as e:
    st.error(f"Error: {e}")
