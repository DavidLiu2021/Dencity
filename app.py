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

# region fetch data from api
@app.route('/api/population-data', methods=['GET'])
def get_population_data():
    """Get population density data for the heatmap"""
    # year = request.args.get('year', '2024')
    district = request.args.get('district', None)
    json_path = "./json/2024_pad_mdbas.json"
    
    try:
        # load from local json file
        data = fetch_population_data(json_path, district)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': str(e)}), 500
# endregion

# region read data from local
def fetch_population_data(json_path, district=None):
    """read from local for population data json"""
    if not os.path.exists(json_path):
        logger.error(f"json not exist: {json_path}")
        return generate_mock_data()
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        
        filtered_records = []
        # year_str = f"{year}-01-01"
        
        if isinstance(records, list):
            for record in records:
                # if record.get('Data_Referencia') == year_str:
                    if district and record.get('Nom_Districte') != district:
                        continue
                    filtered_records.append(record)
        else:
            logger.warning("wrong json format of date")
            return generate_mock_data()
        
        # use mock data instead
        if not filtered_records:
            logger.warning(f"use mock data instead: district={district}")
            return generate_mock_data()
        
        return process_api_data(filtered_records)
            
    except Exception as e:
        logger.error(f"error when fetch population data: {str(e)}")
        return generate_mock_data()
# endregion


# region data process to heatpoint
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
        # Ciutat Vella
        "el Raval": (41.3797223, 2.1686134),
        "el Barri Gòtic": (41.37639828, 2.1728234),
        "la Barceloneta": (41.374599, 2.1869234),
        "Sant Pere, Santa Caterina i la Ribera": (41.3840976, 2.1762239),
        
        # Eixample
        "el Fort Pienc": (41.395334, 2.181323),
        "la Sagrada Família": (41.403797, 2.1735445),
        "la Dreta de l'Eixample": (41.396094, 2.1668367),
        "l'Antiga Esquerra de l'Eixample": (41.3898284, 2.1537083),
        "la Nova Esquerra de l'Eixample": (41.3833284, 2.1427384),
        "Sant Antoni": (41.3867284, 21.1444922),
        
        
        # Sants-Montjuïc
        "el Poble-sec": (41.3708, 2.1579),
        "la Marina de Port": (41.3557, 2.1379),
        "la Font de la Guatlla": (41.3696, 2.1448),
        "Hostafrancs": (41.3579, 2.1575),
        "la Bordeta": (41.3689, 2.1355),
        "Sants - Badal": (41.3718, 2.1226),
        "Sants": (41.3833, 2.1499),
        
        # Les Corts
        "les Corts": (41.3838, 2.1263),
        "Pedralbes": (41.3901, 2.1078),
        "Vallvidrera": (41.4070, 2.10513),
        
        # Sarrià-Sant Gervasi
        "Sarrià": (41.3929, 2.1197),
        "les Tres Torres": (41.3924, 2.1253),
        "Sant Gervasi - la Bonanova": (41.40383, 2.1334),
        "Sant Gervasi - Galvany": (41.3913, 2.1396),
        "el Putxet i el Farró": (41.4069, 2.1439),
        
        # Gràcia
        "Vallcarca i els Penitents": (41.40766, 2.1391),
        "el Coll": (41.418831658, 2.143166094),
        "la Salut": (41.4074850367, 2.1508577299),
        "la Vila de Gràcia": (41.403998384, 2.154832714),
        "el Camp d'en Grassot i Gràcia Nova": (41.4036517187, 2.1671409981),
        
        # Horta-Guinardó
        "el Baix Guinardó": (41.4055350445, 2.16681933272),
        "Can Baró": (41.4166, 2.1622),
        "el Guinardó": (41.418998324, 2.16710266492),
        "la Font d'en Fargues": (41.4216149802, 2.1593160294),
        "el Carmel": (41.421498314, 2.153166054),
        "la Teixonera": (41.4205433178, 2.14084443662),
        "Sant Genís dels Agudells": (41.4237683049, 2.12619449522),
        "Montbau": (41.4252199658, 2.13911277688),
        "la Vall d'Hebron": (41.4240183039, 2.1396077749),
        "Horta": (41.4243666359, 2.15605937576),
        
        # Nou Barris
        "Vilapicina i la Torre Llobeta": (41.4239216376, 2.16918932324),
        "Porta": (41.4341215968, 2.17163431346),
        "el Turó de la Peira": (41.4264699608, 2.15948436206),
        "la Guineueta": (41.4381365808, 2.1698576539), 
        "Canyelles": (41.4462639, 2.1731444),
        "les Roquetes": (41.4425182299, 2.16988432046),
        "Verdun": (41.442, 2.17531),
        "la Prosperitat": (41.4389282443, 2.17567763062),
        "la Trinitat Nova": (41.4424798967, 2.18448092874),
        "Torre Baró": (41.451076529,  2.17379763814),
        "Ciutat Meridiana": (41.4609, 2.1744),
        
        # Sant Andreu
        "la Trinitat Vella": (41.4428082288, 2.18932257604),
        "Baró de Viver": (41.4420748984, 2.20044419822),
        "el Bon Pastor": (41.4365, 2.19989),
        "Sant Andreu": (41.43499826, 2.187999248),
        "la Sagrera": (41.4200799863, 2.1851242595),
        "el Congrés i els Indians": (41.4221933112, 2.17507263304),
        "Navas": (41.409331696, 2.185499258),
        
        # Sant Martí
        "el Camp de l'Arpa del Clot": (41.4068583726, 2.176165962),
        "el Clot": (41.408682, 2.186899),
        "el Parc i la Llacuna del Poblenou": (41.3986, 2.1903),
        "la Vila Olímpica del Poblenou": (41.387831782, 2.192832562),
        "el Poblenou": (41.392831762, 2.202332524),
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
        
        lat_offset = (district_id * 0.001) + (barri_id * 0.00001) + (section_id * 0.00001)
        lng_offset = (district_id * 0.001) + (barri_id * 0.00001) + (section_id * 0.00001)
        
        
        return base_lat, base_lng
        # return base_lat + lat_offset, base_lng + lng_offset
    
    points = []
    
    for record in records:
        try:
            value = float(record.get('Valor', 0))
            lat, lng = generate_coordinates(record)
            points.append([lat, lng, value])
                
        except (ValueError, TypeError) as e:
            logger.warning(f"data dealing error {record}: {e}")
            continue
    
    if len(points) < 10:
        logger.warning(f"not enough data points")
        mock_points = generate_mock_data()
        points.extend(mock_points[:100-len(points)])
    
    logger.info(f"correct perform with {len(points)} data points")
    return points
# endregion

# region mock data
def generate_mock_data():
    """mock data"""
    
    north = 41.45
    south = 41.32
    east = 2.18
    west = 2.09
    
    np.random.seed()
    
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
# endregion

# region get location info on map
@app.route('/api/districts', methods=['GET'])
def get_districts():
    """get district location"""
    districts = [
        # {"id": "ciutat_vella", "name": "Ciutat Vella"},
        {"id": "Ciutat Vella", "name": "Ciutat Vella"},
        {"id": "Eixample", "name": "Eixample"},
        {"id": "Sants-Montjuïc", "name": "Sants-Montjuïc"},
        {"id": "Les Corts", "name": "Les Corts"},
        {"id": "Sarrià-Sant Gervasi", "name": "Sarrià-Sant Gervasi"},
        {"id": "Gràcia", "name": "Gràcia"},
        {"id": "Horta-Guinardó", "name": "Horta-Guinardó"},
        {"id": "Nou Barris", "name": "Nou Barris"},
        {"id": "Sant Andreu", "name": "Sant Andreu"},
        {"id": "Sant Martí", "name": "Sant Martí"}
    ]
    return jsonify(districts)
# endregion

# region get barcelona boundaries
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
# endregion
    
if __name__ == '__main__':
    app.run(debug=True)