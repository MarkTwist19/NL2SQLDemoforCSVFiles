# nl2sql_demo.py
import streamlit as st
import pandas as pd
import sqlite3  # Built-in, no pip install needed
import json
import random
from datetime import datetime, timedelta
import re
import os

# Set page config FIRST
st.set_page_config(
    page_title="Sales Data NL2SQL Demo",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Sales Data NL2SQL Demo")
st.markdown("Ask natural language questions about sales data and see the generated SQL and results!")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'conn' not in st.session_state:
    st.session_state.conn = None

# ==============================
# 1. Generate Sample Sales Data (Streamlit Cloud compatible)
# ==============================

def generate_sales_data(n_rows: int = 1000):
    """Generate synthetic sales data - Streamlit Cloud safe"""
    
    # Use deterministic random for consistent results
    random.seed(42)  # Fixed seed for reproducibility
    
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
    products = ['Laptop Pro', 'Phone X', 'Tablet Air', 'Monitor Ultra', 'Keyboard Elite']
    categories = ['Electronics', 'Accessories', 'Computers', 'Mobile']
    payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer']
    
    data = []
    for i in range(n_rows):
        # Use modulo to avoid large date ranges
        order_date = datetime(2023, 1, 1) + timedelta(days=i % 365)
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(50, 1000), 2)
        
        row = {
            'order_id': f'ORD{i:05d}',
            'customer_id': f'CUST{random.randint(1000, 9999)}',
            'order_date': order_date.strftime('%Y-%m-%d'),
            'product': random.choice(products),
            'category': random.choice(categories),
            'region': random.choice(regions),
            'quantity': quantity,
            'unit_price': unit_price,
            'total_sales': round(quantity * unit_price, 2),
            'profit': round(quantity * unit_price * random.uniform(0.2, 0.5), 2),
            'payment_method': random.choice(payment_methods),
            'customer_type': random.choice(['New', 'Returning']),
            'discount': round(random.uniform(0, 0.2), 2)
        }
        data.append(row)
    
    return pd.DataFrame(data)

# ==============================
# 2. Database Setup
# ==============================

def setup_database(df: pd.DataFrame):
    """Convert DataFrame to SQLite database"""
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df.to_sql('sales', conn, if_exists='replace', index=False)
    return conn

# ==============================
# 3. Main App (Simplified for Cloud)
# ==============================

def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        n_rows = st.slider("Sample Data Size", 100, 2000, 500)
        
        if st.button("🔄 Generate Data", type="primary"):
            with st.spinner("Generating data..."):
                st.session_state.df = generate_sales_data(n_rows)
                st.session_state.conn = setup_database(st.session_state.df)
            st.success(f"Generated {n_rows} rows!")
        
        st.markdown("---")
        st.subheader("💡 Try These Questions:")
        
        sample_questions = [
            "Show total sales by region",
            "Top 5 products by quantity",
            "Monthly sales trend",
            "Profit by category",
            "Customer types analysis",
            "Payment methods summary"
        ]
        
        for q in sample_questions:
            if st.button(f"▸ {q}"):
                st.session_state.current_question = q
                st.rerun()
    
    # Initialize if first run
    if st.session_state.df is None:
        with st.spinner("Loading demo data..."):
            st.session_state.df = generate_sales_data(500)
            st.session_state.conn = setup_database(st.session_state.df)
    
    # Display data stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", f"{len(st.session_state.df):,}")
    with col2:
        total_sales = st.session_state.df['total_sales'].sum()
        st.metric("Total Sales", f"${total_sales:,.0f}")
    with col3:
        unique_customers = st.session_state.df['customer_id'].nunique()
        st.metric("Unique Customers", unique_customers)
    
    # Data preview
    with st.expander("📋 View Sample Data"):
        st.dataframe(st.session_state.df.head(10))
    
    # Query interface
    st.header("🔍 Ask Questions About the Data")
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    
    question = st.text_input(
        "Type your question:",
        value=st.session_state.current_question,
        placeholder="e.g., 'Show total sales by region'"
    )
    
    if question:
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
        elif 'profit' in question_lower and 'category' in question_lower:
            sql = """
            SELECT category, SUM(profit) as total_profit 
            FROM sales 
            GROUP BY category 
            ORDER BY total_profit DESC
            """
        else:
            sql = "SELECT * FROM sales LIMIT 10"
        
        # Display SQL
        st.subheader("📝 Generated SQL")
        st.code(sql, language='sql')
        
        # Execute and show results
        try:
            result_df = pd.read_sql_query(sql, st.session_state.conn)
            st.subheader(f"📊 Results ({len(result_df)} rows)")
            
            if not result_df.empty:
                st.dataframe(result_df)
                
                # Simple chart for certain queries
                if 'region' in result_df.columns and 'total_sales' in result_df.columns:
                    st.bar_chart(result_df.set_index('region')['total_sales'])
                elif 'month' in result_df.columns and 'monthly_sales' in result_df.columns:
                    st.line_chart(result_df.set_index('month')['monthly_sales'])
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Try a simpler question like 'Show total sales by region'")
    
    # Footer
    st.markdown("---")
    st.info("💡 **Tip**: Use the sample questions in the sidebar to get started!")

# Run the app
if __name__ == "__main__":
    main()