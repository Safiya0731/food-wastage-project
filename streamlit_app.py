import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Database connection
conn = sqlite3.connect("food_wastage.db")
cursor = conn.cursor()


# Set page config (this controls layout and initial look)
st.set_page_config(
    page_title="Food Wastage Management System",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for styling
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #000000;
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: black;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    /* Titles */
    h1, h2, h3 {
        color: #FF4B4B;
        font-family: 'Segoe UI', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Load data into SQLite tables
# -------------------------------
providers_df = pd.read_csv("providers_data.csv")
receivers_df = pd.read_csv("receivers_data.csv")
food_listings_df = pd.read_csv("food_listings_data.csv")
claims_df = pd.read_csv("claims_data.csv")

providers_df.to_sql("providers", conn, if_exists="replace", index=False)
receivers_df.to_sql("receivers", conn, if_exists="replace", index=False)
food_listings_df.to_sql("food_listings", conn, if_exists="replace", index=False)
claims_df.to_sql("claims", conn, if_exists="replace", index=False)



# -------------------------------
# Queries
# -------------------------------
queries = {
    "1. Total Providers by City":
        """SELECT City, COUNT(*) AS provider_count
           FROM providers
           GROUP BY City;""",

    "2. Total Receivers by City":
        """SELECT City, COUNT(*) AS receiver_count
           FROM receivers
           GROUP BY City;""",

    "3. Top Providers by Quantity Donated":
        """SELECT Provider_Type, SUM(Quantity) AS total_quantity
           FROM food_listings
           GROUP BY Provider_Type
           ORDER BY total_quantity DESC;""",
           
    "4. Contact info of food providers in a specific city":
        """
        SELECT Provider_ID, Name, Address, City, Contact
        FROM providers
        WHERE LOWER(City) = LOWER(?);
        """,       
    
    "5. Receivers who claimed the most food":
        """SELECT r.Name AS Receiver_Name,COUNT(c.Claim_ID) AS Total_Claims
           FROM claims c
           JOIN receivers r
           ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.Name
           ORDER BY Total_Claims DESC
           limit 5;""",

    "6. Total quantity of food available from all providers":
        """SELECT SUM(Quantity) AS Total_Quantity_Available
           FROM food_listings;""",

    "7. City having the highest number of food listings":
        """SELECT Location as City, COUNT(*) AS total_listings
           FROM food_listings
           GROUP BY Location
           ORDER BY total_listings DESC
           LIMIT 1;""",

    "8. Most commonly available food types":
        """SELECT COALESCE(Food_Type, 'Unknown') AS Food_Type,
           SUM(COALESCE(Quantity, 0)) AS total_quantity_available
           FROM food_listings
           GROUP BY Food_Type
           ORDER BY total_quantity_available DESC;""",

    "9. Claims Count per Food Item":
        """SELECT f.Food_Name,COUNT(c.Claim_ID) AS total_claims
           FROM claims c
           JOIN food_listings f
           ON c.Food_ID = f.Food_ID
           GROUP BY f.Food_Name
           ORDER BY total_claims DESC;""",

    "10. Top Provider by Number of Claims":
        """SELECT p.Name,COUNT(c.Claim_ID) AS successful_claims
           FROM claims c
           JOIN food_listings f
           ON c.Food_ID = f.Food_ID
           JOIN providers p
           ON f.Provider_ID = p.Provider_ID
           WHERE c.Status = 'Completed'
           GROUP BY p.Name
           ORDER BY successful_claims DESC
           Limit 1;""",

    "11. Claims Status Percentages":
        """SELECT Status,COUNT(*) AS total_claims,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS percentage
           FROM claims
           GROUP BY Status;""",

    "12. Average Quantity of Claimed Food per receiver":
        """SELECT r.Name AS receiver_name,ROUND(AVG(f.Quantity), 2) AS avg_quantity_claimed
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.Name
           ORDER BY avg_quantity_claimed DESC;""",

    "13. Most Claimed Meal Type":
        """SELECT f.Meal_Type,COUNT(c.Claim_ID) AS total_claims
           FROM claims c
           JOIN food_listings f 
           ON c.Food_ID = f.Food_ID
           GROUP BY f.Meal_Type
           ORDER BY total_claims DESC
           LIMIT 1;""",

    "14. Total Donated Quantity per Provider ":
        """SELECT p.Name AS provider_name,SUM(f.Quantity) AS total_quantity_donated
           FROM food_listings f
           JOIN providers p 
           ON f.Provider_ID = p.Provider_ID
           GROUP BY p.Name
           ORDER BY total_quantity_donated DESC;""",

    "15. City that received the highest total quantity of claimed food":
        """SELECT r.City AS city,SUM(f.Quantity) AS total_quantity_claimed
           FROM claims c
           JOIN food_listings f 
           ON c.Food_ID = f.Food_ID
           JOIN receivers r 
           ON c.Receiver_ID = r.Receiver_ID
           WHERE c.Status = 'Completed'
           GROUP BY r.City
           ORDER BY total_quantity_claimed DESC
           LIMIT 1;"""
}

# -------------------------------
# Streamlit App UI
# -------------------------------
st.title("🥑 Local Food Wastage Management System")


providers_count = len(providers_df)
receivers_count = len(receivers_df)
total_donations = food_listings_df["Quantity"].sum()


col1, col2, col3 = st.columns(3)
col1.metric("Providers", providers_count)
col2.metric("Receivers", receivers_count)
col3.metric("Total Donations", total_donations)



query_choice = st.selectbox("Select a Query to View Results", list(queries.keys()))

if query_choice:
    if query_choice == "4. Contact info of food providers in a specific city":
        city_input = st.text_input("Enter city name:")
        if city_input:
            df = pd.read_sql(queries[query_choice], conn, params=(city_input,))
            st.dataframe(df.style.set_properties(**{'background-color': '#8dd3fb', 'color': 'black'}))

    else:
        df = pd.read_sql(queries[query_choice], conn)
        st.dataframe(df.style.set_properties(**{'background-color': "#8dd3fb", 'color': 'black'}))


    # Show chart if possible
    if 'df' in locals() and len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=query_choice)
        st.plotly_chart(fig)
        
        st.markdown("---")

st.subheader("CRUD Operations")

# Add Provider
with st.expander("➕ Add Provider"):
    with st.form("add_provider_form"):
        name = st.text_input("Name")
        ptype = st.text_input("Type")
        address = st.text_input("Address")
        city = st.text_input("City")
        contact = st.text_input("Contact")
        submitted = st.form_submit_button("Add")
        if submitted:
            conn.execute("INSERT INTO providers (Name, Type, Address, City, Contact) VALUES (?, ?, ?, ?, ?)",
                         (name, ptype, address, city, contact))
            conn.commit()
            st.success("Provider Added Successfully!")

# Delete Provider
with st.expander("🗑 Delete Provider"):
    prov_id = st.number_input("Provider ID to Delete", min_value=1)
    if st.button("Delete Provider"):
        conn.execute("DELETE FROM providers WHERE Provider_ID = ?", (prov_id,))
        conn.commit()
        st.success("Provider Deleted Successfully!")

# Update Provider
with st.expander("✏ Update Provider Contact"):
    prov_id_u = st.number_input("Provider ID to Update", min_value=1)
    new_contact = st.text_input("New Contact")
    if st.button("Update Contact"):
        conn.execute("UPDATE providers SET Contact = ? WHERE Provider_ID = ?", (new_contact, prov_id_u))
        conn.commit()
        st.success("Contact Updated Successfully!")
        

# Sidebar filters
st.sidebar.header("Filters")

city_filter = st.sidebar.selectbox(
    "Select City", 
    ["All"] + sorted(providers_df["City"].dropna().unique())
)

provider_filter = st.sidebar.selectbox(
    "Select Provider", 
    ["All"] + sorted(providers_df["Name"].dropna().unique())
)

food_type_filter = st.sidebar.selectbox(
    "Select Food Type", 
    ["All"] + sorted(food_listings_df["Food_Type"].dropna().unique())
)

meal_type_filter = st.sidebar.selectbox(
    "Select Meal Type", 
    ["All"] + sorted(food_listings_df["Meal_Type"].dropna().unique())
)



# Apply filters
filtered_providers = providers_df.copy()
filtered_food_listings = food_listings_df.copy()

if city_filter != "All":
    filtered_providers = filtered_providers[filtered_providers["City"] == city_filter]

if provider_filter != "All":
    filtered_providers = filtered_providers[filtered_providers["Name"] == provider_filter]

if food_type_filter != "All":
    filtered_food_listings = filtered_food_listings[filtered_food_listings["Food_Type"] == food_type_filter]

if meal_type_filter != "All":
    filtered_food_listings = filtered_food_listings[filtered_food_listings["Meal_Type"] == meal_type_filter]

# Merge for combined view
filtered_data = pd.merge(
    filtered_food_listings,
    filtered_providers,
    on="Provider_ID",
    how="inner"
)

st.markdown("---")

# Show filtered results
st.subheader("Filtered Food Donations")
st.dataframe(filtered_data)

st.markdown("---")

# Contact provider and receiver section
st.subheader("📞 Contact Providers or Receivers")

contact_type = st.radio(
    "Who do you want to contact?",
    ("Provider", "Receiver")
)


if contact_type == "Provider":
    selected_provider = st.selectbox(
        "Select a Provider",
        providers_df["Name"].unique()
    )
    if selected_provider:
        provider_phone = providers_df.loc[
            providers_df["Name"] == selected_provider, "Contact"
        ].values[0]
        st.markdown(
            f"[📞 Call {selected_provider}](tel:{provider_phone})",
            unsafe_allow_html=True
        )

elif contact_type == "Receiver":
    selected_receiver = st.selectbox(
        "Select a Receiver",
        receivers_df["Name"].unique()
    )
    if selected_receiver:
        receiver_phone = receivers_df.loc[
            receivers_df["Name"] == selected_receiver, "Contact"
        ].values[0]
        st.markdown(
            f"[📞 Call {selected_receiver}](tel:{receiver_phone})",
            unsafe_allow_html=True
        )





