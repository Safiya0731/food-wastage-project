import streamlit as st
import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect("food_wastage.db")

st.title("Food Wastage Data Dashboard")

# Query 1: Provider count by city
query1 = """
SELECT City, COUNT(*) AS provider_count
FROM providers
GROUP BY City;
"""
df1 = pd.read_sql(query1, conn)
st.subheader("Number of Providers by City")
st.dataframe(df1)

# Query 2: Total food donated by each provider
query2 = """
SELECT p.Provider_Name, SUM(f.Quantity) AS total_quantity
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE c.Status = 'Successful'
GROUP BY p.Provider_Name
ORDER BY total_quantity DESC;
"""
df2 = pd.read_sql(query2, conn)
st.subheader("Total Quantity of Food Donated by Each Provider")
st.dataframe(df2)

# Close the connection
conn.close()
