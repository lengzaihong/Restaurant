import streamlit as st
import requests
import pandas as pd
import gdown
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit.components.v1 import html

# Function to download the CSV from Google Drive
@st.cache
def download_data_from_drive():
    # Google Drive link for the dataset (convert to direct download link)
    url = 'https://drive.google.com/uc?id=1Tc3Hequ5jVjamAfuPhpBv8JvsOp7LSJY'
    output = 'restaurant_reviews.csv'
    
    # Download the file without printing progress (quiet=True)
    gdown.download(url, output, quiet=True)
    
    # Load the dataset
    return pd.read_csv(output)

# Load the dataset of restaurant reviews
reviews_df = download_data_from_drive()

# Geoapify API keys
GEOAPIFY_API_KEY = "1b8f2a07690b4cde9b94e68770914821"

# Display the title
st.title("Restaurant Recommendation System")

# Use streamlit_geolocation to capture the location
location = streamlit_geolocation()

# Extract latitude and longitude from the location dictionary
if location and "latitude" in location and "longitude" in location:
    lat, lon = location["latitude"], location["longitude"]
    coords = f"{lat},{lon}"
    st.write(f"Detected Coordinates: Latitude {lat}, Longitude {lon}")
else:
    lat, lon = None, None

# Input for manual entry of geolocation data if location is not available or to override
coords = st.text_input("Enter your coordinates (latitude,longitude):", value=coords if lat and lon else "")

# Allow the user to change the search radius and category of the restaurant
radius = st.slider("Select search radius (meters):", min_value=1000, max_value=10000, value=5000, step=500)
category = st.selectbox("Select restaurant category:", 
                        ["catering.restaurant", "catering.fast_food", "catering.cafe", "catering.bar"])

# Proceed if either geolocation was found or the user has inputted coordinates
if coords:
    try:
        lat, lon = map(float, coords.split(","))
    except ValueError:
        st.error("Invalid coordinates format. Please enter valid latitude and longitude values separated by a comma.")
        st.stop()

    st.write(f"Using Coordinates: (Latitude: {lat}, Longitude: {lon})")
    
    # Function to fetch restaurant recommendations from Geoapify
    def get_restaurant_recommendations(lat, lon, radius, category):
        url = f"https://api.geoapify.com/v2/places?categories={category}&filter=circle:{lon},{lat},{radius}&limit=10&apiKey={GEOAPIFY_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            restaurants = data["features"]
            restaurant_list = [
                {
                    "name": place["properties"].get("name", "Unknown name"),
                    "address": place["properties"].get("formatted", "No address available"),
                    "category": place["properties"]["categories"][0],
                    "latitude": place["geometry"]["coordinates"][1],
                    "longitude": place["geometry"]["coordinates"][0]
                }
                for place in restaurants
            ]
            return restaurant_list
        else:
            st.error("Failed to retrieve restaurant data.")
            return []

    # Function to match restaurants with CSV data and add ratings
    def match_and_enrich_recommendations(restaurants, reviews_df):
        enriched_recommendations = []
        for restaurant in restaurants:
            # Match by restaurant name (case-insensitive)
            matching_reviews = reviews_df[reviews_df["Restaurant"].str.contains(restaurant['name'], case=False, na=False)]
            if not matching_reviews.empty:
                # Calculate average rating if available
                avg_rating = matching_reviews["Rating"].mean()
                reviews_text = matching_reviews["Review"].tolist()[:5]  # Display a few reviews
                restaurant['avg_rating'] = avg_rating
                restaurant['reviews'] = reviews_text
            else:
                restaurant['avg_rating'] = None
                restaurant['reviews'] = []

            enriched_recommendations.append(restaurant)
        
        # Sort recommendations based on rating (descending)
        enriched_recommendations.sort(key=lambda x: x['avg_rating'] if x['avg_rating'] is not None else 0, reverse=True)
        
        return enriched_recommendations

    # Display restaurant recommendations
    st.header("Nearby Restaurant Recommendations:")
    restaurants = get_restaurant_recommendations(lat, lon, radius, category)
    enriched_recommendations = match_and_enrich_recommendations(restaurants, reviews_df)

    # Create a Folium map centered around the user's location
    m = folium.Map(location=[lat, lon], zoom_start=13)

    # Add a marker for the user's location
    folium.Marker(
            [lat, lon], 
            popup="Your Location",
            icon=folium.Icon(color='blue', icon='user')
        ).add_to(m)

    # Add markers for each recommended restaurant
    for restaurant in enriched_recommendations:
        folium.Marker(
            [restaurant['latitude'], restaurant['longitude']],
            popup=f"{restaurant['name']}<br>{restaurant['address']}<br>Rating: {restaurant.get('avg_rating', 'N/A')}",
            tooltip=restaurant['name'],
            icon=folium.Icon(color='red', icon='cutlery')
        ).add_to(m)

    # Render the map in Streamlit
    folium_map = m._repr_html_()  # Convert to HTML representation
    html(folium_map, height=500)

    if enriched_recommendations:
        for restaurant in enriched_recommendations:
            st.write(f"**{restaurant['name']}**")
            st.write(f"Address: {restaurant['address']}")
            st.write(f"Category: {restaurant['category']}")
            st.write(f"Average Rating: {restaurant.get('avg_rating', 'N/A')}")
            st.write("---")

            # Display reviews if available
            if restaurant['reviews']:
                st.write("**Reviews:**")
                for review in restaurant['reviews']:
                    st.write(f"- {review}")
            else:
                st.write("No reviews found.")
            st.write("---")
    else:
        st.write("No restaurants found nearby.")
else:
    st.write("Waiting for coordinates...")

