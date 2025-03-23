from flask import Flask, jsonify, request, render_template, send_from_directory
import requests
import os
import json
from dotenv import load_dotenv
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/population-data', methods=['GET'])
def get_population_data():
    """Get population density data for the heatmap"""
    year = request.args.get('year', '2024')
    district = request.args.get('district', None)
    json_path = "./json/2024_pad_mdbas.json"
    
    try:
        # load from local json file
        data = fetch_population_data(json_path, year, district)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': str(e)}), 500

def fetch_population_data(json_path, year, district=None):
    """read from local for population data json"""
    if not os.path.exists(json_path):
        logger.error(f"json not exist: {json_path}")
        return generate_mock_data(year)
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        
        filtered_records = []
        year_str = f"{year}-01-01"
        
        if isinstance(records, list):
            for record in records:
                if record.get('Data_Referencia') == year_str:
                    if district and record.get('Nom_Districte') != district:
                        continue
                    filtered_records.append(record)
        else:
            logger.warning("wrong json format of date")
            return generate_mock_data(year)
        
        # use mock data instead
        if not filtered_records:
            logger.warning(f"use mock data instead: year={year}, district={district}")
            return generate_mock_data(year)
        
        return process_api_data(filtered_records)
            
    except Exception as e:
        logger.error(f"error when fetch population data: {str(e)}")
        return generate_mock_data(year)

def process_api_data(records):
    """transfer filtered data -> heatmap data"""

    district_coordinates = {
        "Ciutat Vella": (41.3851, 2.1734),
        "Eixample": (41.3917, 2.1630),
        "Sants-Montjuïc": (41.3751, 2.1430),
        "Les Corts": (41.3871, 2.1350),
        "Sarrià-Sant Gervasi": (41.4036, 2.1309),
        "Gràcia": (41.4031, 2.1530),
        "Horta-Guinardó": (41.4169, 2.1674),
        "Nou Barris": (41.4304, 2.1784),
        "Sant Andreu": (41.4305, 2.1894),
        "Sant Martí": (41.4110, 2.2054)
    }
    
    barri_coordinates = {
        "el Raval": (41.3797, 2.1686),
        "el Gòtic": (41.3833, 2.1763),
        "la Barceloneta": (41.3829, 2.1897),
        "Sant Pere, Santa Caterina i la Ribera": (41.3861, 2.1819),
        # ...
    }
    
    def generate_coordinates(record):
        """generate location based on district code"""
        district = record.get('Nom_Districte')
        barri = record.get('Nom_Barri')
        section = record.get('Seccio_Censal')
        
        # use barri location first
        if barri and barri in barri_coordinates:
            base_lat, base_lng = barri_coordinates[barri]
        # else district location
        elif district and district in district_coordinates:
            base_lat, base_lng = district_coordinates[district]
        # default: centre of barcelona
        else:
            base_lat, base_lng = 41.3851, 2.1734
        
        # add offest
        district_id = record.get('Codi_Districte', 0)
        barri_id = record.get('Codi_Barri', 0)
        section_id = record.get('Seccio_Censal', 0)
        
        lat_offset = (district_id * 0.006) + (barri_id * 0.00001) + (section_id * 0.00001)
        lng_offset = (district_id * 0.002) + (barri_id * 0.00009) + (section_id * 0.00001)
        
        return base_lat + lat_offset, base_lng + lng_offset
    
    points = []
    
    for record in records:
        try:
            value = float(record.get('Valor', 0))
            lat, lng = generate_coordinates(record)
            points.append([lat, lng, value])
                
        except (ValueError, TypeError) as e:
            logger.warning(f"处理记录时出错 {record}: {e}")
            continue
    
    if len(points) < 10:
        logger.warning(f"not enough data points")
        mock_points = generate_mock_data("2024")
        points.extend(mock_points[:100-len(points)])
    
    logger.info(f"correct perform with {len(points)} data points")
    return points

def generate_mock_data(year):
    """mock data"""
    
    north = 41.45
    south = 41.32
    east = 2.18
    west = 2.09
    
    np.random.seed(int(year))
    
    points = []
    for _ in range(200): 
        lat = south + (north - south) * np.random.random()
        lng = west + (east - west) * np.random.random()
        
        dist_from_center = np.sqrt(
            np.power(lat - 41.3851, 2) + np.power(lng - 2.1734, 2)
        )
        intensity = 1500 - (dist_from_center * 10000)
        

        if lat > 41.4:  
            intensity *= 0.7  
        if lng < 2.15 and lat < 41.37:  
            intensity *= 1.3  
            
        intensity = max(100, min(2000, intensity)) 
        points.append([lat, lng, intensity])
    
    return points

@app.route('/api/districts', methods=['GET'])
def get_districts():
    """get district location"""
    districts = [
        {"id": "ciutat_vella", "name": "Ciutat Vella"},
        {"id": "eixample", "name": "Eixample"},
        {"id": "sants_montjuic", "name": "Sants-Montjuïc"},
        {"id": "les_corts", "name": "Les Corts"},
        {"id": "sarria_sant_gervasi", "name": "Sarrià-Sant Gervasi"},
        {"id": "gracia", "name": "Gràcia"},
        {"id": "horta_guinardo", "name": "Horta-Guinardó"},
        {"id": "nou_barris", "name": "Nou Barris"},
        {"id": "sant_andreu", "name": "Sant Andreu"},
        {"id": "sant_marti", "name": "Sant Martí"}
    ]
    return jsonify(districts)

@app.route('/api/boundaries/<district>', methods=['GET'])
def get_district_boundaries(district):
    """set boudaries"""
    try:
        # geojson_path = os.path.join(app.static_folder, 'geojson', f'{district}.json')
        geojson_path = "./json/area-estadistica-basica.geojson"
        
        if os.path.exists(geojson_path):
            with open(geojson_path, 'r') as f:
                return jsonify(json.load(f))
        else:
            logger.warning(f"didn;t find the boundaries: {district}")
            return jsonify({"error": "boundaries doesn't exist"}), 404
    except Exception as e:
        logger.error(f"error when fetching boundaries data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)