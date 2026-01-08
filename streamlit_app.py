import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

import streamlit as st
import pandas as pd
import mysql.connector

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Ola Ride Insights",
    page_icon="🚗",
    layout="wide"
)

# -----------------------------
# MYSQL CONNECTION
# -----------------------------
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )

def fetch_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -----------------------------
# TITLE
# -----------------------------
st.title("🚗 Ola Ride Insights Dashboard")
st.markdown("---")

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Filters")

vehicle_df = fetch_data("SELECT DISTINCT vehicle_type FROM ola_dataset_cleaned")
vehicle_list = vehicle_df["vehicle_type"].dropna().tolist()

vehicle_filter = st.sidebar.multiselect(
    "Select Vehicle Type",
    vehicle_list,
    default=vehicle_list
)

vehicle_condition = ",".join([f"'{v}'" for v in vehicle_filter])

# -----------------------------
# KPIs
# -----------------------------
kpi_query = f"""
SELECT
    COUNT(*) AS total_rides,
    SUM(CASE WHEN booking_status LIKE '%Success%' THEN 1 ELSE 0 END) AS completed_rides,
    SUM(CASE WHEN booking_status LIKE '%Customer%' OR booking_status LIKE '%Driver%' THEN 1 ELSE 0 END) AS cancelled_rides,
    SUM(CASE WHEN booking_status LIKE '%Success%' THEN booking_value ELSE 0 END) AS revenue,
    AVG(customer_rating) AS avg_customer_rating
FROM ola_dataset_cleaned
WHERE vehicle_type IN ({vehicle_condition})
"""

kpi_df = fetch_data(kpi_query)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("🚗 Total Rides", int(kpi_df["total_rides"][0]))
col2.metric("✅ Completed", int(kpi_df["completed_rides"][0]))
col3.metric("❌ Cancelled", int(kpi_df["cancelled_rides"][0]))
col4.metric("💰 Revenue", f"₹ {round(kpi_df['revenue'][0],2)}")
col5.metric("⭐ Avg Rating", round(kpi_df["avg_customer_rating"][0],2))

st.markdown("---")

# -----------------------------
# RIDE TRENDS
# -----------------------------
st.subheader("📈 Ride Trends (Daily)")

trend_query = f"""
SELECT 
    DATE(booking_datetime) AS ride_date,
    COUNT(*) AS total_rides
FROM ola_dataset_cleaned
WHERE vehicle_type IN ({vehicle_condition})
GROUP BY ride_date
ORDER BY ride_date
"""

trend_df = fetch_data(trend_query)
st.line_chart(trend_df.set_index("ride_date"))

# -----------------------------
# REVENUE BY PAYMENT METHOD
# -----------------------------
st.subheader("💳 Revenue by Payment Method")

revenue_query = f"""
SELECT payment_method, SUM(booking_value) AS revenue
FROM ola_dataset_cleaned
WHERE booking_status LIKE '%Success%'
  AND vehicle_type IN ({vehicle_condition})
GROUP BY payment_method
ORDER BY revenue DESC
"""

revenue_df = fetch_data(revenue_query)
st.bar_chart(revenue_df.set_index("payment_method"))

# -----------------------------
# CANCELLATION ANALYSIS
# -----------------------------
st.subheader("❌ Cancellation Reasons (Customer)")

cust_cancel_query = f"""
SELECT 
    COALESCE(cancellation_reason_customer, 'Unknown') AS reason,
    COUNT(*) AS total
FROM ola_dataset_cleaned
WHERE booking_status LIKE '%Customer%'
  AND vehicle_type IN ({vehicle_condition})
GROUP BY reason
ORDER BY total DESC
"""

cust_cancel_df = fetch_data(cust_cancel_query)
st.bar_chart(cust_cancel_df.set_index("reason"))

# -----------------------------
# DRIVER CANCELLATIONS
# -----------------------------
st.subheader("🚕 Cancellation Reasons (Driver)")

driver_cancel_query = f"""
SELECT 
    COALESCE(cancellation_reason_driver, 'Unknown') AS reason,
    COUNT(*) AS total
FROM ola_dataset_cleaned
WHERE booking_status LIKE '%Driver%'
  AND vehicle_type IN ({vehicle_condition})
GROUP BY reason
ORDER BY total DESC
"""

driver_cancel_df = fetch_data(driver_cancel_query)
st.bar_chart(driver_cancel_df.set_index("reason"))

# -----------------------------
# TOP VEHICLE TYPES
# -----------------------------
st.subheader("🚙 Top Vehicle Types by Distance")

vehicle_distance_query = f"""
SELECT vehicle_type, SUM(ride_distance) AS total_distance
FROM ola_dataset_cleaned
WHERE booking_status LIKE '%Success%'
GROUP BY vehicle_type
ORDER BY total_distance DESC
"""

vehicle_dist_df = fetch_data(vehicle_distance_query)
st.bar_chart(vehicle_dist_df.set_index("vehicle_type"))

# -----------------------------
# DATA PREVIEW
# -----------------------------
with st.expander("📄 View Raw Data"):
    preview_df = fetch_data(
        "SELECT * FROM ola_dataset_cleaned LIMIT 100"
    )
    st.dataframe(preview_df)

