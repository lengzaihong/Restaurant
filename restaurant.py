import streamlit as st
import requests
from requests.structures import CaseInsensitiveDict

# Geoapify API keys
GEOAPIFY_API_KEY = "1b8f2a07690b4cde9b94e68770914821"

# Function to get user's location based on IP
def get_user_location():
    url = f"https://api.geoapify.com/v1/ipinfo?&apiKey={GEOAPIFY_API_KEY}"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Debugging: Print the full response to see what the structure looks like
        st.write("Location data response:", data)
        
        # Safely access latitude, longitude, and city name
        lat = data.get("location", {}).get("latitude")
        lon = data.get("location", {}).get("longitude")
        city = data.get("location", {}).get("city", {}).get("name", "Unknown city")
        
        return lat, lon, city
    else:
        st.error("Failed to retrieve location data.")
        return None, None, None

# Function to get restaurant recommendations using Geoapify Places API
def get_restaurant_recommendations(lat, lon):
    url = f"https://api.geoapify.com/v2/places?categories=catering.restaurant&filter=circle:{lon},{lat},5000&limit=10&apiKey={GEOAPIFY_API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        restaurants = data["features"]
        restaurant_list = [
            {
                "name": place["properties"].get("name", "Unknown name"),
                "address": place["properties"].get("formatted", "No address available"),
                "category": place["properties"]["categories"][0]
            }
            for place in restaurants
        ]
        return restaurant_list
    else:
        st.error("Failed to retrieve restaurant data.")
        return []

# Streamlit app layout
st.title("Restaurant Recommendation System")

# Step 1: Get user's location
st.header("Your Location:")
lat, lon, city = get_user_location()

if lat and lon:
    st.write(f"Detected Location: {city} (Latitude: {lat}, Longitude: {lon})")
    
    # Step 2: Get restaurant recommendations based on the location
    st.header("Nearby Restaurant Recommendations:")
    restaurants = get_restaurant_recommendations(lat, lon)
    
    if restaurants:
        for restaurant in restaurants:
            st.write(f"**{restaurant['name']}**")
            st.write(f"Address: {restaurant['address']}")
            st.write(f"Category: {restaurant['category']}")
            st.write("---")
    else:
        st.write("No restaurants found nearby.")
else:
    st.write("Could not detect location.")
