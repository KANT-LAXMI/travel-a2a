import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Recommendations.css'

const Recommendations = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [searchPlace, setSearchPlace] = useState('')
  const [loading, setLoading] = useState(false)
  const [places, setPlaces] = useState([])
  const [filteredPlaces, setFilteredPlaces] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchLocation, setSearchLocation] = useState(null)
  const [error, setError] = useState('')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchPlace.trim()) return

    setLoading(true)
    setError('')
    setPlaces([])
    setFilteredPlaces([])
    setSelectedCategory('all')

    try {
      const response = await fetch('http://localhost:5000/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ place: searchPlace }),
      })

      const data = await response.json()

      if (data.success) {
        setPlaces(data.results)
        setFilteredPlaces(data.results)
        setSearchLocation(data.search_location)
      } else {
        setError(data.message || 'No recommendations found')
      }
    } catch (err) {
      setError('Failed to fetch recommendations. Please try again.')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryFilter = (category) => {
    setSelectedCategory(category)
    
    if (category === 'all') {
      setFilteredPlaces(places)
    } else {
      const filtered = places.filter(place => place.type === category)
      setFilteredPlaces(filtered)
    }
  }

  return (
    <div className="recommendations-page">
      <header className="dashboard-header">
        <div className="logo">
          <div className="logo-icon"></div>
          <span className="logo-text">Anywhere app.</span>
        </div>

        <nav className="dashboard-nav">
          <a href="/dashboard">Home</a>
          <a href="#destinations">Destinations</a>
          <a href="#trips">My Trips</a>
          <a href="/recommendations" className="active">Recommendations</a>
          <a href="/about">About</a>
        </nav>

        <div className="user-menu">
          <div className="user-info">
            <span className="user-name">{user?.first_name} {user?.last_name}</span>
            <span className="user-email">{user?.email}</span>
          </div>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      <main className="recommendations-main">
        <section className="search-section">
          <h1 className="page-title">Discover Places</h1>
          <p className="page-subtitle">Find hotels, attractions, and monuments near any location</p>

          <form onSubmit={handleSearch} className="search-form">
            <div className="search-input-group">
              <input
                type="text"
                value={searchPlace}
                onChange={(e) => setSearchPlace(e.target.value)}
                placeholder="Enter a place name (e.g., Agra, Paris, Tokyo)"
                className="search-input"
              />
              <button type="submit" className="btn-search" disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>
        </section>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {searchLocation && (
          <section className="results-section">
            <div className="results-header">
              <h2 className="results-title">
                Places near {searchLocation.name}
              </h2>
              <p className="results-count">
                {filteredPlaces.length} {filteredPlaces.length === 1 ? 'place' : 'places'} found
              </p>
            </div>

            <div className="category-filters">
              <button
                className={`filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('all')}
              >
                All ({places.length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'hotel' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('hotel')}
              >
                🏨 Hotels ({places.filter(p => p.type === 'hotel').length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'monument' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('monument')}
              >
                🏛️ Monuments ({places.filter(p => p.type === 'monument').length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'attraction' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('attraction')}
              >
                🎯 Attractions ({places.filter(p => p.type === 'attraction').length})
              </button>
            </div>

            {filteredPlaces.length === 0 ? (
              <div className="no-results">
                <span className="no-results-icon">🔍</span>
                <p>No {selectedCategory !== 'all' ? selectedCategory + 's' : 'places'} found</p>
              </div>
            ) : (
              <div className="places-grid">
                {filteredPlaces.map((place, index) => (
                  <div key={index} className="place-card">
                    <div className="place-image-container">
                      <img
                        src={place.image}
                        alt={place.name}
                        className="place-image"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/400x300?text=No+Image'
                        }}
                      />
                      <span className={`place-type-badge ${place.type}`}>
                        {place.type === 'hotel' && '🏨'}
                        {place.type === 'monument' && '🏛️'}
                        {place.type === 'attraction' && '🎯'}
                        {' '}
                        {place.type.charAt(0).toUpperCase() + place.type.slice(1)}
                      </span>
                    </div>
                    <div className="place-content">
                      <h3 className="place-name">{place.name}</h3>
                      <p className="place-coordinates">
                        📍 {place.lat.toFixed(4)}, {place.lon.toFixed(4)}
                      </p>
                      {place.extract && (
                        <p className="place-description">
                          {place.extract.length > 150
                            ? place.extract.substring(0, 150) + '...'
                            : place.extract}
                        </p>
                      )}
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lon}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-view-map"
                      >
                        View on Map
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {!loading && !error && places.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🗺️</div>
            <h3>Start Exploring</h3>
            <p>Enter a place name above to discover amazing hotels, attractions, and monuments nearby</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default Recommendations
