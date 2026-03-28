import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Signup.css'

const Signup = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await signup(
      formData.firstName,
      formData.lastName,
      formData.email,
      formData.password
    )

    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.message)
    }

    setLoading(false)
  }

  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-content">
          <div className="logo">
            <div className="logo-icon"></div>
            <span className="logo-text">Anywhere app.</span>
          </div>

          <nav className="auth-nav">
            <Link to="/dashboard" className="nav-link">Home</Link>
            <Link to="/login" className="nav-link">Join</Link>
          </nav>

          <div className="auth-form-wrapper">
            <p className="form-subtitle">START FOR FREE</p>
            <h1 className="form-title">
              Create new account<span className="title-dot">.</span>
            </h1>
            <p className="form-helper">
              Already A Member? <Link to="/login" className="form-link">Log In</Link>
            </p>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="firstName">First name</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      id="firstName"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      required
                      placeholder="Michel"
                    />
                    <span className="input-icon">👤</span>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="lastName">Last name</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      id="lastName"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      required
                      placeholder="Maslak"
                    />
                    <span className="input-icon">👤</span>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <div className="input-wrapper">
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    placeholder="michel.maslak@anywhere.co"
                  />
                  <span className="input-icon">✉️</span>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    placeholder="••••••••"
                    minLength="6"
                  />
                  <span className="input-icon">👁️</span>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="form-actions">
                <button type="button" className="btn-secondary">
                  Change method
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Creating account...' : 'Create account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="hero-image"></div>
        <div className="hero-pattern"></div>
      </div>
    </div>
  )
}

export default Signup
