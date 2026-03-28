import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./About.css";

const About = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);

  // Slideshow images
  const slideshowImages = [
    "https://img.freepik.com/premium-photo/travel-traveling-symbolic-picture-vacation-background-15_1032298-2376.jpg?semt=ais_user_personalization&w=740&q=80",
    "https://imageio.forbes.com/specials-images/imageserve//62bdd4a21a6dc599d18bca9b/0x0.jpg?format=jpg&height=900&width=1600&fit=bounds",
    "https://tse3.mm.bing.net/th/id/OIP.ALx8ofNNeqMIWx1OqEE1jwHaE8?rs=1&pid=ImgDetMain&o=7&rm=3",
    "https://cdn.getyourguide.com/img/tour/5e4576a871130.jpeg/97.jpg",
    "https://thecsrjournal.in/wp-content/uploads/2025/07/pune-travel.webp",
    "https://rameswaramtravelguide.com/wp-content/uploads/2018/08/Satelite-view-Adams-bridge-post.jpg",
  ];

  // Auto-advance slideshow every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slideshowImages.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [slideshowImages.length]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  return (
    <div className="about-page">
      <header className="dashboard-header">
        <div className="logo">
          <div className="logo-icon"></div>
          <span className="logo-text">Anywhere app.</span>
        </div>

        <nav className="dashboard-nav">
          <a href="/dashboard">Home</a>
          <a href="#destinations">Destinations</a>
          <a href="#trips">My Trips</a>
          <a href="/recommendations">Recommendations</a>
          <a href="/about" className="active">
            About
          </a>
        </nav>

        <div className="user-menu">
          <div className="user-info">
            <span className="user-name">
              {user?.first_name} {user?.last_name}
            </span>
            <span className="user-email">{user?.email}</span>
          </div>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      <main className="about-main">
        {/* Hero Section */}
        <section className="about-hero">
          <div className="hero-background-image">
            <img
              src="https://img.freepik.com/premium-photo/person-sits-summit-mountain-taking-breathtaking-vistas-surrounding-valley-hiker-enjoying-stunning-panoramic-view-ai-generated_538213-20213.jpg"
              alt="Travel background"
            />
          </div>
          <div className="about-hero-content">
            <h1 className="about-title">
              Your AI-Powered Travel Companion
              <span className="title-dot">.</span>
            </h1>
            <p className="about-subtitle">
              Transforming the way you plan, explore, and experience travel with
              cutting-edge artificial intelligence
            </p>
          </div>
        </section>

        {/* Mission Section */}
        <section className="mission-section">
          <div className="mission-content">
            <div className="mission-text">
              <h2 className="section-heading">Our Mission</h2>
              <p className="mission-description">
                At Anywhere App, we believe travel planning should be
                effortless, personalized, and exciting. Our mission is to
                empower travelers with AI-driven insights that transform complex
                itineraries into seamless adventures, making every journey
                memorable and stress-free.
              </p>
            </div>
            <div className="mission-image">
              <div className="slideshow-container">
                {slideshowImages.map((image, index) => (
                  <div
                    key={index}
                    className={`slide ${index === currentSlide ? "active" : ""}`}
                  >
                    <img src={image} alt={`Travel ${index + 1}`} />
                  </div>
                ))}

                {/* Dots/Indicators */}
                <div className="slideshow-dots">
                  {slideshowImages.map((_, index) => (
                    <span
                      key={index}
                      className={`dot ${index === currentSlide ? "active" : ""}`}
                      onClick={() => goToSlide(index)}
                    ></span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* AI Features Section */}
        <section className="ai-features-section">
          <h2 className="section-heading centered">Powered by Advanced AI</h2>
          <p className="section-subheading">
            Our intelligent system combines multiple AI technologies to deliver
            the best travel experience
          </p>

          <div className="ai-features-grid">
            <div className="ai-feature-card">
              <div className="ai-icon">🤖</div>
              <h3>Multi-Agent Architecture</h3>
              <p>
                Specialized AI agents work together - Budget Agent manages
                finances, Places Agent discovers attractions, Map Agent
                visualizes routes, and RAG Agent provides contextual travel
                knowledge from extensive documentation.
              </p>
            </div>

            <div className="ai-feature-card">
              <div className="ai-icon">🧠</div>
              <h3>Semantic Kernel Integration</h3>
              <p>
                Powered by Microsoft's Semantic Kernel framework, our
                orchestrator intelligently coordinates multiple AI agents,
                ensuring seamless communication and optimal task execution for
                complex travel planning scenarios.
              </p>
            </div>

            <div className="ai-feature-card">
              <div className="ai-icon">💬</div>
              <h3>Conversational Memory</h3>
              <p>
                Our system remembers your preferences, past conversations, and
                travel history. Each interaction builds context, allowing for
                more personalized recommendations and natural, flowing
                conversations.
              </p>
            </div>

            <div className="ai-feature-card">
              <div className="ai-icon">📚</div>
              <h3>RAG-Powered Knowledge</h3>
              <p>
                Retrieval-Augmented Generation (RAG) technology processes travel
                documents, guides, and PDFs using FAISS vector search, providing
                accurate, context-aware answers to your travel questions.
              </p>
            </div>

            <div className="ai-feature-card">
              <div className="ai-icon">🗺️</div>
              <h3>Smart Recommendations</h3>
              <p>
                Combining Wikipedia Geosearch and OpenStreetMap Overpass APIs
                with AI filtering, we discover hidden gems, popular attractions,
                and perfect accommodations tailored to your preferences.
              </p>
            </div>

            <div className="ai-feature-card">
              <div className="ai-icon">💰</div>
              <h3>Intelligent Budgeting</h3>
              <p>
                Our Budget Agent uses AI to analyze costs, optimize spending,
                and provide detailed breakdowns for accommodation, food,
                transport, and activities - ensuring you stay within budget.
              </p>
            </div>
          </div>
        </section>

        {/* Technology Stack Section */}
        {/* <section className="tech-stack-section">
          <h2 className="section-heading centered">Built with Modern Technology</h2>
          
          <div className="tech-categories">
            <div className="tech-category">
              <h3>AI & Machine Learning</h3>
              <div className="tech-tags">
                <span className="tech-tag">Azure OpenAI</span>
                <span className="tech-tag">Semantic Kernel</span>
                <span className="tech-tag">LangChain</span>
                <span className="tech-tag">FAISS Vector DB</span>
                <span className="tech-tag">RAG Architecture</span>
              </div>
            </div>

            <div className="tech-category">
              <h3>Backend</h3>
              <div className="tech-tags">
                <span className="tech-tag">Python</span>
                <span className="tech-tag">Flask</span>
                <span className="tech-tag">SQLite</span>
                <span className="tech-tag">JWT Authentication</span>
                <span className="tech-tag">Bcrypt</span>
              </div>
            </div>

            <div className="tech-category">
              <h3>Frontend</h3>
              <div className="tech-tags">
                <span className="tech-tag">React</span>
                <span className="tech-tag">Vite</span>
                <span className="tech-tag">React Router</span>
                <span className="tech-tag">Context API</span>
              </div>
            </div>

            <div className="tech-category">
              <h3>APIs & Services</h3>
              <div className="tech-tags">
                <span className="tech-tag">Wikipedia API</span>
                <span className="tech-tag">OpenStreetMap</span>
                <span className="tech-tag">Overpass API</span>
                <span className="tech-tag">Folium Maps</span>
              </div>
            </div>
          </div>
        </section> */}

        {/* How It Works Section */}
        <section className="how-it-works-section">
          <h2 className="section-heading centered">How It Works</h2>

          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Tell Us Your Plans</h3>
                <p>
                  Simply describe your travel goals - destination, duration,
                  budget, and preferences
                </p>
              </div>
            </div>

            <div className="workflow-arrow">→</div>

            <div className="workflow-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>AI Orchestration</h3>
                <p>
                  Our Semantic Kernel orchestrator routes your request to
                  specialized AI agents
                </p>
              </div>
            </div>

            <div className="workflow-arrow">→</div>

            <div className="workflow-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Intelligent Processing</h3>
                <p>
                  Agents collaborate - Budget calculates costs, Places finds
                  attractions, Map visualizes routes
                </p>
              </div>
            </div>

            <div className="workflow-arrow">→</div>

            <div className="workflow-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Personalized Results</h3>
                <p>
                  Receive a complete itinerary with budget breakdown, day-by-day
                  plans, and interactive maps
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">5+</div>
              <div className="stat-label">AI Agents</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">100K+</div>
              <div className="stat-label">Places Database</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">24/7</div>
              <div className="stat-label">AI Availability</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">∞</div>
              <div className="stat-label">Possibilities</div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <h2>Ready to Plan Your Next Adventure?</h2>
          <p>
            Let our AI-powered platform create the perfect itinerary for you
          </p>
          <button onClick={() => navigate("/dashboard")} className="btn-cta">
            Start Planning Now
          </button>
        </section>
      </main>

      <footer className="about-footer">
        <p>&copy; 2026 Anywhere App. Powered by AI. Built with ❤️</p>
      </footer>
    </div>
  );
};

export default About;
