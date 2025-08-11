import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# Connect to database
conn = sqlite3.connect("food_wastage.db")

st.set_page_config(page_title="Food Wastage Dashboard", layout="wide")
st.title("🍽️ Food Wastage Analysis Dashboard")

try:
    # Query 1 - Providers per city
    query1 = """
    SELECT City, COUNT(*) AS provider_count
    FROM providers
    GROUP BY City;
    """
    df1 = pd.read_sql(query1, conn)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Providers per City")
        st.dataframe(df1)
    with col2:
        fig1 = px.bar(df1, x="City", y="provider_count", title="Providers by City", color="provider_count")
        st.plotly_chart(fig1, use_container_width=True)

    # Query 2 - Receivers per city
    query2 = """
    SELECT City, COUNT(*) AS receiver_count
    FROM receivers
    GROUP BY City;
    """
    df2 = pd.read_sql(query2, conn)
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Receivers per City")
        st.dataframe(df2)
    with col4:
        fig2 = px.bar(df2, x="City", y="receiver_count", title="Receivers by City", color="receiver_count")
        st.plotly_chart(fig2, use_container_width=True)

    # Query 3 - Provider type contribution
    query3 = """
    SELECT Provider_Type, SUM(Quantity) AS total_quantity
    FROM food_listings
    GROUP BY Provider_Type
    ORDER BY total_quantity DESC;
    """
    df3 = pd.read_sql(query3, conn)
    st.subheader("Food Contribution by Provider Type")
    fig3 = px.pie(df3, names="Provider_Type", values="total_quantity", title="Provider Type Contribution")
    st.plotly_chart(fig3, use_container_width=True)

    # Query 4 - Providers contact info by city
    city = st.text_input("Enter a city to view provider contact info:", "New Jessica")
    query4 = """
    SELECT Provider_ID, Name, Address, City, Contact
    FROM providers
    WHERE LOWER(City) = LOWER(?);
    """
    df4 = pd.read_sql(query4, conn, params=(city,))
    st.subheader(f"Providers in {city}")
    st.dataframe(df4)

    # Query 5 - Top 5 Receivers by claims
    query5 = """
    SELECT r.Name AS Receiver_Name, COUNT(c.Claim_ID) AS Total_Claims
    FROM claims c
    JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    GROUP BY r.Name
    ORDER BY Total_Claims DESC
    LIMIT 5;
    """
    df5 = pd.read_sql(query5, conn)
    st.subheader("Top 5 Receivers by Claims")
    fig5 = px.bar(df5, x="Receiver_Name", y="Total_Claims", color="Total_Claims", title="Top Receivers")
    st.plotly_chart(fig5, use_container_width=True)

    # Query 6 - Total food available
    query6 = """
    SELECT SUM(Quantity) AS Total_Quantity_Available
    FROM food_listings;
    """
    df6 = pd.read_sql(query6, conn)
    st.metric("Total Food Available (Units)", df6["Total_Quantity_Available"][0])

    # Query 8 - Common food types
    query8 = """
    SELECT COALESCE(Food_Type, 'Unknown') AS Food_Type,
    SUM(COALESCE(Quantity, 0)) AS total_quantity_available
    FROM food_listings
    GROUP BY Food_Type
    ORDER BY total_quantity_available DESC;
    """
    df8 = pd.read_sql(query8, conn)
    st.subheader("Most Common Food Types")
    fig8 = px.bar(df8, x="Food_Type", y="total_quantity_available", color="total_quantity_available")
    st.plotly_chart(fig8, use_container_width=True)

    # Query 11 - Claims by status
    query11 = """
    SELECT Status, COUNT(*) AS total_claims,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS percentage
    FROM claims
    GROUP BY Status;
    """
    df11 = pd.read_sql(query11, conn)
    st.subheader("Claims Status Distribution")
    fig11 = px.pie(df11, names="Status", values="total_claims", title="Claims Status")
    st.plotly_chart(fig11, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {e}")

st.markdown("---")
st.write("✅ End of Food Wastage Report")
