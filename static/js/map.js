const map = L.map('map').setView([41.3851, 2.1734], 13);

// Add the base map tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Variables to store layers
let heatmapLayer = null;
let districtLayer = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Load districts dropdown
    loadDistricts();
    
    // Set up event listener for update button
    document.getElementById('updateMap').addEventListener('click', updateHeatmap);
    
    // Initialize the map with default data
    updateHeatmap();
});

// Function to load districts into dropdown
async function loadDistricts() {
    try {
        const response = await fetch('/api/districts');
        const districts = await response.json();
        
        const districtSelect = document.getElementById('district');
        
        districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.id;
            option.textContent = district.name;
            districtSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading districts:', error);
    }
}

// Function to update the heatmap
async function updateHeatmap() {
    // Get selected options
    const year = document.getElementById('year').value;
    const district = document.getElementById('district').value;
    
    try {
        // Construct API URL with query parameters
        let url = `/api/population-data?year=${year}`;
        if (district) {
            url += `&district=${district}`;
            // Load district boundary if a specific district is selected
            await loadDistrictBoundary(district);
        } else {
            // Remove district boundary if viewing all districts
            if (districtLayer) {
                map.removeLayer(districtLayer);
                districtLayer = null;
            }
        }
        
        // Fetch the data
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove existing heatmap layer if it exists
        if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
        }
        
        // Create and add the new heatmap layer
        heatmapLayer = L.heatLayer(data, {
            radius: 25,
            blur: 15,
            maxZoom: 17,
            max: 100,
            gradient: {
                0.4: 'blue',
                0.6: 'cyan',
                0.7: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            }
        }).addTo(map);
        
    } catch (error) {
        console.error('Error updating heatmap:', error);
        alert('Failed to load population data. Please try again later.');
    }
}

// Function to load district boundary
async function loadDistrictBoundary(district) {
    try {
        // Remove existing district layer if present
        if (districtLayer) {
            map.removeLayer(districtLayer);
        }
        
        const response = await fetch(`/api/boundaries/${district}`);
        
        if (!response.ok) {
            // If district boundary is not found, just log it
            console.warn(`District boundary not found for ${district}`);
            return;
        }
        
        const geojson = await response.json();
        
        // Add the geojson as a layer
        districtLayer = L.geoJSON(geojson, {
            style: {
                color: "#ff7800",
                weight: 2,
                opacity: 0.7,
                fillOpacity: 0.1
            }
        }).addTo(map);
        
        // Zoom to district bounds
        map.fitBounds(districtLayer.getBounds());
        
    } catch (error) {
        console.error('Error loading district boundary:', error);
    }
}