/**
 * Leaflet Map JavaScript for CSIDC Industrial Land Monitoring
 * Handles map initialization, layer management, and API interactions
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Map instance
let map;
let plotsLayer;
let satelliteLayer;
let thermalLayer;
let currentPlotId = null;

// Color mapping for violation types
const VIOLATION_COLORS = {
    'encroachment': '#dc3545',
    'illegal_construction': '#fd7e14',
    'unused_land': '#ffc107',
    'suspicious_change': '#17a2b8',
    'compliant': '#28a745'
};

/**
 * Initialize map on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    initializeDateInputs();
    loadAllPlots();
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    // Create map centered on Chhattisgarh, India
    map = L.map('map').setView([21.2787, 81.8661], 10);

    // Add OpenStreetMap base layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Initialize layer groups
    plotsLayer = L.layerGroup().addTo(map);
    satelliteLayer = L.layerGroup();
    thermalLayer = L.layerGroup();

    // Add layer control
    L.control.layers(
        {
            'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
        },
        {
            'Plots': plotsLayer,
            'Satellite RGB': satelliteLayer,
            'Thermal': thermalLayer
        }
    ).addTo(map);

    console.log('✓ Map initialized');
}

/**
 * Initialize date inputs with default values
 */
function initializeDateInputs() {
    const today = new Date();
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(today.getMonth() - 3);

    document.getElementById('start-date').valueAsDate = threeMonthsAgo;
    document.getElementById('end-date').valueAsDate = today;
}

/**
 * Load all plots from API and display on map
 */
async function loadAllPlots() {
    showLoading(true);
    updateInfo('Loading plots...');

    try {
        const response = await fetch(`${API_BASE_URL}/geojson/all`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Clear existing plots
        plotsLayer.clearLayers();

        // Populate plot selector
        const plotSelect = document.getElementById('plot-select');
        plotSelect.innerHTML = '<option value="">-- Select a plot --</option>';

        let violationCount = 0;

        // Add each plot to map
        data.features.forEach(feature => {
            const props = feature.properties;
            const plotId = props.plot_id;

            // Add to dropdown
            const option = document.createElement('option');
            option.value = plotId;
            option.textContent = `${plotId} - ${props.industry_name || 'N/A'}`;
            plotSelect.appendChild(option);

            // Determine color based on violation status
            const violationStatus = props.violation_status || 'compliant';
            const color = VIOLATION_COLORS[violationStatus];

            if (violationStatus !== 'compliant') {
                violationCount++;
            }

            // Create polygon
            const polygon = L.geoJSON(feature, {
                style: {
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.3
                },
                onEachFeature: function(feature, layer) {
                    // Popup content
                    const popupContent = createPopupContent(props);
                    layer.bindPopup(popupContent);

                    // Click handler
                    layer.on('click', function() {
                        currentPlotId = plotId;
                        document.getElementById('plot-select').value = plotId;
                        showPlotInfo(props);
                    });

                    // Highlight on hover
                    layer.on('mouseover', function() {
                        layer.setStyle({ weight: 4, fillOpacity: 0.5 });
                    });

                    layer.on('mouseout', function() {
                        layer.setStyle({ weight: 2, fillOpacity: 0.3 });
                    });
                }
            });

            plotsLayer.addLayer(polygon);
        });

        // Update statistics
        document.getElementById('total-plots').textContent = data.features.length;
        document.getElementById('total-violations').textContent = violationCount;

        updateInfo(`Loaded ${data.features.length} plots. ${violationCount} violations detected.`);

        // Fit map to plots
        if (plotsLayer.getLayers().length > 0) {
            map.fitBounds(plotsLayer.getBounds());
        }

    } catch (error) {
        console.error('Error loading plots:', error);
        updateInfo(`Error: ${error.message}`);
        alert('Failed to load plots. Please check if the backend is running.');
    } finally {
        showLoading(false);
    }
}

/**
 * Load satellite data for selected plot
 */
async function loadSatelliteData() {
    const plotId = document.getElementById('plot-select').value;
    
    if (!plotId) {
        alert('Please select a plot first');
        return;
    }

    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    if (!startDate || !endDate) {
        alert('Please select date range');
        return;
    }

    showLoading(true);
    updateInfo('Loading satellite data...');

    try {
        const url = `${API_BASE_URL}/satellite?plot_id=${plotId}&start_date=${startDate}&end_date=${endDate}&include_thermal=true`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        updateInfo(`
            <h3>Satellite Data Loaded</h3>
            <p><strong>Plot:</strong> ${plotId}</p>
            <p><strong>RGB URL:</strong> ${data.rgb_url ? '✓ Available' : '✗ Not available'}</p>
            <p><strong>NDVI URL:</strong> ${data.ndvi_url ? '✓ Available' : '✗ Not available'}</p>
            <p><strong>NDBI URL:</strong> ${data.ndbi_url ? '✓ Available' : '✗ Not available'}</p>
            <p><strong>Thermal URL:</strong> ${data.thermal_url ? '✓ Available' : '✗ Not available'}</p>
            <p><strong>Scene Count:</strong> ${data.metadata.sentinel.scene_count || 'N/A'}</p>
        `);

        // In a production app, you would add these as overlay layers
        // For now, we just display the metadata
        console.log('Satellite data:', data);

    } catch (error) {
        console.error('Error loading satellite data:', error);
        updateInfo(`Error: ${error.message}`);
        alert('Failed to load satellite data.');
    } finally {
        showLoading(false);
    }
}

/**
 * Analyze selected plot
 */
async function analyizePlot() {
    const plotId = document.getElementById('plot-select').value;
    
    if (!plotId) {
        alert('Please select a plot first');
        return;
    }

    showLoading(true);
    updateInfo('Analyzing plot... This may take a minute.');

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/${plotId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Display analysis results
        const summary = result.analysis_summary;
        
        updateInfo(`
            <h3>Analysis Complete</h3>
            <p><strong>Plot:</strong> ${plotId}</p>
            <p><strong>Violation Type:</strong> <span class="violation-badge badge-${summary.violation_type}">${summary.violation_type}</span></p>
            <p><strong>Severity:</strong> ${summary.severity.toUpperCase()}</p>
            <p><strong>Confidence:</strong> ${(summary.confidence * 100).toFixed(1)}%</p>
            <hr>
            <p><strong>Recommendation:</strong></p>
            <p style="font-size: 12px; white-space: pre-wrap;">${summary.recommendation}</p>
        `);

        // Reload plots to update colors
        loadAllPlots();

    } catch (error) {
        console.error('Error analyzing plot:', error);
        updateInfo(`Error: ${error.message}`);
        alert('Failed to analyze plot.');
    } finally {
        showLoading(false);
    }
}

/**
 * Create popup content for plot
 */
function createPopupContent(props) {
    const violationBadge = props.violation_status 
        ? `<span class="violation-badge badge-${props.violation_status}">${props.violation_status.replace('_', ' ').toUpperCase()}</span>`
        : '';

    return `
        <div class="custom-popup">
            <h4>${props.plot_id}</h4>
            <p><strong>Industry:</strong> ${props.industry_name || 'N/A'}</p>
            <p><strong>Area:</strong> ${props.approved_area ? props.approved_area.toFixed(2) + ' sqm' : 'N/A'}</p>
            <p><strong>Status:</strong> ${violationBadge}</p>
        </div>
    `;
}

/**
 * Show plot information in sidebar
 */
function showPlotInfo(props) {
    const violationInfo = props.violations && props.violations.length > 0
        ? `<p><strong>Violations:</strong> ${props.violations.length}</p>` +
          props.violations.map(v => 
            `<p style="font-size: 12px;">• ${v.type}: ${v.severity} (${(v.confidence * 100).toFixed(0)}%)</p>`
          ).join('')
        : '<p><strong>Status:</strong> Compliant</p>';

    updateInfo(`
        <h3>Plot Details</h3>
        <p><strong>Plot ID:</strong> ${props.plot_id}</p>
        <p><strong>Industry:</strong> ${props.industry_name || 'N/A'}</p>
        <p><strong>Land Use:</strong> ${props.land_use || 'N/A'}</p>
        <p><strong>Approved Area:</strong> ${props.approved_area ? props.approved_area.toFixed(2) + ' sqm' : 'N/A'}</p>
        ${violationInfo}
    `);
}

/**
 * Update info panel
 */
function updateInfo(content) {
    document.getElementById('info-panel').innerHTML = content;
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

/**
 * Plot selection change handler
 */
document.getElementById('plot-select').addEventListener('change', function(e) {
    const plotId = e.target.value;
    if (plotId) {
        currentPlotId = plotId;
        // Find and highlight the plot
        plotsLayer.eachLayer(function(layer) {
            if (layer.feature && layer.feature.properties.plot_id === plotId) {
                map.fitBounds(layer.getBounds());
                layer.openPopup();
            }
        });
    }
});

console.log('✓ Leaflet map script loaded');
