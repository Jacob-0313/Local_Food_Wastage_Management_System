import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Food Redistribution Dashboard", layout="wide")

# -----------------------------
# Load CSV and Remove Duplicates
# -----------------------------
@st.cache_data
def load_clean_data():
    food = pd.read_csv("food_listings_data.csv").drop_duplicates(subset="Food_ID")
    providers = pd.read_csv("providers_data.csv").drop_duplicates(subset="Provider_ID")
    receivers = pd.read_csv("receivers_data.csv").drop_duplicates(subset="Receiver_ID")
    claims = pd.read_csv("claims_data.csv").drop_duplicates(subset="Claim_ID")
    return food, providers, receivers, claims

food_df, providers_df, receivers_df, claims_df = load_clean_data()

# -----------------------------
# Save Clean Data to SQLite
# -----------------------------
conn = sqlite3.connect("food_redistribution.db")

food_df.to_sql("food_listings", conn, if_exists="replace", index=False)
providers_df.to_sql("providers", conn, if_exists="replace", index=False)
receivers_df.to_sql("receivers", conn, if_exists="replace", index=False)
claims_df.to_sql("claims", conn, if_exists="replace", index=False)

# -----------------------------
# Header
# -----------------------------
col1, col2 = st.columns([6,1])

with col1:
    st.markdown("""
        <h1 style='margin-bottom:0;'>Food Redistribution Dashboard</h1>
        <p style='margin-top:0; font-size:18px; color:gray;'>
        Precision Logistics for a Zero-Waste World
        </p>
    """, unsafe_allow_html=True)

with col2:
    st.image("D:\Downloads\Gemini_Generated_Image_hqirgmhqirgmhqir.png", width=80)


st.markdown("---")

# -----------------------------
# Load Main Tables
# -----------------------------
food_df = pd.read_sql("SELECT * FROM food_listings", conn)
claims_df = pd.read_sql("SELECT * FROM claims", conn)
providers_df = pd.read_sql("SELECT * FROM providers", conn)

# -----------------------------
# KPI Cards (Gradient Style)
# -----------------------------
st.subheader("Key Metrics")

k1, k2, k3 = st.columns(3)

k1.markdown(f"""
<div style="background: linear-gradient(135deg,#43cea2,#185a9d);
padding:20px;border-radius:12px;color:white;text-align:center">
<h4>📦 Total Listings</h4>
<h2>{len(food_df)}</h2>
</div>
""", unsafe_allow_html=True)

k2.markdown(f"""
<div style="background: linear-gradient(135deg,#36d1dc,#5b86e5);
padding:20px;border-radius:12px;color:white;text-align:center">
<h4>📑 Total Claims</h4>
<h2>{len(claims_df)}</h2>
</div>
""", unsafe_allow_html=True)

k3.markdown(f"""
<div style="background: linear-gradient(135deg,#ff9966,#ff5e62);
padding:20px;border-radius:12px;color:white;text-align:center">
<h4>🏢 Active Providers</h4>
<h2>{providers_df['Provider_ID'].nunique()}</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# Dataset Selection
# -----------------------------
table_options = {
    "Food Catalogue": "food_listings",
    "Claims Data": "claims",
    "Providers Data": "providers",
    "Receivers Data": "receivers"
}

selected_view = st.selectbox("Select Dataset", list(table_options.keys()))
selected_table = table_options[selected_view]

df = pd.read_sql(f"SELECT * FROM {selected_table}", conn)

# -----------------------------
# Tabs Layout
# -----------------------------
tab1, tab2, = st.tabs(["Table View"," ANALYTICS - SQL Queries"])

# =============================
# TAB 1 – TABLE VIEW
# =============================
with tab1:
    st.subheader(selected_view)

    filtered_df = df.copy()

    for col in df.columns:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) < 20:
            selected_val = st.selectbox(f"Filter by {col}", ["All"] + list(unique_vals), key=col)
            if selected_val != "All":
                filtered_df = filtered_df[filtered_df[col] == selected_val]

    st.dataframe(filtered_df, use_container_width=True)


# =============================
# TAB 2 – ANALYTICS
# =============================
with tab2:

    st.subheader("SQL Insights")

    query_option = st.selectbox(
        "Choose Analysis",
        (
            "Total Food Available",
            "Providers per City",
            "Most Common Food Type",
            "Provider with Most Claims"
        )
    )

    if query_option == "Total Food Available":
        result = pd.read_sql("SELECT SUM(Quantity) AS Total_Food FROM food_listings", conn)
        st.dataframe(result)
        st.bar_chart(result.set_index(result.columns[0]))

    elif query_option == "Providers per City":
        result = pd.read_sql("""
            SELECT City, COUNT(*) AS Provider_Count
            FROM providers
            GROUP BY City
        """, conn)
        st.dataframe(result)
        st.bar_chart(result.set_index("City"))

    elif query_option == "Most Common Food Type":
        result = pd.read_sql("""
            SELECT Food_Type, COUNT(*) AS Count
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY Count DESC
        """, conn)
        st.dataframe(result)
        st.bar_chart(result.set_index("Food_Type"))

    elif query_option == "Provider with Most Claims":
        result = pd.read_sql("""
            SELECT p.Name, COUNT(c.Claim_ID) AS claim_count
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Name
            ORDER BY claim_count DESC
            LIMIT 1
        """, conn)
        st.dataframe(result)

# -----------------------------
# Expiry Alerts
# -----------------------------
if "Expiry_Date" in food_df.columns:
    food_df["Expiry_Date"] = pd.to_datetime(food_df["Expiry_Date"], errors="coerce")
    soon_expiring = food_df[
        food_df["Expiry_Date"] <= datetime.now() + timedelta(days=2)
    ]

    if not soon_expiring.empty:
        st.error("⚠️ Food items expiring within the next 48 hours!")
        st.dataframe(soon_expiring, use_container_width=True)

st.markdown("---")

st.subheader("SQL Query Results")

query = st.selectbox(
    "Choose a question",
    (
        "Q1: Total Food Available",
        "Q2: Providers per City",
        "Q3: Receivers per City",
        "Q4: Provider-wise Total Food Donated",
        "Q5: Average Food Provided by Each Provider",
        "Q6: City with Highest Food Listings",
        "Q7: Most Common Food Type",
        "Q8: Claims per Food Item",
        "Q9: Provider with Most Claims",
        "Q10: Average Food Claimed per Receiver",
        "Q11: Most Claimed Meal Type",
        "Q12: City with Highest Claims",
        "Q13: Food Type Claimed the Most",
        "Q14: Average Quantity per Listing",
        "Q15: Provider-wise Average Donation"
    ),
    key="final_sql_section"
)

# Helper function to show chart automatically
def show_chart(df):
    if df.shape[1] >= 2:
        try:
            chart_df = df.set_index(df.columns[0])
            st.bar_chart(chart_df)
        except:
            pass


if query == "Q1: Total Food Available":
    df = pd.read_sql("""
        SELECT SUM(Quantity) AS total_food_available
        FROM food_listings
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q2: Providers per City":
    df = pd.read_sql("""
        SELECT City, COUNT(*) AS provider_count
        FROM providers
        GROUP BY City
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q3: Receivers per City":
    df = pd.read_sql("""
        SELECT City, COUNT(*) AS receiver_count
        FROM receivers
        GROUP BY City
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q4: Provider-wise Total Food Donated":
    df = pd.read_sql("""
        SELECT p.Name, SUM(f.Quantity) AS total_food
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q5: Average Food Provided by Each Provider":
    df = pd.read_sql("""
        SELECT p.Name, AVG(f.Quantity) AS avg_food
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q6: City with Highest Food Listings":
    df = pd.read_sql("""
        SELECT Location, COUNT(*) AS listing_count
        FROM food_listings
        GROUP BY Location
        ORDER BY listing_count DESC
        LIMIT 1
    """, conn)
    st.dataframe(df)


elif query == "Q7: Most Common Food Type":
    df = pd.read_sql("""
        SELECT Food_Type, COUNT(*) AS count
        FROM food_listings
        GROUP BY Food_Type
        ORDER BY count DESC
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q8: Claims per Food Item":
    df = pd.read_sql("""
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q9: Provider with Most Claims":
    df = pd.read_sql("""
        SELECT p.Name, COUNT(c.Claim_ID) AS claim_count
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY claim_count DESC
        LIMIT 1
    """, conn)
    st.dataframe(df)


elif query == "Q10: Average Food Claimed per Receiver":
    df = pd.read_sql("""
        SELECT r.Name, AVG(f.Quantity) AS avg_quantity
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q11: Most Claimed Meal Type":
    df = pd.read_sql("""
        SELECT f.Meal_Type, COUNT(*) AS claim_count
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Meal_Type
        ORDER BY claim_count DESC
    """, conn)
    st.dataframe(df)
    show_chart(df)


elif query == "Q12: City with Highest Claims":
    df = pd.read_sql("""
        SELECT f.Location, COUNT(*) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Location
        ORDER BY total_claims DESC
        LIMIT 1
    """, conn)
    st.dataframe(df)


elif query == "Q13: Food Type Claimed the Most":
    df = pd.read_sql("""
        SELECT f.Food_Type, COUNT(*) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Type
        ORDER BY total_claims DESC
        LIMIT 1
    """, conn)
    st.dataframe(df)


elif query == "Q14: Average Quantity per Listing":
    df = pd.read_sql("""
        SELECT AVG(Quantity) AS avg_quantity
        FROM food_listings
    """, conn)
    st.dataframe(df)


elif query == "Q15: Provider-wise Average Donation":
    df = pd.read_sql("""
        SELECT p.Name, AVG(f.Quantity) AS avg_donation
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
    """, conn)
    st.dataframe(df)
    show_chart(df)



st.markdown("---")

st.caption("Food Redistribution System | Portfolio Project")
