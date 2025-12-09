import streamlit as st
import psycopg2
import pandas as pd
import datetime
import altair as alt
from io import BytesIO # 🟢 عشان نتعامل مع ملفات الإكسيل في الذاكرة

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Nexus Cloud ☁️",
    page_icon="🦷",
    layout="wide"
)

# 2. رابط الداتابيز
DB_URL = "postgresql://postgres.thiulhrlurohmfkmxwqw:Mr.junior1966@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)

# --- CSS للتجميل وتقليل الزحمة ---
st.markdown("""
<style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #333;
        text-align: center;
    }
    /* تكبير العناوين شوية */
    h3 { color: #4da6ff; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🖌️ دالة لتوليد إكسيل احترافي (ملون ومنظم)
# ==========================================
def generate_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # 1. تنسيق الهيدر (أزرق غامق + كلام أبيض + بولد)
        header_fmt = workbook.add_format({
            'bold': True,
            'fg_color': '#2C3E50',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # 2. تنسيق الخلايا (كلام في النص + حدود)
        cell_fmt = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # تطبيق التنسيقات
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            # تظبيط عرض العمود أوتوماتيك
            worksheet.set_column(col_num, col_num, 20, cell_fmt)
            
    return output.getvalue()

# ==========================================
# 🖌️ دالة الرسم
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
# 🎛️ القائمة الجانبية (Filters)
# ==========================================
with st.sidebar:
    st.title("⚙️ Controls")
    
    st.write("### 📅 Period Filter")
    filter_type = st.radio(
        "Select Mode:", 
        ["Daily", "Monthly", "Yearly", "All Time"], 
    )

    query_condition = ""
    query_params = []
    display_label = ""

    if filter_type == "Daily":
        sel_date = st.date_input("Select Date", datetime.date.today())
        query_condition = "WHERE date::DATE = %s"
        query_params = [sel_date]
        display_label = f"Daily Report: {sel_date}"

    elif filter_type == "Monthly":
        months = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
                  7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
        c1, c2 = st.columns(2)
        with c1:
            sel_month = st.selectbox("Month", list(months.keys()), format_func=lambda x: months[x], index=datetime.date.today().month-1)
        with c2:
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
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        st.rerun()

# ==========================================
# 🏠 المتن الرئيسي
# ==========================================
st.title("🦷 Nexus Cloud Dashboard")
st.caption(f"Showing Data for: **{display_label}**")

try:
    conn = get_connection()
    
    # 💰 1. KPIs (دايماً في وشك)
    sql_inc = f"SELECT SUM(amount) FROM income {query_condition}"
    df_inc = pd.read_sql(sql_inc, conn, params=query_params)
    inc_val = df_inc.iloc[0,0] if not df_inc.empty and df_inc.iloc[0,0] else 0
    
    sql_exp = f"SELECT SUM(total_cost) FROM orders {query_condition}"
    df_exp = pd.read_sql(sql_exp, conn, params=query_params)
    exp_val = df_exp.iloc[0,0] if not df_exp.empty and df_exp.iloc[0,0] else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Income", f"{inc_val:,.0f}", delta="QAR")
    c2.metric("Expenses", f"{exp_val:,.0f}", delta_color="inverse", delta="QAR")
    profit = inc_val - exp_val
    c3.metric("Net Profit", f"{profit:,.0f}", delta_color="normal" if profit >=0 else "inverse")

    st.divider()

    # 🟢 هنا قللنا الزحمة: فصلنا الرسوم عن الجداول
    main_tabs = st.tabs(["📊 Visual Analysis (Charts)", "📥 Detailed Reports (Excel)"])

    # === Tab 1: الرسوم البيانية فقط (للمدير السريع) ===
    with main_tabs[0]:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("💰 Income by Branch")
            sql_inc_br = f"SELECT branch_name, SUM(amount) as total FROM income {query_condition} GROUP BY branch_name"
            df_inc_br = pd.read_sql(sql_inc_br, conn, params=query_params)
            if not df_inc_br.empty:
                plot_with_labels(df_inc_br, "branch_name", "total", "#2ECC71", "Branch", "Income")
            else:
                st.info("No data.")

        with col_chart2:
            st.subheader("📉 Expense by Branch")
            sql_exp_br = f"SELECT requester as branch, SUM(total_cost) as total FROM orders {query_condition} GROUP BY requester"
            df_exp_br = pd.read_sql(sql_exp_br, conn, params=query_params)
            if not df_exp_br.empty:
                plot_with_labels(df_exp_br, "branch", "total", "#FF4B4B", "Branch", "Expense")
            else:
                st.info("No data.")
        
        st.subheader("🏆 Top Consumed Materials")
        top_sql = f"SELECT item, SUM(qty) as total_qty FROM orders {query_condition} GROUP BY item ORDER BY total_qty DESC LIMIT 7"
        df_top = pd.read_sql(top_sql, conn, params=query_params)
        if not df_top.empty:
            st.bar_chart(df_top, x="item", y="total_qty", color="#8E44AD", horizontal=True)

    # === Tab 2: الجداول والتحميل (للمحاسب والدقة) ===
    with main_tabs[1]:
        st.info("💡 Tip: Click 'Download Excel' to get a formatted report.")
        
        c_r1, c_r2 = st.columns(2)
        
        with c_r1:
            st.write("#### 📄 Income Report")
            if not df_inc_br.empty:
                st.dataframe(df_inc_br, use_container_width=True)
                # زرار الإكسيل المطور
                excel_data = generate_excel(df_inc_br)
                st.download_button(
                    label="📥 Download Excel (Formatted)",
                    data=excel_data,
                    file_name=f"Income_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("No data available.")

        with c_r2:
            st.write("#### 📄 Expense Report")
            if not df_exp_br.empty:
                st.dataframe(df_exp_br, use_container_width=True)
                # زرار الإكسيل المطور
                excel_data_exp = generate_excel(df_exp_br)
                st.download_button(
                    label="📥 Download Excel (Formatted)",
                    data=excel_data_exp,
                    file_name=f"Expense_Report_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("No data available.")

    conn.close()

except Exception as e:
    st.error(f"Error: {e}")
