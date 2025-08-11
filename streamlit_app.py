import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Database connection
conn = sqlite3.connect("food_wastage.db")

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
        """SELECT City, COUNT(*) AS total_providers
           FROM providers
           GROUP BY City
           ORDER BY total_providers DESC;""",

    "2. Total Receivers by City":
        """SELECT City, COUNT(*) AS total_receivers
           FROM receivers
           GROUP BY City
           ORDER BY total_receivers DESC;""",

    "3. Top Providers by Quantity Donated":
        """SELECT p.Name, SUM(f.Quantity) AS total_quantity
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           WHERE c.Status = 'Successful'
           GROUP BY p.Name
           ORDER BY total_quantity DESC;""",

    "4. Contact Info of Top 5 Providers":
        """SELECT p.Name, p.Contact, SUM(f.Quantity) AS total_quantity
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           WHERE c.Status = 'Successful'
           GROUP BY p.Name, p.Contact
           ORDER BY total_quantity DESC
           LIMIT 5;""",

    "5. Top Receivers by Claims":
        """SELECT r.Name, COUNT(c.Claim_ID) AS total_claims
           FROM claims c
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.Name
           ORDER BY total_claims DESC;""",

    "6. Total Quantity Donated Overall":
        """SELECT SUM(Quantity) AS total_quantity_donated
           FROM food_listings;""",

    "7. Most Common Food Types":
        """SELECT Food_Type, COUNT(*) AS count
           FROM food_listings
           GROUP BY Food_Type
           ORDER BY count DESC;""",

    "8. Claims Count per Food Item":
        """SELECT f.Food_Name, COUNT(c.Claim_ID) AS claim_count
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           GROUP BY f.Food_Name
           ORDER BY claim_count DESC;""",

    "9. Top Providers by Number of Claims":
        """SELECT p.Name, COUNT(c.Claim_ID) AS claim_count
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           GROUP BY p.Name
           ORDER BY claim_count DESC;""",

    "10. Claims Status Percentages":
        """SELECT Status, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims) AS percentage
           FROM claims
           GROUP BY Status;""",

    "11. Average Quantity of Claimed Food":
        """SELECT AVG(f.Quantity) AS avg_quantity
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           WHERE c.Status = 'Successful';""",

    "12. Most Claimed Meal Type":
        """SELECT Meal_Type, COUNT(*) AS claim_count
           FROM food_listings f
           JOIN claims c ON f.Food_ID = c.Food_ID
           WHERE c.Status = 'Successful'
           GROUP BY Meal_Type
           ORDER BY claim_count DESC;""",

    "13. Total Donated Quantity per Provider":
        """SELECT p.Name, SUM(f.Quantity) AS total_quantity
           FROM food_listings f
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           GROUP BY p.Name
           ORDER BY total_quantity DESC;""",

    "14. Expiring Soon Food Items":
        """SELECT Food_Name, Expiry_Date
           FROM food_listings
           WHERE date(Expiry_Date) <= date('now', '+2 day')
           ORDER BY Expiry_Date ASC;""",

    "15. City-wise Demand (Claims)":
        """SELECT r.City, COUNT(c.Claim_ID) AS total_claims
           FROM claims c
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.City
           ORDER BY total_claims DESC;"""
}

# -------------------------------
# Streamlit App UI
# -------------------------------
st.title("🍽 Local Food Wastage Management System")

query_choice = st.selectbox("Select a Query to View Results", list(queries.keys()))

if query_choice:
    df = pd.read_sql(queries[query_choice], conn)
    st.dataframe(df)

    if len(df.columns) >= 2 and df[df.columns[1]].dtype != "object":
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=query_choice)
        st.plotly_chart(fig)

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
