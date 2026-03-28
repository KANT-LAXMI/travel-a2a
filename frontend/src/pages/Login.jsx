import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
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

    const result = await login(formData.email, formData.password)

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
            <Link to="/signup" className="nav-link">Join</Link>
          </nav>

          <div className="auth-form-wrapper">
            <p className="form-subtitle">WELCOME BACK</p>
            <h1 className="form-title">
              Log into your account<span className="title-dot">.</span>
            </h1>
            <p className="form-helper">
              Don't have an account? <Link to="/signup" className="form-link">Sign Up</Link>
            </p>

            <form onSubmit={handleSubmit} className="auth-form">
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
                    placeholder="your.email@anywhere.co"
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
                  />
                  <span className="input-icon">👁️</span>
                </div>
                <div className="forgot-password-link">
                  <Link to="/forgot-password" className="form-link">Forgot Password?</Link>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="form-actions">
                <Link to="/signup" className="btn-secondary">
                  Create Account
                </Link>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Logging in...' : 'Log in'}
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

export default Login
