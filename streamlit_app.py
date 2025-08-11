# streamlit_app.py
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Food Wastage Dashboard", layout="wide")
st.title("🍽️ Local Food Wastage Management System")

# ---------------------------
# Cached DB connection
# ---------------------------
@st.cache_data
def get_conn(db_path: str = "food_wastage.db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

conn = get_conn()

# ---------------------------
# Helper to run queries
# ---------------------------
def run_sql(query: str, params: tuple | None = None) -> pd.DataFrame:
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"SQL execution error:\n{e}")
        return pd.DataFrame()
    # Try to convert numeric-like columns to numeric types where sensible
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_numeric(df[col], errors="ignore")
            except Exception:
                pass
    return df

# ---------------------------
# SQL queries (all 15)
# ---------------------------
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

    "Query 3 — Provider Type (total donated quantity)": """
SELECT Provider_Type, SUM(CAST(Quantity AS INTEGER)) AS total_quantity
FROM food_listings
GROUP BY Provider_Type
ORDER BY total_quantity DESC;
""",

    # Query 4 (interactive) -- handled separately

    "Query 5 — Top 5 receivers by number of claims": """
SELECT r.Name AS Receiver_Name,
       COUNT(c.Claim_ID) AS Total_Claims
FROM claims c
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Name
ORDER BY Total_Claims DESC
LIMIT 5;
""",

    "Query 6 — Total quantity available (all providers)": """
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

    "Query 9 — Number of claims per food item (by name)": """
SELECT f.Food_Name,
       COUNT(c.Claim_ID) AS total_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Food_Name
ORDER BY total_claims DESC;
""",

    "Query 10 — Provider with highest number of completed claims (top 1)": """
SELECT p.Name AS Name,
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
SELECT LOWER(Status) AS Status,
       COUNT(*) AS total_claims,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS percentage
FROM claims
GROUP BY LOWER(Status);
""",

    "Query 12 — Average quantity of food claimed per receiver": """
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

    "Query 14 — Total quantity donated by each provider": """
SELECT p.Name AS provider_name,
       SUM(CAST(f.Quantity AS INTEGER)) AS total_quantity_donated
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Name
ORDER BY total_quantity_donated DESC;
""",

    "Query 15 — City with highest total quantity claimed (completed only, top 1)": """
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

# ---------------------------
# Sidebar navigation
# ---------------------------
st.sidebar.header("Choose view")
options = ["All queries (run in order)"] + ["Query 4 — Provider contacts in a city (interactive)"] + list(QUERIES.keys())
selection = st.sidebar.selectbox("Select an option", options)

# small instructions
st.sidebar.markdown("**Tips:**\n- Make sure `food_wastage.db` is in the same folder as this app.\n- For Query 4, type a city and press Run.")

# ---------------------------
# Helper to display DataFrame and chart if numeric
# ---------------------------
def show_df_and_chart(df: pd.DataFrame, title: str = ""):
    if df is None or df.empty:
        st.info("No results to display.")
        return
    st.dataframe(df, use_container_width=True)
    # If exactly two columns and second is numeric, show bar chart
    if df.shape[1] == 2:
        x_col = df.columns[0]
        y_col = df.columns[1]
        # ensure numeric y
        try:
            df[y_col] = pd.to_numeric(df[y_col], errors="coerce").fillna(0)
            fig = px.bar(df, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}", labels={x_col:x_col, y_col:y_col})
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

# ---------------------------
# Execution: All queries or single
# ---------------------------
if selection == "All queries (run in order)":
    st.header("All queries output")
    # Query 4 param first
    city = st.text_input("Type a city (for Query 4 - Provider contacts)", value="")
    st.write("Running all queries. Scroll down to view results.")
    # Iterate through queries in order, show Query 4 separately
    # 1 & 2 are fine
    # Show Query 1
    st.subheader("1 — Providers by City")
    df = run_sql(QUERIES["Query 1 — Providers by City"])
    show_df_and_chart(df, "Providers by City")

    st.subheader("2 — Receivers by City")
    df = run_sql(QUERIES["Query 2 — Receivers by City"])
    show_df_and_chart(df, "Receivers by City")

    st.subheader("3 — Provider Type (total quantity)")
    df = run_sql(QUERIES["Query 3 — Provider Type (total donated quantity)"])
    show_df_and_chart(df, "Provider Type Contribution")

    st.subheader("4 — Provider contacts in city")
    if city.strip() == "":
        st.info("Type a city above to view provider contacts for Query 4.")
    else:
        q4 = """
SELECT Provider_ID, Name, Address, City, Contact
FROM providers
WHERE LOWER(City) = LOWER(?);
"""
        df = run_sql(q4, params=(city.strip(),))
        show_df_and_chart(df, f"Providers in {city.strip()}")

    st.subheader("5 — Top 5 receivers by number of claims")
    df = run_sql(QUERIES["Query 5 — Top 5 receivers by number of claims"])
    show_df_and_chart(df, "Top receivers")

    st.subheader("6 — Total quantity available (units)")
    df = run_sql(QUERIES["Query 6 — Total quantity available (all providers)"])
    # Show metric if single scalar
    if not df.empty and df.columns[0] in df:
        try:
            total_val = int(df.iloc[0, 0]) if pd.notna(df.iloc[0,0]) else 0
            st.metric("Total Quantity Available", f"{total_val}")
        except Exception:
            st.write(df)

    st.subheader("7 — City with highest number of listings (top 1)")
    df = run_sql(QUERIES["Query 7 — City with highest number of listings (top 1)"])
    show_df_and_chart(df, "City with most listings")

    st.subheader("8 — Food types by total quantity available")
    df = run_sql(QUERIES["Query 8 — Food types by total quantity available"])
    show_df_and_chart(df, "Food types by quantity")

    st.subheader("9 — Claims per food item (by name)")
    df = run_sql(QUERIES["Query 9 — Number of claims per food item (by name)"])
    show_df_and_chart(df, "Claims per food item")

    st.subheader("10 — Provider with highest number of completed claims (top 1)")
    df = run_sql(QUERIES["Query 10 — Provider with highest number of completed claims (top 1)"])
    show_df_and_chart(df, "Top provider (completed claims)")

    st.subheader("11 — Percentage of claims by status")
    df = run_sql(QUERIES["Query 11 — Percentage of claims by status"])
    if not df.empty:
        # show table and pie
        st.dataframe(df, use_container_width=True)
        try:
            fig = px.pie(df, names=df.columns[0], values=df.columns[1], title="Claims status distribution")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    st.subheader("12 — Average quantity claimed per receiver")
    df = run_sql(QUERIES["Query 12 — Average quantity of food claimed per receiver"])
    show_df_and_chart(df, "Avg quantity per receiver")

    st.subheader("13 — Most claimed meal type (top 1)")
    df = run_sql(QUERIES["Query 13 — Most claimed meal type (top 1)"])
    show_df_and_chart(df, "Most claimed meal type")

    st.subheader("14 — Total quantity donated by each provider")
    df = run_sql(QUERIES["Query 14 — Total quantity donated by each provider"])
    show_df_and_chart(df, "Total donated by provider")

    st.subheader("15 — City with highest total quantity claimed (completed only)")
    df = run_sql(QUERIES["Query 15 — City with highest total quantity claimed (completed only, top 1)"])
    show_df_and_chart(df, "City with highest total claimed quantity")

elif selection == "Query 4 — Provider contacts in a city (interactive)":
    st.header("Query 4 — Provider contact information in a specific city")
    city_input = st.text_input("Enter city name (example: Jaipur)", value="")
    if st.button("Run Query 4"):
        if city_input.strip() == "":
            st.warning("Please type a city name then press Run.")
        else:
            q4 = """
SELECT Provider_ID, Name, Address, City, Contact
FROM providers
WHERE LOWER(City) = LOWER(?);
"""
            df = run_sql(q4, params=(city_input.strip(),))
            show_df_and_chart(df, f"Providers in {city_input.strip()}")

else:
    # Single-query view for any of the named queries
    st.header(selection)
    sql_text = QUERIES.get(selection)
    if sql_text is None:
        st.error("Query not found.")
    else:
        if st.button("Run"):
            df = run_sql(sql_text)
            show_df_and_chart(df, selection)

st.markdown("---")
st.caption("Built with ❤️ — Local Food Wastage Management System")

