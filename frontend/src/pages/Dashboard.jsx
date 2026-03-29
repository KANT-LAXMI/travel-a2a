import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import TravelMap from "../components/TravelMap";
import DestinationCard from "../components/DestinationCard";
import { generateTripPDF } from "../utils/pdfGenerator";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [tripData, setTripData] = useState(null);
  const [wikipediaData, setWikipediaData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedDay, setSelectedDay] = useState(null);
  const [generatingPDF, setGeneratingPDF] = useState(false);

  const handleGeneratePDF = async () => {
    if (!tripData) return;
    
    setGeneratingPDF(true);
    try {
      const result = await generateTripPDF(tripData);
      if (result.success) {
        alert(`PDF generated successfully: ${result.filename}`);
      } else {
        alert(`Failed to generate PDF: ${result.error}`);
      }
    } catch (error) {
      console.error('PDF generation error:', error);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setGeneratingPDF(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setTripData(null);
    setWikipediaData(null);
    setSelectedDay(null);

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/plan-trip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ query: query }),
      });

      const data = await res.json();
      console.log("API Response:", data);

      if (data.success) {
        // New structured response format
        const parsed = {
          budget: [],
          itinerary: [],
          locations: [],
          totalBudget: 0,
        };

        // Parse budget - FIX: values are coming as decimals (0.6 instead of 6000)
        if (data.budget) {
          const budget = data.budget;
          console.log("Raw budget from API:", budget);
          
          // Check if values are too small (likely divided by 10000)
          const needsMultiplication = budget.total && budget.total < 100;
          const multiplier = needsMultiplication ? 10000 : 1;
          
          console.log(`Budget multiplier: ${multiplier} (needsMultiplication: ${needsMultiplication})`);
          
          parsed.budget = [
            { category: "Transport", amount: (budget.transport || 0) * multiplier },
            { category: "Accommodation", amount: (budget.accommodation || 0) * multiplier },
            { category: "Food", amount: (budget.food || 0) * multiplier },
            { category: "Activities", amount: (budget.activities || 0) * multiplier },
            { category: "Miscellaneous", amount: (budget.miscellaneous || 0) * multiplier },
          ].filter((item) => item.amount > 0);
          parsed.totalBudget = (budget.total || 0) * multiplier;
          
          console.log("Corrected budget:", parsed.budget);
          console.log("Corrected total:", parsed.totalBudget);
        }

        // Parse itinerary
        if (data.itinerary && data.itinerary.days) {
          data.itinerary.days.forEach((day) => {
            const dayActivities = day.activities.map((activity) => ({
              time: activity.time || "",
              place: activity.location?.name || activity.title || "",
              description: activity.description || "",
            }));
            parsed.itinerary.push({
              day: `Day ${day.day}`,
              activities: dayActivities,
            });
          });
        }

        // Parse map locations
        if (data.map && data.map.locations) {
          parsed.locations = data.map.locations.filter(
            (loc) => loc.latitude && loc.longitude
          );
        }

        console.log("Parsed data:", parsed);
        console.log("Budget array:", parsed.budget);
        console.log("Total budget:", parsed.totalBudget);
        console.log("Locations:", parsed.locations);
        console.log("Itinerary:", parsed.itinerary);
        console.log("PDF URL:", data.pdf_url);
        
        // Add PDF URL to parsed data
        if (data.pdf_url) {
          parsed.pdf_url = data.pdf_url;
        }
        
        setTripData(parsed);
        console.log("tripData state set!");
        
        // Set Wikipedia data if available
        if (data.wikipedia) {
          console.log("Wikipedia data received:", data.wikipedia);
          setWikipediaData(data.wikipedia);
        }
      } else {
        alert(`Error: ${data.message || "Failed to plan trip"}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert(
        "Error connecting to travel planner. Make sure all agents are running.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDayClick = (day) => {
    setSelectedDay(selectedDay === day ? null : day);
  };

  const handlePlaceClick = (place, dayNumber) => {
    if (!tripData?.locations?.length) return;

    // Find location by name and day
    const locationIndex = tripData.locations.findIndex(
      (loc) =>
        loc.name.toLowerCase().includes(place.toLowerCase()) &&
        loc.day === dayNumber,
    );

    if (locationIndex !== -1 && window.focusMapLocation) {
      window.focusMapLocation(locationIndex);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="logo">
          <div className="logo-icon"></div>
          <span className="logo-text">Anywhere app.</span>
        </div>

        <nav className="dashboard-nav">
          <a href="/dashboard">Home</a>
          <a href="/my-trips">My Trips</a>
          <a href="/recommendations">Recommendations</a>
          <a href="/about">About</a>
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

      <main className="dashboard-main">
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">
              Plan Your Perfect Trip<span className="title-dot">.</span>
            </h1>
            <p className="hero-subtitle">
              AI-powered travel planning with budget, itinerary, and maps
            </p>

            <form onSubmit={handleSubmit} className="trip-form">
              <div className="input-group">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., Plan a 2-day trip to Varanasi"
                  className="trip-input"
                />
                <button type="submit" className="btn-plan" disabled={loading}>
                  {loading ? "Planning..." : "Plan Trip"}
                </button>
              </div>
            </form>
          </div>

          <div className="hero-image-container">
            <img
              src="https://www.tripsavvy.com/thmb/upPBRJhuW8T9WjIG63ERp-_sJGw=/2190x1369/filters:fill(auto,1)/GettyImages-1075879774-714c3b3b727d4d8c8dc9f66a12ea7d03.jpg"
              alt="Travel destination"
              className="hero-img"
            />
          </div>
        </section>

        {/* Loading Spinner */}
        {loading && (
          <div className="loading-section">
            <div className="spinner"></div>
            <p>Planning your perfect trip...</p>
          </div>
        )}

        {/* Trip Results */}
        {tripData && !loading && (
          <section className="trip-results">
            {/* PDF Download Button */}
            <div className="pdf-download-section">
              <button 
                onClick={handleGeneratePDF}
                disabled={generatingPDF}
                className="btn-download-pdf"
              >
                {generatingPDF ? '⏳ Generating PDF...' : '📄 Download Trip Plan PDF'}
              </button>
            </div>

            {/* Wikipedia Destination Card */}
            {wikipediaData && <DestinationCard wikipediaData={wikipediaData} />}

            {/* Destination Hero Image Section */}
            {wikipediaData && (wikipediaData.image || wikipediaData.thumbnail) && (
              <div className="destination-hero">
                <div className="hero-image-container">
                  <img 
                    src={wikipediaData.image || wikipediaData.thumbnail} 
                    alt={wikipediaData.title || "Destination"} 
                    className="hero-image"
                  />
                  <div className="hero-overlay">
                    <h1 className="hero-title">{wikipediaData.title || "Your Destination"}</h1>
                  </div>
                </div>
              </div>
            )}

            {/* Budget Section */}
            {tripData.budget && tripData.budget.length > 0 && (
              <div className="budget-section">
                <h2 className="section-title">Budget Breakdown</h2>
                <div className="budget-container">
                  <div className="budget-table-wrapper">
                    <table className="budget-table">
                      <thead>
                        <tr>
                          <th>Category</th>
                          <th>Cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tripData.budget.map((item, index) => (
                          <tr key={index}>
                            <td>{item.category}</td>
                            <td>₹{item.amount.toLocaleString()}</td>
                          </tr>
                        ))}
                        <tr className="total-row">
                          <td>
                            <strong>Total</strong>
                          </td>
                          <td>
                            <strong>
                              ₹{tripData.totalBudget.toLocaleString()}
                            </strong>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="budget-chart">
                    <BudgetPieChart data={tripData.budget} />
                  </div>
                </div>
              </div>
            )}

            {/* Map and Itinerary Section */}
            {tripData.locations && tripData.locations.length > 0 && (
              <div className="map-section">
                <TravelMap locations={tripData.locations} />
              </div>
            )}

            {/* Itinerary Section - Only show if no locations for map */}
            {tripData.itinerary &&
              tripData.itinerary.length > 0 &&
              (!tripData.locations || tripData.locations.length === 0) && (
                <div className="map-itinerary-section">
                  <h2 className="section-title">Your Itinerary</h2>
                  <div className="itinerary-container">
                    <div className="days-list">
                      {tripData.itinerary.map((dayData, index) => {
                        const dayNumber = index + 1;
                        return (
                          <div key={index} className="day-item">
                            <button
                              className={`day-button ${selectedDay === dayData.day ? "active" : ""}`}
                              onClick={() => handleDayClick(dayData.day)}
                            >
                              {dayData.day}
                            </button>

                            {selectedDay === dayData.day && (
                              <div className="day-activities">
                                {dayData.activities.map(
                                  (activity, actIndex) => (
                                    <div
                                      key={actIndex}
                                      className="activity-item"
                                    >
                                      {activity.time && (
                                        <span className="activity-time">
                                          {activity.time}
                                        </span>
                                      )}
                                      <button
                                        className="activity-place"
                                        onClick={() =>
                                          handlePlaceClick(
                                            activity.place,
                                            dayNumber,
                                          )
                                        }
                                      >
                                        📍 {activity.place}
                                      </button>
                                    </div>
                                  ),
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
          </section>
        )}

        <section className="features-section">
          <h2 className="section-title">Why Anywhere App?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">💰</div>
              <h3>Smart Budgeting</h3>
              <p>AI-powered budget breakdown for your trips</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📍</div>
              <h3>Day-by-Day Itinerary</h3>
              <p>Detailed plans with timings and activities</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🗺️</div>
              <h3>Interactive Maps</h3>
              <p>Visual maps with all your destinations</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📚</div>
              <h3>Travel Knowledge</h3>
              <p>Ask questions about destinations</p>
            </div>
          </div>
        </section>

        <FAQSection />

        <section className="destinations-section">
          <h2 className="section-title">Popular Destinations</h2>
          <div className="destinations-grid">
            <div className="destination-card">
              <img
                src="https://assets.serenity.co.uk/38000-38999/38650/720x480.jpg"
                alt="Goa"
              />
              <div className="destination-info">
                <h3>Goa</h3>
                <p>Beaches & Nightlife</p>
              </div>
            </div>
            <div className="destination-card">
              <img
                src="https://tse3.mm.bing.net/th/id/OIP.1OaP_aGpqP7BpuFMmzWrUAHaEL?rs=1&pid=ImgDetMain&o=7&rm=3"
                alt="Jaipur"
              />
              <div className="destination-info">
                <h3>Jaipur</h3>
                <p>Heritage & Culture</p>
              </div>
            </div>
            <div className="destination-card">
              <img
                src="https://tse1.mm.bing.net/th/id/OIP.uT7Wl0kVemIz-HmT58PSqwHaEK?rs=1&pid=ImgDetMain&o=7&rm=3"
                alt="Kerala"
              />
              <div className="destination-info">
                <h3>Kerala</h3>
                <p>Backwaters & Nature</p>
              </div>
            </div>
            <div className="destination-card">
              <img
                src="https://www.tripsavvy.com/thmb/-P6SntHznvukqlm7YsUQlsw41Jc=/3217x2120/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-148864437-5ae5850a8e1b6e003704971f.jpg"
                alt="Manali"
              />
              <div className="destination-info">
                <h3>Manali</h3>
                <p>Mountains & Adventure</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>&copy; 2026 Anywhere App. All rights reserved.</p>
      </footer>
    </div>
  );
};

// FAQ Section Component
const FAQSection = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: "How does Anywhere App work?",
      answer: "Anywhere App uses AI-powered agents to plan your perfect trip. Simply enter your destination and duration, and our system will generate a complete travel plan including budget breakdown, day-by-day itinerary, interactive maps, and destination information from Wikipedia. All agents work together to provide you with comprehensive travel planning."
    },
    {
      question: "How can I find the cheapest trip using Anywhere App?",
      answer: "Our Budget Agent analyzes various factors to provide realistic cost estimates for your trip. It breaks down expenses into categories like transport, accommodation, food, activities, and miscellaneous. You can adjust your trip duration and preferences to find the most budget-friendly options. The system provides transparent pricing in Indian Rupees (₹) based on current market rates."
    },
    {
      question: "What destinations can I plan trips to?",
      answer: "You can plan trips to any destination in India and around the world. Our system has extensive knowledge of popular destinations like Goa, Jaipur, Kerala, Manali, Varanasi, Mumbai, and many more. The Wikipedia integration provides detailed historical and cultural context for each destination."
    },
    {
      question: "Can I customize my itinerary?",
      answer: "Yes! While our AI generates a comprehensive itinerary, you can use the interactive map to explore different locations and adjust your plans. The day-by-day breakdown allows you to see all activities with timings, and you can click on any location to view it on the map."
    },
    {
      question: "What information is included in the travel plan?",
      answer: "Each travel plan includes: (1) Budget breakdown with category-wise expenses, (2) Day-by-day itinerary with timings and activities, (3) Interactive map with all locations marked, (4) Wikipedia information about the destination including history and culture, (5) Downloadable PDF of your complete trip plan."
    },
    {
      question: "How accurate is the budget estimation?",
      answer: "Our Budget Agent uses realistic Indian pricing data for 2024-2026, considering factors like accommodation type (budget/mid-range/luxury), food costs, transportation, and activities. The estimates are based on current market rates and provide a reliable baseline for your trip planning."
    },
    {
      question: "Can I save my trip plans?",
      answer: "Yes! All your trip plans are automatically saved to your account. You can access them anytime from your dashboard. Additionally, each plan is saved as a PDF in the plans folder with detailed information about your itinerary, budget, and map."
    },
    {
      question: "What makes Anywhere App different from other travel planners?",
      answer: "Anywhere App uses a multi-agent AI system where specialized agents handle different aspects: Budget Agent for cost planning, Places Agent for itinerary creation, Map Agent for location mapping, RAG Agent for knowledge queries, and a Host Agent that orchestrates everything. This provides more accurate and comprehensive travel planning than single-purpose tools."
    },
    {
      question: "Is my travel data secure?",
      answer: "Yes, we take security seriously. Your account information is encrypted, and all travel plans are stored securely in our database. We use industry-standard authentication and password reset mechanisms to protect your data."
    },
    {
      question: "Can I ask questions about destinations?",
      answer: "Absolutely! Our RAG Agent can answer questions about destinations using uploaded travel documents and guides. Additionally, the Wikipedia integration provides comprehensive information about historical context, cultural significance, and related attractions for any destination you're planning to visit."
    }
  ];

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="faq-section">
      <h2 className="section-title">Booking Trip with Anywhere</h2>
      <div className="faq-container">
        {faqs.map((faq, index) => (
          <div key={index} className="faq-item">
            <button
              className={`faq-question ${openIndex === index ? 'active' : ''}`}
              onClick={() => toggleFAQ(index)}
            >
              <span>{faq.question}</span>
              <span className="faq-icon">{openIndex === index ? '−' : '+'}</span>
            </button>
            {openIndex === index && (
              <div className="faq-answer">
                <p>{faq.answer}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

// Pie Chart Component
const BudgetPieChart = ({ data }) => {
  const [hoveredSegment, setHoveredSegment] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const total = data.reduce((sum, item) => sum + item.amount, 0);
  const colors = [
    "#667eea",
    "#764ba2",
    "#f093fb",
    "#4facfe",
    "#43e97b",
    "#fa709a",
  ];

  let currentAngle = 0;
  const segments = data.map((item, index) => {
    const percentage = (item.amount / total) * 100;
    const angle = (percentage / 100) * 360;
    const startAngle = currentAngle;
    currentAngle += angle;

    return {
      ...item,
      percentage: percentage.toFixed(1),
      startAngle,
      endAngle: currentAngle,
      color: colors[index % colors.length],
    };
  });

  const handleMouseMove = (e, segment, index) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    setHoveredSegment(index);
  };

  const handleMouseLeave = () => {
    setHoveredSegment(null);
  };

  return (
    <div className="pie-chart-container">
      <div style={{ position: 'relative' }}>
        <svg viewBox="0 0 200 200" className="pie-chart">
          <circle cx="100" cy="100" r="90" fill="#f5f5f5" />
          {segments.map((segment, index) => {
            const startAngle = (segment.startAngle - 90) * (Math.PI / 180);
            const endAngle = (segment.endAngle - 90) * (Math.PI / 180);
            const x1 = 100 + 90 * Math.cos(startAngle);
            const y1 = 100 + 90 * Math.sin(startAngle);
            const x2 = 100 + 90 * Math.cos(endAngle);
            const y2 = 100 + 90 * Math.sin(endAngle);
            const largeArc = segment.endAngle - segment.startAngle > 180 ? 1 : 0;

            return (
              <path
                key={index}
                d={`M 100 100 L ${x1} ${y1} A 90 90 0 ${largeArc} 1 ${x2} ${y2} Z`}
                fill={segment.color}
                stroke="white"
                strokeWidth="2"
                style={{
                  cursor: 'pointer',
                  opacity: hoveredSegment === null || hoveredSegment === index ? 1 : 0.6,
                  transition: 'opacity 0.2s ease',
                }}
                onMouseMove={(e) => handleMouseMove(e, segment, index)}
                onMouseLeave={handleMouseLeave}
              />
            );
          })}
          <circle cx="100" cy="100" r="50" fill="white" />
        </svg>
        
        {hoveredSegment !== null && (
          <div
            className="pie-chart-tooltip"
            style={{
              position: 'absolute',
              left: `${tooltipPos.x}px`,
              top: `${tooltipPos.y}px`,
              transform: 'translate(-50%, -120%)',
              pointerEvents: 'none',
            }}
          >
            <div className="tooltip-content">
              <strong>{segments[hoveredSegment].category}</strong>
              <div>₹{segments[hoveredSegment].amount.toLocaleString()}</div>
              <div>{segments[hoveredSegment].percentage}% of total</div>
            </div>
          </div>
        )}
      </div>
      
      <div className="pie-chart-legend">
        {segments.map((segment, index) => (
          <div key={index} className="legend-item">
            <span
              className="legend-color"
              style={{ backgroundColor: segment.color }}
            ></span>
            <span className="legend-text">
              {segment.category} ({segment.percentage}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
