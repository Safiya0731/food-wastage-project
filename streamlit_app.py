# streamlit_app.py
import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

st.set_page_config(page_title="Food Wastage Dashboard", layout="wide")
st.title("🍽️ Local Food Wastage Management System")

# -----------------------
# Helper: DB connection
# -----------------------
@st.cache_data
def get_conn():
    # DB file must be in the same folder as this app on Streamlit Cloud / GitHub repo
    conn = sqlite3.connect("food_wastage.db", check_same_thread=False)
    return conn

def run_query(query, params=None):
    conn = get_conn()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    # Convert numeric-looking columns to numeric (safe)
    for c in df.columns:
        if df[c].dtype == object:
            # try converting to numeric if many values look numeric
            try:
                df[c] = pd.to_numeric(df[c], errors="ignore")
            except Exception:
                pass
    return df

# -----------------------
# All queries
# -----------------------
QUERIES = {
    "Query 1 — Providers by City": """
SELECT City, COUNT(*) AS provider_count
FROM providers
GROUP BY City;
""",

    "Query 2 — Receivers by City": """
SELECT City, COUNT(*) AS receiver_count
FROM receivers
GROUP BY City;
""",

    "Query 3 — Provider type (total quantity)": """
SELECT Provider_Type, SUM(Quantity) AS total_quantity
FROM food_listings
GROUP BY Provider_Type
ORDER BY total_quantity DESC;
""",

    # Query 4 will be handled separately because it needs user input (city)
    "Query 5 — Top 5 receivers by number of claims": """
SELECT r.Name AS Receiver_Name,
       COUNT(c.Claim_ID) AS Total_Claims
FROM claims c
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Name
ORDER BY Total_Claims DESC
LIMIT 5;
""",

    "Query 6 — Total quantity available": """
SELECT SUM(CAST(Quantity AS INTEGER)) AS Total_Quantity_Available
FROM food_listings;
""",

    "Query 7 — City with highest number of listings (top 1)": """
SELECT Location AS City,
       COUNT(*) AS total_listings
FROM food_listings
GROUP BY Location
ORDER BY total_listings DESC
LIMIT 1;
""",

    "Query 8 — Food types by total quantity available": """
SELECT COALESCE(Food_Type, 'Unknown') AS Food_Type,
       SUM(COALESCE(CAST(Quantity AS INTEGER), 0)) AS total_quantity_available
FROM food_listings
GROUP BY Food_Type
ORDER BY total_quantity_available DESC;
""",

    "Query 9 — Claims per food item (by name)": """
SELECT f.Food_Name,
       COUNT(c.Claim_ID) AS total_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Food_Name
ORDER BY total_claims DESC;
""",

    "Query 10 — Provider with highest number of completed claims (top 1)": """
SELECT p.Name,
       COUNT(c.Claim_ID) AS successful_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE LOWER(c.Status) = 'completed'
GROUP BY p.Name
ORDER BY successful_claims DESC
LIMIT 1;
""",

    "Query 11 — Percentage of claims by status": """
SELECT Status,
       COUNT(*) AS total_claims,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS percentage
FROM claims
GROUP BY Status;
""",

    "Query 12 — Average quantity claimed per receiver": """
SELECT r.Name AS receiver_name,
       ROUND(AVG(CAST(f.Quantity AS REAL)), 2) AS avg_quantity_claimed
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Name
ORDER BY avg_quantity_claimed DESC;
""",

    "Query 13 — Most claimed meal type (top 1)": """
SELECT f.Meal_Type,
       COUNT(c.Claim_ID) AS total_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Meal_Type
ORDER BY total_claims DESC
LIMIT 1;
""",

    # Query 14 (fixed)
    "Query 14 — Total quantity donated by each provider": """
SELECT p.Name AS provider_name,
       SUM(CAST(f.Quantity AS INTEGER)) AS total_quantity_donated
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Name
ORDER BY total_quantity_donated DESC;
""",

    # Query 15 (fixed)
    "Query 15 — City with highest total quantity claimed (completed only)": """
SELECT r.City AS city,
       SUM(CAST(f.Quantity AS INTEGER)) AS total_quantity_claimed
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
WHERE LOWER(c.Status) = 'completed'
GROUP BY r.City
ORDER BY total_quantity_claimed DESC
LIMIT 1;
"""
}

# -----------------------
# Sidebar / Navigation
# -----------------------
st.sidebar.header("Select query")
all_names = ["Query 4 — Provider contacts in city (interactive)"] + list(QUERIES.keys())
choice = st.sidebar.selectbox("Choose a query to run", all_names)

# optional small help
with st.sidebar.expander("Instructions", expanded=False):
    st.write("Make sure `food_wastage.db` is in the same repo folder as this app.")
    st.write("If a query needs a city, type it when asked and press Run.")

# -----------------------
# Show selected query
# -----------------------
if choice == "Query 4 — Provider contacts in city (interactive)":
    st.subheader("Query 4 — Provider contact information in a specific city")
    city_input = st.text_input("Type city name (example: Jaipur)", value="")
    if st.button("Run Query 4"):
        if city_input.strip() == "":
            st.warning("Please type a city name then press Run.")
        else:
            q4 = """
SELECT Provider_ID, Name, Address, City, Contact
FROM providers
WHERE LOWER(City) = LOWER(?);
"""
            df = run_query(q4, params=(city_input.strip(),))
            if df.empty:
                st.info("No providers found for that city.")
            else:
                st.dataframe(df)
                if df.shape[1] == 2 or df.shape[1] == 5:
                    # if numeric column present, try a simple bar chart for counts
                    try:
                        if "provider_count" in df.columns:
                            st.bar_chart(df.set_index(df.columns[0])[df.columns[1]])
                    except Exception:
                        pass

else:
    st.subheader(choice)
    sql = QUERIES[choice]
    if st.button("Run"):
        df = run_query(sql)
        if df is None or df.empty:
            st.info("No results (empty dataframe).")
        else:
            st.dataframe(df, use_container_width=True)
            # If the result is two columns and the second is numeric — show a bar chart
            if df.shape[1] == 2:
                try:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    # ensure y is numeric
                    df[y_col] = pd.to_numeric(df[y_col], errors="coerce").fillna(0)
                    chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X(x_col, sort=None),
                        y=y_col
                    )
                    st.altair_chart(chart, use_container_width=True)

# -----------------------
# Footer / Close DB connection on exit (optional)
# -----------------------
# Note: Streamlit will keep connection cached by get_conn(); no manual close needed.
st.markdown("---")
st.write("Built with ❤️ — Local Food Wastage Management System")
