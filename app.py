from flask import Flask, request, jsonify, render_template
import requests
import pandas as pd
from sklearn.cluster import KMeans
from pandas import json_normalize
import folium
from geopy.distance import geodesic

app = Flask(__name__)

# Foursquare credentials
CLIENT_ID = '5O2OQN1HOFBER5CQ4VJSEBU3PZ54Z3T31EGTNFJ0V04KSKZI'
CLIENT_SECRET = 'H2KIZ3QZRGZD2GVCOSSTL04SQ3N0Y5QWEWQKPQ1VTPQNF24R' 
VERSION = '20180604'
LIMIT = 200

# Helper function to fetch Foursquare data
def fetch_foursquare_data(lat, lng, query='Apartment', radius=18000):
    url = f'https://api.foursquare.com/v2/venues/search?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&v={VERSION}&ll={lat},{lng}&query={query}&radius={radius}&limit={LIMIT}'
    response = requests.get(url).json()
    venues = response['response']['venues']
    df = json_normalize(venues)
    return df

# Helper function to process data and apply K-means clustering
def get_clusters(lat, lng, kclusters=3):
    df = fetch_foursquare_data(lat, lng)
    if df.empty:
        return None
    kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(df[['location.lat', 'location.lng']])
    df['Cluster'] = kmeans.labels_
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map():
    return render_template('map.html')


@app.route('/api/map', methods=['POST'])
def get_map():
    data = request.get_json()
    lat = data['latitude']
    lng = data['longitude']
    college_location = (lat, lng)
    df_clusters = get_clusters(lat, lng)
    if df_clusters is None:
        return jsonify({'error': 'No data found'}), 404
    
    # Generate map with clusters
    map_bang = folium.Map(location=[lat, lng], zoom_start=10)
    for _, row in df_clusters.iterrows():
        apartment_location = (row['location.lat'], row['location.lng'])
        distance = geodesic(college_location, apartment_location).kilometers  # Calculate distance

        popup_content = f"<b>{row['name']}</b><br>Distance: {distance:.2f} km"
        popup = folium.Popup(popup_content, max_width=200, min_width=150)  # Set width
        folium.CircleMarker(
            [row['location.lat'], row['location.lng']],
            radius=5,
            color='blue',
            fill=True,
            fill_opacity=0.6,
            popup=popup
        ).add_to(map_bang)
    folium.Marker([lat, lng], popup="My Location", icon=folium.Icon(color="red")).add_to(map_bang)
    map_bang.save('templates/map.html')
    return jsonify({'message': 'Map generated successfully'})
    
if __name__ == '__main__':
    app.run(debug=True)
