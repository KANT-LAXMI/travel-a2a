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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/recommend`, {
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
        {/* Hero Search Section */}
        <section className="hero-search-section">
          <div className="hero-search-background">
            <img 
              src="https://media.cntraveller.in/wp-content/uploads/2017/01/spiti-lead-image-1366x768.jpg" 
              alt="Discover places" 
            />
          </div>
          <div className="hero-search-content">
            <h1 className="hero-search-title">
              Discover Amazing Places<span className="title-dot">.</span>
            </h1>
            <p className="hero-search-subtitle">
              Explore hotels, attractions, and monuments powered by AI
            </p>

            <form onSubmit={handleSearch} className="hero-search-form">
              <div className="hero-search-input-group">
                <svg className="search-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
                <input
                  type="text"
                  value={searchPlace}
                  onChange={(e) => setSearchPlace(e.target.value)}
                  placeholder="Where do you want to explore? (e.g., Agra, Paris, Tokyo)"
                  className="hero-search-input"
                />
                <button type="submit" className="hero-search-btn" disabled={loading}>
                  {loading ? (
                    <span className="loading-spinner"></span>
                  ) : (
                    'Explore'
                  )}
                </button>
              </div>
            </form>
          </div>
        </section>

        {error && (
          <div className="error-container">
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {searchLocation && (
          <section className="results-section">
            <div className="results-header">
              <div className="results-title-section">
                <h2 className="results-title">
                  Places near <span className="highlight">{searchLocation.name}</span>
                </h2>
                <p className="results-count">
                  {filteredPlaces.length} {filteredPlaces.length === 1 ? 'place' : 'places'} found
                </p>
              </div>
            </div>

            <div className="category-filters">
              <button
                className={`filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('all')}
              >
                <span className="filter-icon">🌍</span>
                All ({places.length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'hotel' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('hotel')}
              >
                <span className="filter-icon">🏨</span>
                Hotels ({places.filter(p => p.type === 'hotel').length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'monument' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('monument')}
              >
                <span className="filter-icon">🏛️</span>
                Monuments ({places.filter(p => p.type === 'monument').length})
              </button>
              <button
                className={`filter-btn ${selectedCategory === 'attraction' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('attraction')}
              >
                <span className="filter-icon">🎯</span>
                Attractions ({places.filter(p => p.type === 'attraction').length})
              </button>
            </div>

            {filteredPlaces.length === 0 ? (
              <div className="no-results">
                <div className="no-results-icon">🔍</div>
                <h3>No {selectedCategory !== 'all' ? selectedCategory + 's' : 'places'} found</h3>
                <p>Try selecting a different category or search for another location</p>
              </div>
            ) : (
              <div className="places-grid">
                {filteredPlaces.map((place, index) => (
                  <div key={index} className="place-card">
                    <div className="place-image-wrapper">
                      <img
                        src={place.image}
                        alt={place.name}
                        className="place-image"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/400x300?text=No+Image'
                        }}
                      />
                      <div className="place-type-badge-wrapper">
                        <span className={`place-type-badge ${place.type}`}>
                          {place.type === 'hotel' && '🏨'}
                          {place.type === 'monument' && '🏛️'}
                          {place.type === 'attraction' && '🎯'}
                          {' '}
                          {place.type.charAt(0).toUpperCase() + place.type.slice(1)}
                        </span>
                      </div>
                    </div>
                    <div className="place-info">
                      <h3 className="place-name">{place.name}</h3>
                      <p className="place-coordinates">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        {place.lat.toFixed(4)}, {place.lon.toFixed(4)}
                      </p>
                      {place.extract && (
                        <p className="place-description">
                          {place.extract.length > 120
                            ? place.extract.substring(0, 120) + '...'
                            : place.extract}
                        </p>
                      )}
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lon}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-view-map"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
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
            <div className="empty-state-icon">🗺️</div>
            <h3>Start Your Journey</h3>
            <p>Enter a destination above to discover amazing places, hotels, and attractions</p>
            <div className="popular-destinations">
              <p className="popular-label">Popular destinations:</p>
              <div className="popular-chips">
                <button onClick={() => { setSearchPlace('Paris'); }} className="popular-chip">Paris</button>
                <button onClick={() => { setSearchPlace('Tokyo'); }} className="popular-chip">Tokyo</button>
                <button onClick={() => { setSearchPlace('New York'); }} className="popular-chip">New York</button>
                <button onClick={() => { setSearchPlace('Dubai'); }} className="popular-chip">Dubai</button>
                <button onClick={() => { setSearchPlace('London'); }} className="popular-chip">London</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Recommendations
