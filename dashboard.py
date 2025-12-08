import streamlit as st
import psycopg2
import pandas as pd
import datetime
import altair as alt  # 🟢 دي المكتبة المسؤولة عن الرسم الاحترافي

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
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

st.title("🦷 Nexus Dashboard")

# ==========================================
# 🖌️ دالة الرسم الاحترافي (عواميد + أرقام)
# ==========================================
def plot_with_labels(df, x_col, y_col, color, x_title, y_title):
    # الأساس
    base = alt.Chart(df).encode(
        x=alt.X(x_col, sort='-y', axis=alt.Axis(title=x_title, labelAngle=-45)),
        y=alt.Y(y_col, axis=alt.Axis(title=y_title)),
        tooltip=[x_col, y_col]
    )

    # 1. طبقة العواميد
    bars = base.mark_bar(color=color).encode(
        y=alt.Y(y_col)
    )

    # 2. طبقة الأرقام (فوق العواميد)
    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,  # ترفع الرقم فوق العمود سنة
        color='white',
        fontSize=12
    ).encode(
        text=alt.Text(y_col, format=',.0f') # تقريب لأقرب رقم صحيح
    )

    # دمج الاثنين وعرضهم
    st.altair_chart(bars + text, use_container_width=True)


# ==========================================
# 🎛️ الفلتر
# ==========================================
st.write("### 🔍 Filter Period")
filter_type = st.radio(
    "Select Period:", 
    ["Daily 📅", "Monthly 🗓️", "Yearly 📆", "All Time ♾️"], 
    horizontal=True, 
    label_visibility="collapsed"
)

query_condition = ""
query_params = []
display_label = ""

col1, col2 = st.columns(2)

if filter_type == "Daily 📅":
    with col1:
        sel_date = st.date_input("Select Date", datetime.date.today())
    query_condition = "WHERE date::DATE = %s"
    query_params = [sel_date]
    display_label = f"📅 {sel_date}"

elif filter_type == "Monthly 🗓️":
    with col1:
        months = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
                  7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
        sel_month = st.selectbox("Month", list(months.keys()), format_func=lambda x: months[x], index=datetime.date.today().month-1)
    with col2:
        sel_year = st.number_input("Year", min_value=2024, max_value=2030, value=datetime.date.today().year)
    query_condition = "WHERE EXTRACT(MONTH FROM date::DATE) = %s AND EXTRACT(YEAR FROM date::DATE) = %s"
    query_params = [sel_month, sel_year]
    display_label = f"🗓️ {months[sel_month]} {sel_year}"

elif filter_type == "Yearly 📆":
    with col1:
        sel_year_only = st.number_input("Select Year", min_value=2024, max_value=2030, value=datetime.date.today().year)
    query_condition = "WHERE EXTRACT(YEAR FROM date::DATE) = %s"
    query_params = [sel_year_only]
    display_label = f"📆 {sel_year_only}"

else:
    query_condition = ""
    query_params = []
    display_label = "♾️ All Time"

if st.button("🔄 Update View", type="primary", use_container_width=True):
    st.rerun()

try:
    conn = get_connection()
    
    # ==========================================
    # 💰 1. الملخص المالي
    # ==========================================
    st.header(f"💵 Financial Summary ({display_label})")
    
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

    st.markdown("---")

    # ==========================================
    # ⚖️ 2. مقارنة الفروع (مع أرقام 🔢)
    # ==========================================
    st.header("⚖️ Branch Performance")
    
    tab1, tab2 = st.tabs(["💰 Income by Branch", "📉 Consumption by Branch"])

    with tab1:
        sql_inc_br = f"""
            SELECT branch_name, SUM(amount) as total 
            FROM income 
            {query_condition}
            GROUP BY branch_name
        """
        df_inc_br = pd.read_sql(sql_inc_br, conn, params=query_params)
        
        if not df_inc_br.empty:
            # استخدام دالة الرسم الجديدة (لون أخضر)
            plot_with_labels(df_inc_br, "branch_name", "total", "#2ECC71", "Branch Name", "Total Income")
        else:
            st.info("No data.")

    with tab2:
        sql_exp_br = f"""
            SELECT requester as branch, SUM(total_cost) as total 
            FROM orders 
            {query_condition}
            GROUP BY requester
        """
        df_exp_br = pd.read_sql(sql_exp_br, conn, params=query_params)
        
        if not df_exp_br.empty:
            # استخدام دالة الرسم الجديدة (لون أحمر)
            plot_with_labels(df_exp_br, "branch", "total", "#FF4B4B", "Branch Name", "Total Expense")
        else:
            st.info("No data.")

    st.markdown("---")

    # ==========================================
    # 🏆 3. الأكثر استهلاكاً (Top Materials)
    # ==========================================
    st.subheader("🏆 Top Materials Consumed")
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
        # هنا بنستخدم شارت عادي عشان الأفقي (Horizontal) أسهل في القراءة للأسماء الطويلة
        st.bar_chart(df_top, x="item", y="total_qty", color="#8E44AD", horizontal=True)
        # لو عايز تعرض الجدول كمان للتأكيد:
        st.dataframe(df_top, hide_index=True, use_container_width=True)
    else:
        st.info("No data.")

    # ==========================================
    # 📦 4. النواقص
    # ==========================================
    st.markdown("---")
    st.subheader("🚨 Low Stock Alerts")
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
                "quantity": st.column_config.NumberColumn("Qty", format="%d 📦"),
                "branch_name": "Branch"
            },
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.success("✅ Inventory healthy.")

    conn.close()

except Exception as e:
    st.error(f"Error: {e}")
