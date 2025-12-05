# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="NL2SQL Demo", layout="wide")
st.title("📊 Sales Data Query Demo")

# Sample data
@st.cache_data
def get_data():
    data = {
        'region': ['North', 'South', 'East', 'West'] * 100,
        'product': ['A', 'B', 'C'] * 133 + ['A'],
        'sales': [100, 200, 150, 300] * 100,
        'quantity': [1, 2, 1, 3] * 100
    }
    return pd.DataFrame(data)

df = get_data()
st.write(f"Data loaded: {len(df)} rows")

question = st.selectbox("Ask a question:", [
    "Show total sales by region",
    "Show top products",
    "Show sales distribution"
])

if question == "Show total sales by region":
    result = df.groupby('region')['sales'].sum().reset_index()
    st.bar_chart(result.set_index('region'))
    st.dataframe(result)
    
st.success("✅ Demo working!")