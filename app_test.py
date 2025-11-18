import streamlit as st

st.title(" Test App")
st.write("If you see this, Streamlit is working!")

# Try to import packages
try:
    import pandas as pd
    st.success("✅ Pandas imported")
except Exception as e:
    st.error(f" Pandas error: {e}")

try:
    import plotly
    st.success(" Plotly imported")
except Exception as e:
    st.error(f" Plotly error: {e}")

# Try to load ONE small file
try:
    df = pd.read_csv('data/gun_law_grades_2024.csv')
    st.success(f" Loaded gun laws: {len(df)} rows")
except Exception as e:
    st.error(f" Data load error: {e}")
