# app.py - Streamlit Cloud Compatible Version
import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

st.set_page_config(
    page_title="NL2SQL Sales Demo",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales Data NL2SQL Demo")
st.markdown("Ask questions about sales data in plain English")

# Session state initialization
if 'df' not in st.session_state:
    st.session_state.df = None
if 'conn' not in st.session_state:
    st.session_state.conn = None

def create_sample_data(rows=500):
    """Create sample sales data"""
    data = []
    for i in range(rows):
        data.append({
            'order_id': f'ORD{i:05d}',
            'customer_id': f'CUST{random.randint(1000, 9999)}',
            'order_date': (datetime(2023, 1, 1) + timedelta(days=i % 365)).strftime('%Y-%m-%d'),
            'product': random.choice(['Laptop', 'Phone', 'Tablet', 'Monitor']),
            'region': random.choice(['North', 'South', 'East', 'West']),
            'quantity': random.randint(1, 5),
            'price': round(random.uniform(100, 2000), 2),
            'total_sales': 0  # Will calculate
        })
    
    df = pd.DataFrame(data)
    df['total_sales'] = df['quantity'] * df['price']
    return df

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    rows = st.slider("Data Size", 100, 1000, 300)
    
    if st.button("Generate Data", type="primary") or st.session_state.df is None:
        with st.spinner("Creating sample data..."):
            st.session_state.df = create_sample_data(rows)
            st.session_state.conn = sqlite3.connect(':memory:')
            st.session_state.df.to_sql('sales', st.session_state.conn, index=False)
        st.success(f"Created {rows} sales records")

# Main content
if st.session_state.df is not None:
    st.header("📈 Data Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", len(st.session_state.df))
    with col2:
        st.metric("Total Sales", f"${st.session_state.df['total_sales'].sum():,.0f}")
    with col3:
        st.metric("Avg Order", f"${st.session_state.df['total_sales'].mean():,.0f}")
    
    # Query interface
    st.header("🔍 Ask Questions")
    
    question = st.selectbox(
        "Choose a question or type your own:",
        [
            "Show total sales by region",
            "Top products by quantity sold",
            "Monthly sales trend",
            "Average price by product",
            "Custom query..."
        ]
    )
    
    if question == "Custom query...":
        custom_q = st.text_input("Type your question:")
        if custom_q:
            question = custom_q
    
    if question and question != "Custom query...":
        # Simple rule-based SQL generation
        question_lower = question.lower()
        
        if 'total sales' in question_lower and 'region' in question_lower:
            sql = """
            SELECT region, SUM(total_sales) as total_sales 
            FROM sales 
            GROUP BY region 
            ORDER BY total_sales DESC
            """
        elif 'top' in question_lower and 'product' in question_lower:
            sql = """
            SELECT product, SUM(quantity) as total_quantity 
            FROM sales 
            GROUP BY product 
            ORDER BY total_quantity DESC 
            LIMIT 5
            """
        elif 'monthly' in question_lower or 'trend' in question_lower:
            sql = """
            SELECT strftime('%Y-%m', order_date) as month, 
                   SUM(total_sales) as monthly_sales 
            FROM sales 
            GROUP BY month 
            ORDER BY month
            """
        elif 'average' in question_lower and 'price' in question_lower:
            sql = """
            SELECT product, AVG(price) as avg_price 
            FROM sales 
            GROUP BY product 
            ORDER BY avg_price DESC
            """
        else:
            sql = "SELECT * FROM sales LIMIT 10"
        
        # Display and execute
        st.subheader("📝 Generated SQL")
        st.code(sql, language='sql')
        
        try:
            result = pd.read_sql_query(sql, st.session_state.conn)
            st.subheader("📊 Results")
            st.dataframe(result)
            
            # Simple visualization
            if len(result) > 1:
                if 'region' in result.columns and 'total_sales' in result.columns:
                    st.bar_chart(result.set_index('region')['total_sales'])
                elif 'month' in result.columns and 'monthly_sales' in result.columns:
                    st.line_chart(result.set_index('month')['monthly_sales'])
                elif 'product' in result.columns and 'avg_price' in result.columns:
                    st.bar_chart(result.set_index('product')['avg_price'])
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Data preview
    with st.expander("👀 View Sample Data"):
        st.dataframe(st.session_state.df.head(10))
else:
    st.info("👈 Click 'Generate Data' in the sidebar to get started!")

st.markdown("---")
st.caption("✨ Demo: Natural Language to SQL for Sales Data")