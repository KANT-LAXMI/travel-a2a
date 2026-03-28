import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import './ForgotPassword.css'

const ForgotPassword = () => {
  const [step, setStep] = useState(1) // 1: Email, 2: OTP, 3: New Password
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  // Step 1: Request OTP
  const handleRequestOTP = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/forgot-password`, {
        email
      })
      
      setSuccess(response.data.message)
      setStep(2) // Move to OTP verification step
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send OTP')
    }

    setLoading(false)
  }

  // Step 2: Verify OTP (optional, can skip to step 3)
  const handleVerifyOTP = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/verify-otp`, {
        email,
        otp
      })
      
      if (response.data.valid) {
        setSuccess('OTP verified! Enter your new password.')
        setStep(3) // Move to password reset step
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid OTP')
    }

    setLoading(false)
  }

  // Step 3: Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password length
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/reset-password`, {
        email,
        otp,
        newPassword
      })
      
      setSuccess(response.data.message)
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to reset password')
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
            <Link to="/login" className="nav-link">Login</Link>
          </nav>

          <div className="auth-form-wrapper">
            {/* Step Indicator */}
            <div className="step-indicator">
              <div className={`step ${step >= 1 ? 'active' : ''}`}>
                <div className="step-number">1</div>
                <div className="step-label">Email</div>
              </div>
              <div className="step-line"></div>
              <div className={`step ${step >= 2 ? 'active' : ''}`}>
                <div className="step-number">2</div>
                <div className="step-label">OTP</div>
              </div>
              <div className="step-line"></div>
              <div className={`step ${step >= 3 ? 'active' : ''}`}>
                <div className="step-number">3</div>
                <div className="step-label">Reset</div>
              </div>
            </div>

            <p className="form-subtitle">PASSWORD RECOVERY</p>
            <h1 className="form-title">
              {step === 1 && 'Reset your password'}
              {step === 2 && 'Enter OTP code'}
              {step === 3 && 'Create new password'}
              <span className="title-dot">.</span>
            </h1>

            {/* Step 1: Email Input */}
            {step === 1 && (
              <>
                <p className="form-helper">
                  Remember your password? <Link to="/login" className="form-link">Log In</Link>
                </p>

                <form onSubmit={handleRequestOTP} className="auth-form">
                  <div className="form-group">
                    <label htmlFor="email">Email Address</label>
                    <div className="input-wrapper">
                      <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="your.email@anywhere.co"
                      />
                      <span className="input-icon">✉️</span>
                    </div>
                    <p className="input-hint">We'll send a 6-digit OTP to this email</p>
                  </div>

                  {error && <div className="error-message">{error}</div>}
                  {success && <div className="success-message">{success}</div>}

                  <div className="form-actions">
                    <Link to="/login" className="btn-secondary">
                      Back to Login
                    </Link>
                    <button type="submit" className="btn-primary" disabled={loading}>
                      {loading ? 'Sending...' : 'Send OTP'}
                    </button>
                  </div>
                </form>
              </>
            )}

            {/* Step 2: OTP Input */}
            {step === 2 && (
              <>
                <p className="form-helper">
                  OTP sent to <strong>{email}</strong>
                </p>

                <form onSubmit={handleVerifyOTP} className="auth-form">
                  <div className="form-group">
                    <label htmlFor="otp">Enter 6-Digit OTP</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="otp"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        required
                        placeholder="123456"
                        maxLength="6"
                        className="otp-input"
                      />
                      <span className="input-icon">🔐</span>
                    </div>
                    <p className="input-hint">Check your email for the OTP code (valid for 10 minutes)</p>
                  </div>

                  {error && <div className="error-message">{error}</div>}
                  {success && <div className="success-message">{success}</div>}

                  <div className="form-actions">
                    <button 
                      type="button" 
                      className="btn-secondary"
                      onClick={() => setStep(1)}
                    >
                      Change Email
                    </button>
                    <button type="submit" className="btn-primary" disabled={loading}>
                      {loading ? 'Verifying...' : 'Verify OTP'}
                    </button>
                  </div>

                  <div className="resend-section">
                    <p>Didn't receive OTP?</p>
                    <button 
                      type="button" 
                      className="btn-link"
                      onClick={handleRequestOTP}
                      disabled={loading}
                    >
                      Resend OTP
                    </button>
                  </div>
                </form>
              </>
            )}

            {/* Step 3: New Password Input */}
            {step === 3 && (
              <>
                <p className="form-helper">
                  Create a strong password for your account
                </p>

                <form onSubmit={handleResetPassword} className="auth-form">
                  <div className="form-group">
                    <label htmlFor="newPassword">New Password</label>
                    <div className="input-wrapper">
                      <input
                        type="password"
                        id="newPassword"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        placeholder="••••••••"
                        minLength="6"
                      />
                      <span className="input-icon">🔒</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <div className="input-wrapper">
                      <input
                        type="password"
                        id="confirmPassword"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        placeholder="••••••••"
                        minLength="6"
                      />
                      <span className="input-icon">🔒</span>
                    </div>
                  </div>

                  {error && <div className="error-message">{error}</div>}
                  {success && <div className="success-message">{success}</div>}

                  <div className="form-actions">
                    <button 
                      type="button" 
                      className="btn-secondary"
                      onClick={() => setStep(2)}
                    >
                      Back
                    </button>
                    <button type="submit" className="btn-primary" disabled={loading}>
                      {loading ? 'Resetting...' : 'Reset Password'}
                    </button>
                  </div>
                </form>
              </>
            )}
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

export default ForgotPassword
