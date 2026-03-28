import React, { useEffect, useRef, useState } from 'react'
import './TravelMap.css'

const TravelMap = ({ locations }) => {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])
  const [selectedDay, setSelectedDay] = useState(null)

  useEffect(() => {
    if (!locations || locations.length === 0) return

    if (!window.L) {
      loadLeaflet()
    } else {
      initializeMap()
    }
  }, [locations])

  const loadLeaflet = () => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = () => initializeMap()
    document.head.appendChild(script)
  }

  const initializeMap = () => {
    if (!window.L || !locations || locations.length === 0 || !mapRef.current) return

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove()
    }

    const L = window.L

    // Calculate center
    const centerLat = locations.reduce((sum, loc) => sum + loc.latitude, 0) / locations.length
    const centerLng = locations.reduce((sum, loc) => sum + loc.longitude, 0) / locations.length

    const map = L.map(mapRef.current).setView([centerLat, centerLng], 13)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19
    }).addTo(map)

    const dayColors = {
      1: '#667eea',
      2: '#764ba2',
      3: '#f093fb',
      4: '#4facfe',
      5: '#43e97b'
    }

    const markers = []
    const bounds = []

    locations.forEach((location, index) => {
      const color = dayColors[location.day] || '#667eea'
      
      const iconHtml = `
        <div style="
          background-color: ${color};
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 3px solid white;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 14px;
          box-shadow: 0 3px 10px rgba(0,0,0,0.3);
          cursor: pointer;
        ">
          ${index + 1}
        </div>
      `

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-marker',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      })

      const marker = L.marker([location.latitude, location.longitude], {
        icon: customIcon
      }).addTo(map)

      // Create custom popup content with image on left, details on right
      const imageUrl = location.image || 'https://img.freepik.com/premium-vector/no-photo-available-vector-icon-default-image-symbol-picture-coming-soon-web-site-mobile-app_87543-14040.jpg'
      
      const popupContent = `
        <div class="custom-popup-content">
          <div class="custom-popup-image">
            <img src="${imageUrl}" alt="${location.name}" class="custom-popup-img" />
          </div>
          <div class="custom-popup-details">
            <h3 class="custom-popup-title">${location.name}</h3>
            <p class="custom-popup-time">⏰ ${location.time}</p>
            <span class="custom-popup-day-badge" style="background-color: ${color};">
              Day ${location.day}
            </span>
            ${location.description ? `
              <p class="custom-popup-description">${location.description}</p>
            ` : ''}
            ${location.duration ? `
              <p class="custom-popup-duration">⏱️ Duration: ${location.duration} minutes</p>
            ` : ''}
          </div>
        </div>
      `
      
      marker.bindPopup(popupContent, { 
        maxWidth: 500,
        minWidth: 500,
        className: 'custom-leaflet-popup'
      })

      markers.push(marker)
      bounds.push([location.latitude, location.longitude])
    })

    markersRef.current = markers
    mapInstanceRef.current = map

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] })
    }

    // Draw connecting lines by day
    const locationsByDay = {}
    locations.forEach(loc => {
      if (!locationsByDay[loc.day]) {
        locationsByDay[loc.day] = []
      }
      locationsByDay[loc.day].push([loc.latitude, loc.longitude])
    })

    Object.entries(locationsByDay).forEach(([day, coords]) => {
      if (coords.length > 1) {
        const color = dayColors[parseInt(day)] || '#667eea'
        L.polyline(coords, {
          color: color,
          weight: 3,
          opacity: 0.6,
          dashArray: '10, 10'
        }).addTo(map)
      }
    })
  }

  const handlePlaceClick = (location) => {
    // Find the location index
    const index = locations.findIndex(loc => 
      loc.name === location.name && 
      loc.day === location.day && 
      loc.time === location.time
    )

    if (index === -1 || !mapInstanceRef.current || !markersRef.current[index]) return

    // Pan map to location
    mapInstanceRef.current.setView(
      [location.latitude, location.longitude],
      15,
      { animate: true, duration: 1 }
    )

    // Open the marker's popup after animation
    setTimeout(() => {
      markersRef.current[index].openPopup()
    }, 500)
  }

  const handleDayClick = (day) => {
    setSelectedDay(selectedDay === day ? null : day)
  }

  const dayColors = {
    1: '#667eea',
    2: '#764ba2',
    3: '#f093fb',
    4: '#4facfe',
    5: '#43e97b'
  }

  // Group locations by day
  const locationsByDay = {}
  locations.forEach(loc => {
    if (!locationsByDay[loc.day]) {
      locationsByDay[loc.day] = []
    }
    locationsByDay[loc.day].push(loc)
  })

  const totalDays = Object.keys(locationsByDay).length

  if (!locations || locations.length === 0) {
    return (
      <div className="travel-map-placeholder">
        <span className="map-icon">🗺️</span>
        <p>Map will be displayed here</p>
      </div>
    )
  }

  return (
    <div className="travel-map-container">
      {/* Legend */}
      <div className="travel-legend">
        <span className="legend-title">Days:</span>
        {Object.keys(locationsByDay).sort().map(day => (
          <div key={day} className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: dayColors[parseInt(day)] }}
            ></span>
            <span>Day {day}</span>
          </div>
        ))}
      </div>

      {/* Content: Map + Sidebar */}
      <div className="travel-content">
        {/* Map */}
        <div ref={mapRef} className="travel-map"></div>

        {/* Sidebar - Days and Places */}
        <div className="travel-sidebar">
          <div className="sidebar-header">
            <span>Itinerary</span>
            <span className="place-counter">{totalDays} Days</span>
          </div>

          <div className="days-list">
            {Object.keys(locationsByDay).sort((a, b) => parseInt(a) - parseInt(b)).map(day => {
              const dayNumber = parseInt(day)
              const dayLocations = locationsByDay[day]
              const isActive = selectedDay === dayNumber

              return (
                <div key={day} className="day-section">
                  <button
                    className={`day-button ${isActive ? 'active' : ''}`}
                    style={{ 
                      borderLeftColor: dayColors[dayNumber],
                      backgroundColor: isActive ? dayColors[dayNumber] : 'white',
                      color: isActive ? 'white' : '#333'
                    }}
                    onClick={() => handleDayClick(dayNumber)}
                  >
                    <span className="day-label">DAY {day}</span>
                    <span className="day-count">{dayLocations.length} places</span>
                  </button>

                  {isActive && (
                    <div className="places-timeline">
                      {dayLocations.map((location, index) => (
                        <div
                          key={index}
                          className="timeline-item"
                          onClick={() => handlePlaceClick(location)}
                        >
                          <div className="timeline-time">{location.time}</div>
                          <div className="timeline-content">
                            <div className="timeline-place">{location.name}</div>
                            {location.description && (
                              <div className="timeline-description">{location.description}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TravelMap
