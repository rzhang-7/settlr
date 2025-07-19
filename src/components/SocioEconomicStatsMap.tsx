import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import Papa from 'papaparse';
import 'leaflet/dist/leaflet.css';

// TypeScript interfaces
interface Statistic {
  key: string;
  name: string;
  description: string;
}

interface Neighbourhood {
  HOOD_ID: string;
  AREA_NAME: string;
  geometry: any;
  growth_potential_score: number;
  safety_score: number;
  school_score: number;
  business_job_score: number;
}

interface StatRange {
  min: number;
  max: number;
}

// Define available statistics
const STATISTICS: Statistic[] = [
  {
    key: 'growth_potential_score',
    name: 'Growth Potential',
    description: 'Economic growth potential score'
  },
  {
    key: 'safety_score',
    name: 'Safety',
    description: 'Neighbourhood safety score'
  },
  {
    key: 'school_score',
    name: 'School Proximity',
    description: 'School proximity score'
  },
  {
    key: 'business_job_score',
    name: 'Business & Jobs',
    description: 'Business and job opportunities score'
  }
];

// Color function - red for bad/low scores, blue for good/high scores
function getColor(value: number, min: number, max: number): string {
  if (min === max) return '#cccccc';
  let percent = (value - min) / (max - min);
  percent = Math.max(0, Math.min(1, percent));
  percent = Math.pow(percent, 0.7);
  
  let r: number, g: number, b: number;
  if (percent < 0.5) {
    const t = percent / 0.5;
    r = 255; g = Math.round(255 * t); b = 0;
  } else {
    const t = (percent - 0.5) / 0.5;
    r = Math.round(255 * (1 - t)); g = 255; b = Math.round(255 * t);
  }
  return `rgb(${r},${g},${b})`;
}

const SocioEconomicStatsMap: React.FC = () => {
  const [neighbourhoods, setNeighbourhoods] = useState<Neighbourhood[]>([]);
  const [selectedStats, setSelectedStats] = useState<string[]>([STATISTICS[0].key]);
  const [statRange, setStatRange] = useState<StatRange>({ min: 0, max: 1 });
  const [loading, setLoading] = useState<boolean>(true);

  // Load and parse CSV data
  useEffect(() => {
    fetch('/SocioeconomicStats.csv')
      .then(res => res.text())
      .then(csvText => {
        Papa.parse<Neighbourhood>(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            const data: Neighbourhood[] = (results.data as any[]).map((row: any) => {
              // Parse geometry from WKT format
              let geometry = null;
              try {
                if (row.geometry && row.geometry.startsWith('MULTIPOLYGON')) {
                  const coords = row.geometry
                    .replace('MULTIPOLYGON (((', '')
                    .replace(')))', '')
                    .split('), (')
                    .map((poly: string) => [
                      poly.split(', ').map((pair: string) => {
                        const [lng, lat] = pair.split(' ').map(Number);
                        return [lng, lat];
                      })
                    ]);
                  geometry = {
                    type: 'MultiPolygon',
                    coordinates: coords,
                  };
                }
              } catch (e) {
                console.warn('Failed to parse geometry for:', row.AREA_NAME);
                geometry = null;
              }
              
              // Parse numeric statistics with robust error handling
              const parseStat = (field: string): number => {
                const val = row[field];
                if (val === null || val === undefined || val === '') return 0;
                const num = parseFloat(val.toString().trim());
                return isNaN(num) ? 0 : num;
              };
              
              return {
                HOOD_ID: row.HOOD_ID,
                AREA_NAME: row.AREA_NAME,
                geometry,
                growth_potential_score: parseStat('growth_potential_score'),
                safety_score: parseStat('safety_score'),
                school_score: parseStat('school_score'),
                business_job_score: parseStat('business_job_score'),
              };
            }).filter((n: Neighbourhood) => n.geometry); // Only include neighbourhoods with valid geometry
            
            setNeighbourhoods(data);
            setLoading(false);
          },
          error: (error: Error) => {
            console.error('Error parsing CSV:', error);
            setLoading(false);
          }
        });
      })
      .catch(error => {
        console.error('Error loading CSV:', error);
        setLoading(false);
      });
  }, []);

  // Calculate combined score for selected statistics
  const getCombinedScore = (neighbourhood: Neighbourhood): number => {
    if (selectedStats.length === 0) return 0;
    
    const values = selectedStats.map(stat => neighbourhood[stat as keyof Neighbourhood] as number);
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  };

  // Update stat range when selected statistics change
  useEffect(() => {
    if (neighbourhoods.length > 0) {
      const values = neighbourhoods.map(n => getCombinedScore(n));
      const min = Math.min(...values);
      const max = Math.max(...values);
      
      // Ensure we have a visible range even if all values are the same
      const range = max - min;
      if (range === 0) {
        setStatRange({ min: min - 1, max: max + 1 });
      } else {
        setStatRange({ min, max });
      }
    }
  }, [neighbourhoods, selectedStats]);

  // Generate GeoJSON for the map
  const geoJson: GeoJSON.FeatureCollection = {
    type: 'FeatureCollection',
    features: neighbourhoods.map(n => {
      const combinedScore = getCombinedScore(n);
      return {
        type: 'Feature' as const,
        properties: { 
          ...n, 
          combinedScore: combinedScore,
          selectedStats: selectedStats
        },
        geometry: n.geometry,
      };
    }),
  };

  // Style function for GeoJSON features
  const styleFeature = (feature: any) => {
    const value = feature.properties.combinedScore;
    
    return {
      fillColor: getColor(value, statRange.min, statRange.max),
      fillOpacity: 0.7,
      color: '#333',
      weight: 1,
    };
  };

  // Popup content for each neighbourhood
  const onEachFeature = (feature: any, layer: any) => {
    const props = feature.properties;
    
    let popupContent = `
      <div style="min-width: 200px;">
        <h3 style="margin: 0 0 10px 0; color: #333;">${props.AREA_NAME}</h3>
        <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
          <strong>Hood ID:</strong> ${props.HOOD_ID}
        </div>
    `;
    
    if (selectedStats.length > 0) {
      // Calculate the actual combined score for this neighbourhood using current selection
      const actualCombinedScore = getCombinedScore(props);
      
      popupContent += `
        <div style="margin-bottom: 15px;">
          <strong>Combined Score (${selectedStats.length} stat${selectedStats.length > 1 ? 's' : ''}):</strong> ${actualCombinedScore.toFixed(2)}
        </div>
        <div style="font-size: 12px; color: #666;">
      `;
      
      // Show selected stats with their values
      selectedStats.forEach(statKey => {
        const statInfo = STATISTICS.find(s => s.key === statKey);
        popupContent += `<div><strong>${statInfo?.name}:</strong> ${props[statKey].toFixed(2)}</div>`;
      });
      
      popupContent += `</div>`;
    } else {
      popupContent += `
        <div style="margin-bottom: 15px; color: #666;">
          <em>No statistics selected</em>
        </div>
      `;
    }
    
    popupContent += `</div>`;
    
    layer.bindPopup(popupContent);
  };

  // Handle statistic selection/deselection
  const handleStatToggle = (statKey: string) => {
    setSelectedStats(prev => {
      if (prev.includes(statKey)) {
        return prev.filter(s => s !== statKey);
      } else {
        return [...prev, statKey];
      }
    });
  };

  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading Toronto neighbourhood data...
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', width: '100%', position: 'relative' }}>
      {/* Control Panel */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        zIndex: 1000,
        background: 'white',
        padding: 20,
        borderRadius: 8,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        minWidth: 280,
        maxWidth: 320,
        maxHeight: '400px',
        overflowY: 'auto',
        overflowX: 'hidden'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>
          Toronto Neighbourhood Statistics
        </h3>
        
        <div style={{ marginBottom: 15 }}>
          <label style={{ display: 'block', marginBottom: 6, fontWeight: 'bold', color: '#555' }}>
            Select Statistics (Multiple):
          </label>
          {STATISTICS.map(stat => (
            <label key={stat.key} style={{ 
              display: 'block', 
              marginBottom: 6,
              cursor: 'pointer',
              padding: '6px 10px',
              borderRadius: 4,
              backgroundColor: selectedStats.includes(stat.key) ? '#f0f8ff' : 'transparent',
              border: selectedStats.includes(stat.key) ? '2px solid #007bff' : '2px solid transparent'
            }}>
              <input
                type="checkbox"
                checked={selectedStats.includes(stat.key)}
                onChange={() => handleStatToggle(stat.key)}
                style={{ marginRight: 8 }}
              />
              <span style={{ fontWeight: selectedStats.includes(stat.key) ? 'bold' : 'normal' }}>
                {stat.name}
              </span>
              <div style={{ 
                fontSize: '12px', 
                color: '#666', 
                marginLeft: 24,
                marginTop: 2
              }}>
                {stat.description}
              </div>
            </label>
          ))}
        </div>

        {/* Color Legend */}
        <div style={{ 
          padding: 10, 
          background: '#f8f9fa', 
          borderRadius: 6,
          border: '1px solid #e9ecef',
          marginBottom: 12
        }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: 6, color: '#495057' }}>
            Color Legend:
          </div>
          <div style={{ fontSize: '12px', color: '#6c757d' }}>
            <div style={{ marginBottom: '10px' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#333' }}>Color Legend:</h4>
              <div style={{ 
                width: '100%', 
                height: '20px', 
                background: 'linear-gradient(to right, #ff0000, #ffff00, #00ffff, #0000ff)',
                borderRadius: '4px',
                marginBottom: '5px'
              }}></div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                Red = Bad/Low | Blue = Good/High
              </div>
            </div>
          </div>
        </div>

        {/* Current Range Display */}
        <div style={{ 
          padding: 10, 
          background: '#f8f9fa', 
          borderRadius: 6,
          border: '1px solid #e9ecef'
        }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: 6, color: '#495057' }}>
            Current Range:
          </div>
          <div style={{ fontSize: '13px', color: '#6c757d' }}>
            <div>Min: {statRange.min.toFixed(2)}</div>
            <div>Max: {statRange.max.toFixed(2)}</div>
            <div style={{ marginTop: 4 }}>
              <strong>Neighbourhoods:</strong> {neighbourhoods.length}
            </div>
            {selectedStats.length > 0 && (
              <div style={{ marginTop: 4 }}>
                <strong>Selected:</strong> {selectedStats.length} stat{selectedStats.length > 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Map */}
      <MapContainer 
        center={[43.7, -79.4]} 
        zoom={11} 
        style={{ height: '100vh', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {neighbourhoods.length > 0 && (
          <GeoJSON 
            key={selectedStats.join(',')} // Force re-render when selection changes
            data={geoJson} 
            style={styleFeature} 
            onEachFeature={onEachFeature} 
          />
        )}
      </MapContainer>
    </div>
  );
};

export default SocioEconomicStatsMap;
