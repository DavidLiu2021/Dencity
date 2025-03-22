from flask import Flask, jsonify, request, render_template, send_from_directory
import requests
import os
import json
from dotenv import load_dotenv
import numpy as np

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/population-data', methods=['GET'])
def get_population_data():
    """Get population density data for the heatmap"""
    year = request.args.get('year', '2023')
    district = request.args.get('district', None)
    
    try:
        # Get data from Barcelona Open Data API
        data = fetch_population_data(year, district)
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': str(e)}), 500

def fetch_population_data(year, district=None):
    """Fetch population density data from Barcelona Open Data"""
    try:
        # This is a placeholder URL - replace with actual API endpoint
        base_url = "https://opendata-ajuntament.barcelona.cat/data/api/action/datastore_search"
        
        # You would need to find the correct resource_id for population data
        # For example, the population density by neighborhood dataset
        resource_id = "population-dataset-id"  # Replace with actual dataset ID
        
        params = {
            'resource_id': resource_id,
            'filters': json.dumps({'year': year})
        }
        
        if district:
            params['filters'] = json.dumps({'year': year, 'district': district})
            
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process the API response into heatmap points
            # This transformation will depend on the actual data structure
            points = []
            for record in data.get('result', {}).get('records', []):
                try:
                    lat = float(record.get('latitude'))
                    lng = float(record.get('longitude'))
                    value = float(record.get('population'))
                    points.append([lat, lng, value])
                except (ValueError, TypeError):
                    continue
                    
            return points
        else:
            # If the API fails, use mock data for demo purposes
            app.logger.warning(f"Using mock data as API returned: {response.status_code}")
            return generate_mock_data(year)
            
    except Exception as e:
        app.logger.error(f"Error in fetch_population_data: {str(e)}")
        # Fallback to mock data
        return generate_mock_data(year)

def generate_mock_data(year):
    """Generate mock population density data for demonstration"""