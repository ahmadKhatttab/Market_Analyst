import streamlit as st
import pandas as pd
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib.pyplot as plt
import seaborn as sns
# Import database session and model from directory
from database import db_session
from models import CarAd


# Part 1: Backend (Data Retrieval & Feature Engineering)
#احنا دمجنا الback ,front بنفس الفايل 


def load_and_enrich_data():
    """
    Connects to the database via SQLAlchemy, retrieves car listings,
    converts them into a Pandas DataFrame, and applies feature engineering.
    """
    # Fetch data from the database
    query = db_session.query(CarAd).all()
    
    if not query:
        return pd.DataFrame()
        
    # Convert object models into a list of dictionaries for Pandas
    data = []
    for car in query:
        data.append({
            "id": car.id,
            "title": car.title,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "price": car.price,
            "mileage": car.mileage,
            "fuel_type": car.fuel_type,
            "city": car.city
        })
        
    df = pd.DataFrame(data)
    
    # Preliminary cleaning: filter out unpriced listings to guarantee statistical accuracy
    df = df[df['price'] > 0].copy()
    
    # Feature Engineering
    # 1. Calculate vehicle age based on current year 2026
    df['vehicle_age'] = 2026 - df['year']
    
    # 2. Calculate annual mileage to assess asset depreciation rate
    # Replace 0 with 1 to prevent zero-division errors on brand new vehicle models
    df['annual_mileage'] = df['mileage'] / df['vehicle_age'].replace(0, 1)
    
    return df

# Initialize backend data retrieval pipeline and load data into memory
df_market = load_and_enrich_data()



# Part 2: Frontend (UI Layout & Interactive Binding)


st.set_page_config(page_title="Intelligent Market Analyst", layout="wide")

st.title("Intelligent Market Analyst Dashboard")
st.write("An interactive control panel designed to analyze vehicle prices and specifications using scraped data from OpenSooq.")

if df_market.empty:
    st.warning("The database is currently empty or missing. Please run the scraper.py script first to collect market data.")
else:
    # Setup sidebar interface for filtering and data queries
    st.sidebar.header("Data Filtering Options")
    
    # 1. Categorical filter for manufacturing brands
    brands = ["All"] + list(df_market['brand'].unique())
    selected_brand = st.sidebar.selectbox("Select Manufacturer:", brands)
    
    # 2. Range slider filter for listing prices
    min_p, max_p = float(df_market['price'].min()), float(df_market['price'].max())
    selected_price = st.sidebar.slider("Price Range (JOD):", min_p, max_p, (min_p, max_p))
    
    # Apply filtering constraints dynamically to the dataset
    df_filtered = df_market.copy()
    if selected_brand != "All":
        df_filtered = df_filtered[df_filtered['brand'] == selected_brand]
        
    df_filtered = df_filtered[
        (df_filtered['price'] >= selected_price[0]) & 
        (df_filtered['price'] <= selected_price[1])
    ]
    
    
    # Part 3: Analytics (Key Metrics & Statistical Charts)
    
    
    # Structure high-level KPI layout blocks
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listings Available", f"{len(df_filtered)} units")
    with col2:
        avg_price = df_filtered['price'].mean() if not df_filtered.empty else 0
        st.metric("Average Market Price", f"{avg_price:,.0f} JOD")
    with col3:
        avg_age = df_filtered['vehicle_age'].mean() if not df_filtered.empty else 0
        st.metric("Average Fleet Age", f"{avg_age:.1f} years")
        
    st.write("---")
    
    # Structure multi-column chart visualizations
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Market Price Distribution Curve")
        if not df_filtered.empty:
            fig, ax = plt.subplots()
            sns.histplot(df_filtered['price'], kde=True, ax=ax, color="teal")
# استخدمنا مكتبات عشان نعدل ع charts
            # --- Arabic font rendering adjustment for charts ---
            ax.set_xlabel(get_display(arabic_reshaper.reshape("السعر (دينار)")))
            ax.set_ylabel(get_display(arabic_reshaper.reshape("عدد الإعلانات")))
            
            st.pyplot(fig)
        else:
            st.info("Insufficient data available to generate distribution curves.")
            
    with chart_col2:
        st.subheader("Scatter Analysis: Vehicle Age vs Listing Price")
        if not df_filtered.empty:
            fig, ax = plt.subplots()
            
            # Re-shape brand text to render RTL values seamlessly inside graph legends
            df_display = df_filtered.copy()
            df_display['brand'] = df_display['brand'].apply(lambda x: get_display(arabic_reshaper.reshape(str(x))))
            
            sns.scatterplot(data=df_display, x='vehicle_age', y='price', hue='brand', ax=ax, palette='Set2')
            
            # --- Arabic font rendering adjustment for charts ---
            ax.set_xlabel(get_display(arabic_reshaper.reshape("عمر السيارة (بالسنوات)")))
            ax.set_ylabel(get_display(arabic_reshaper.reshape("السعر (دينار)")))
            ax.get_legend().set_title(get_display(arabic_reshaper.reshape("الماركة")))
            
            st.pyplot(fig)
        else:
            st.info("Insufficient data available to generate scatter plots.")
            
    # Display the final engineered dataset at the bottom of the interface

    st.write("---")
    st.subheader("Granular Data View (Engineered Features)")
    st.dataframe(df_filtered[['title', 'brand', 'model', 'year', 'vehicle_age', 'price', 'mileage', 'annual_mileage']])