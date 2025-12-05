# nl2sql_demo.py
import streamlit as st
import pandas as pd
import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any
import openai
import re

# Set page config
st.set_page_config(
    page_title="Sales Data NL2SQL Demo",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Sales Data NL2SQL Demo")
st.markdown("Ask natural language questions about sales data and see the generated SQL and results!")

# ==============================
# 1. Generate Sample Sales Data
# ==============================

@st.cache_data
def generate_sales_data(n_rows: int = 1000):
    """Generate synthetic sales data"""
    
    # Regions and products
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
    products = ['Laptop Pro', 'Phone X', 'Tablet Air', 'Monitor Ultra', 'Keyboard Elite',
                'Mouse Pro', 'Headphones Max', 'Charger Fast', 'Case Premium', 'Stand Adjustable']
    categories = ['Electronics', 'Accessories', 'Computers', 'Mobile']
    payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Cash']
    
    # Generate dates
    start_date = datetime(2023, 1, 1)
    
    data = []
    for i in range(n_rows):
        order_date = start_date + timedelta(days=random.randint(0, 365))
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(50, 2000), 2)
        cost_price = round(unit_price * random.uniform(0.4, 0.7), 2)
        
        row = {
            'order_id': f'ORD{10000 + i}',
            'customer_id': f'CUST{random.randint(1000, 9999)}',
            'order_date': order_date.strftime('%Y-%m-%d'),
            'product': random.choice(products),
            'category': random.choice(categories),
            'region': random.choice(regions),
            'quantity': quantity,
            'unit_price': unit_price,
            'total_sales': round(quantity * unit_price, 2),
            'cost_price': cost_price,
            'profit': round((unit_price - cost_price) * quantity, 2),
            'payment_method': random.choice(payment_methods),
            'customer_type': random.choice(['New', 'Returning', 'VIP']),
            'discount': round(random.uniform(0, 0.3), 2)
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Add some monthly trends
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

# ==============================
# 2. Database Setup
# ==============================

def setup_database(df: pd.DataFrame):
    """Convert DataFrame to SQLite database"""
    conn = sqlite3.connect(':memory:')
    df.to_sql('sales', conn, if_exists='replace', index=False)
    
    # Get schema information
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    columns = cursor.fetchall()
    
    schema = {
        'table': 'sales',
        'columns': {col[1]: col[2] for col in columns},
        'description': {
            'order_id': 'Unique order identifier',
            'customer_id': 'Customer identifier',
            'order_date': 'Date when order was placed',
            'product': 'Product name',
            'category': 'Product category',
            'region': 'Sales region',
            'quantity': 'Number of units sold',
            'unit_price': 'Price per unit',
            'total_sales': 'Total sales amount (quantity × unit_price)',
            'cost_price': 'Cost per unit',
            'profit': 'Profit per transaction (total_sales - cost_price × quantity)',
            'payment_method': 'Payment method used',
            'customer_type': 'Type of customer',
            'discount': 'Discount applied (decimal)'
        }
    }
    
    return conn, schema

# ==============================
# 3. NL2SQL Engine
# ==============================

class NL2SQLEngine:
    def __init__(self, schema: Dict):
        self.schema = schema
        self.examples = self._get_examples()
        
    def _get_examples(self):
        """Provide examples for better SQL generation"""
        return """
        Example questions and their SQL:
        
        1. "Show total sales by region" → 
           SELECT region, SUM(total_sales) as total_sales 
           FROM sales 
           GROUP BY region 
           ORDER BY total_sales DESC
        
        2. "Top 5 products by quantity sold" → 
           SELECT product, SUM(quantity) as total_quantity 
           FROM sales 
           GROUP BY product 
           ORDER BY total_quantity DESC 
           LIMIT 5
        
        3. "Monthly sales trend in 2023" → 
           SELECT strftime('%Y-%m', order_date) as month, 
                  SUM(total_sales) as monthly_sales 
           FROM sales 
           WHERE order_date >= '2023-01-01' 
           GROUP BY month 
           ORDER BY month
        
        4. "Profit by product category" → 
           SELECT category, SUM(profit) as total_profit 
           FROM sales 
           GROUP BY category 
           ORDER BY total_profit DESC
        
        5. "Average discount by customer type" → 
           SELECT customer_type, AVG(discount) as avg_discount 
           FROM sales 
           GROUP BY customer_type
        
        6. "Sales comparison by payment method" → 
           SELECT payment_method, 
                  COUNT(*) as transaction_count,
                  SUM(total_sales) as total_sales
           FROM sales 
           GROUP BY payment_method
        
        7. "Customers with most orders" → 
           SELECT customer_id, COUNT(*) as order_count 
           FROM sales 
           GROUP BY customer_id 
           ORDER BY order_count DESC 
           LIMIT 10
        """
    
    def generate_sql_with_gpt(self, question: str, api_key: str = None):
        """Generate SQL using OpenAI GPT"""
        if not api_key:
            return None, "API key not provided"
            
        try:
            openai.api_key = api_key
            
            prompt = f"""You are a SQL expert. Convert this natural language question to SQLite SQL.
            
            Database Schema:
            Table: {self.schema['table']}
            Columns and Types: {json.dumps(self.schema['columns'], indent=2)}
            
            Column Descriptions:
            {json.dumps(self.schema['description'], indent=2)}
            
            {self.examples}
            
            Important Rules:
            1. Use only the columns from the schema above
            2. Always use table name 'sales'
            3. Return ONLY the SQL query, no explanations
            4. Use proper aggregation when needed (SUM, COUNT, AVG)
            5. Format dates using strftime() if needed
            6. Include ORDER BY for ranking questions
            
            Question: {question}
            
            SQL Query:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that converts natural language to SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            sql = response.choices[0].message.content.strip()
            # Clean up the SQL
            sql = sql.replace('```sql', '').replace('```', '').strip()
            return sql, None
            
        except Exception as e:
            return None, f"GPT Error: {str(e)}"
    
    def generate_sql_rule_based(self, question: str):
        """Simple rule-based SQL generation as fallback"""
        question_lower = question.lower()
        
        # Basic patterns
        if "total sales" in question_lower and "region" in question_lower:
            return "SELECT region, SUM(total_sales) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC"
        elif "top" in question_lower and "product" in question_lower:
            match = re.search(r'top\s+(\d+)', question_lower)
            limit = match.group(1) if match else "5"
            return f"SELECT product, SUM(quantity) as total_quantity FROM sales GROUP BY product ORDER BY total_quantity DESC LIMIT {limit}"
        elif "monthly" in question_lower or "trend" in question_lower:
            return "SELECT strftime('%Y-%m', order_date) as month, SUM(total_sales) as monthly_sales FROM sales GROUP BY month ORDER BY month"
        elif "profit" in question_lower and "category" in question_lower:
            return "SELECT category, SUM(profit) as total_profit FROM sales GROUP BY category ORDER BY total_profit DESC"
        else:
            return "SELECT * FROM sales LIMIT 10"

# ==============================
# 4. Main App
# ==============================

def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Data generation
        n_rows = st.slider("Number of rows to generate", 100, 5000, 1000)
        
        # API Configuration
        st.subheader("AI Configuration")
        use_ai = st.checkbox("Use AI (OpenAI GPT)", value=True)
        
        if use_ai:
            api_key = st.text_input("OpenAI API Key", type="password", 
                                   help="Get your API key from platform.openai.com")
            if not api_key:
                st.warning("Enter OpenAI API key or uncheck to use rule-based queries")
        else:
            api_key = None
            st.info("Using rule-based SQL generation")
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "Show total sales by region",
            "Top 5 products by quantity sold",
            "Monthly sales trend in 2023",
            "Profit by product category",
            "Average discount by customer type",
            "Sales comparison by payment method",
            "Customers with most orders",
            "What is the average unit price by region?",
            "Show me sales by month and region",
            "Which product has the highest profit margin?"
        ]
        
        for q in sample_questions:
            if st.button(f"▸ {q}", key=f"sample_{q}"):
                st.session_state.question = q
    
    # Generate and display data
    st.header("📈 Sales Data Overview")
    
    with st.spinner("Generating sample sales data..."):
        df = generate_sales_data(n_rows)
        conn, schema = setup_database(df)
    
    # Data preview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Total Sales", f"${df['total_sales'].sum():,.2f}")
    with col3:
        st.metric("Total Profit", f"${df['profit'].sum():,.2f}")
    
    # Quick data preview
    with st.expander("View Data Sample"):
        st.dataframe(df.head(10))
    
    # Column information
    with st.expander("View Schema Information"):
        st.json(schema['description'])
    
    # Query Interface
    st.header("🔍 Ask Questions")
    
    # Initialize session state for question
    if 'question' not in st.session_state:
        st.session_state.question = ""
    
    # Question input
    question = st.text_input(
        "Ask a question about your sales data:",
        value=st.session_state.question,
        placeholder="e.g., 'Show me total sales by region'"
    )
    
    if question:
        st.subheader("🧠 Processing Your Question")
        
        # Initialize NL2SQL engine
        engine = NL2SQLEngine(schema)
        
        # Generate SQL
        if use_ai and api_key:
            sql, error = engine.generate_sql_with_gpt(question, api_key)
            method = "AI-Generated"
        else:
            sql = engine.generate_sql_rule_based(question)
            error = None
            method = "Rule-Based"
        
        if error:
            st.error(f"Error generating SQL: {error}")
            st.info("Falling back to rule-based generation...")
            sql = engine.generate_sql_rule_based(question)
            method = "Rule-Based (Fallback)"
        
        # Display SQL
        st.subheader("📝 Generated SQL")
        st.code(sql, language='sql')
        st.caption(f"Method: {method}")
        
        # Execute and display results
        try:
            result_df = pd.read_sql_query(sql, conn)
            
            st.subheader("📊 Results")
            
            # Display metrics for single value results
            if len(result_df) == 1 and len(result_df.columns) == 1:
                col_name = result_df.columns[0]
                value = result_df.iloc[0, 0]
                if isinstance(value, (int, float)):
                    st.metric(col_name.replace('_', ' ').title(), 
                             f"${value:,.2f}" if 'sales' in col_name or 'price' in col_name or 'profit' in col_name else f"{value:,.2f}")
            
            # Display dataframe
            st.dataframe(result_df, use_container_width=True)
            
            # Show summary statistics for numeric columns
            numeric_cols = result_df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                with st.expander("📈 Summary Statistics"):
                    st.dataframe(result_df[numeric_cols].describe())
            
            # Visualization for appropriate results
            if len(result_df) > 1 and len(result_df) <= 20:
                st.subheader("📊 Visualization")
                
                # Determine chart type based on data
                if 'month' in result_df.columns or 'order_date' in result_df.columns:
                    # Time series data
                    time_col = 'month' if 'month' in result_df.columns else 'order_date'
                    numeric_col = next((col for col in result_df.columns 
                                      if col != time_col and pd.api.types.is_numeric_dtype(result_df[col])), None)
                    if numeric_col:
                        chart_data = result_df.set_index(time_col)[numeric_col]
                        st.line_chart(chart_data)
                
                elif 'region' in result_df.columns or 'product' in result_df.columns or 'category' in result_df.columns:
                    # Categorical data
                    cat_col = next((col for col in ['region', 'product', 'category', 'payment_method', 'customer_type'] 
                                  if col in result_df.columns), None)
                    if cat_col:
                        numeric_col = next((col for col in result_df.columns 
                                          if col != cat_col and pd.api.types.is_numeric_dtype(result_df[col])), None)
                        if numeric_col:
                            chart_data = result_df.set_index(cat_col)[numeric_col]
                            st.bar_chart(chart_data)
            
        except Exception as e:
            st.error(f"Error executing SQL: {str(e)}")
            st.info("Try rephrasing your question or check the generated SQL above.")
    
    # Information section
    st.markdown("---")
    st.header("ℹ️ How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 1. Data Generation
        - Synthetic sales data is generated
        - Includes orders, products, regions
        - Realistic patterns and distributions
        """)
    
    with col2:
        st.markdown("""
        ### 2. SQL Generation
        - Natural language → SQL conversion
        - Uses AI (GPT) or rule-based methods
        - Validates against schema
        """)
    
    with col3:
        st.markdown("""
        ### 3. Execution & Display
        - SQL executed on in-memory database
        - Results displayed as tables
        - Automatic visualization
        """)

if __name__ == "__main__":
    main()