import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "./MyTrips.css";

const MyTrips = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [generatingPdf, setGeneratingPdf] = useState(null);

  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/my-trips`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await res.json();
      if (data.success) {
        setTrips(data.trips);
      }
    } catch (error) {
      console.error("Error fetching trips:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleDelete = async (tripId) => {
    if (!confirm("Are you sure you want to delete this trip?")) return;

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/trips/${tripId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        setTrips(trips.filter((t) => t.id !== tripId));
      }
    } catch (error) {
      console.error("Error deleting trip:", error);
    }
  };

  const handleDownloadPDF = async (trip) => {
    setGeneratingPdf(trip.id);
    
    try {
      console.log('🔍 Fetching trip data for:', trip.id);
      
      // Fetch full trip data
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/trips/${trip.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await res.json();
      console.log('📦 API Response:', data);
      
      if (data.success && data.trip) {
        console.log('✅ Trip data received:', {
          destination: data.trip.destination,
          duration: data.trip.duration_days,
          pdf_url: data.trip.pdf_url
        });
        
        // Check if PDF URL exists
        if (data.trip.pdf_url) {
          console.log('📄 Using backend-generated PDF:', data.trip.pdf_url);
          
          // Download the PDF from Blob storage
          window.open(data.trip.pdf_url, '_blank');
          console.log('✅ PDF download initiated');
        } else {
          alert('⚠️ PDF not available for this trip. Please create a NEW trip to generate a PDF.\n\nOld trips were saved before PDF generation was implemented.');
        }
      } else {
        console.error('❌ API returned error:', data);
        alert("Failed to fetch trip data");
      }
    } catch (error) {
      console.error("Error downloading PDF:", error);
      alert("Error downloading PDF. Please try again.");
    } finally {
      setGeneratingPdf(null);
    }
  };

  const filteredTrips = trips.filter((trip) => {
    const matchesFilter =
      filter === "all" ||
      (filter === "completed" && trip.status === "completed") ||
      (filter === "upcoming" && trip.status === "upcoming") ||
      (filter === "draft" && trip.status === "draft");

    const matchesSearch =
      searchQuery === "" ||
      trip.destination?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      trip.user_query?.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const stats = {
    total: trips.length,
    completed: trips.filter((t) => t.status === "completed").length,
    upcoming: trips.filter((t) => t.status === "upcoming").length,
  };

  const getEmoji = (destination) => {
    const emojiMap = {
      pune: "🏙️",
      varanasi: "🕌",
      goa: "🏖️",
      jaipur: "🕍",
      delhi: "🏛️",
      mumbai: "🌆",
      kerala: "🚢",
      manali: "🏔️",
      darjeeling: "🍵",
    };

    const dest = destination?.toLowerCase() || "";
    for (const [key, emoji] of Object.entries(emojiMap)) {
      if (dest.includes(key)) return emoji;
    }
    return "✈️";
  };

  return (
    <div className="my-trips-page">
      {/* NAV */}
      <nav className="trips-nav">
        <div className="nav-logo">
          <div className="logo-dot"></div>
          Anywhere app.
        </div>
        <ul className="nav-links">
          <li>
            <a href="/dashboard">Home</a>
          </li>
          <li>
            <a href="/my-trips" className="active">
              My Trips
            </a>
          </li>
          <li>
            <a href="/my-trips" className="active">
              My Trips
            </a>
          </li>
          <li>
            <a href="/recommendations">Recommendations</a>
          </li>
          <li>
            <a href="/about">About</a>
          </li>
        </ul>
        <div className="nav-user">
          <div className="nav-user-info">
            <div className="nav-user-name">
              {user?.first_name} {user?.last_name}
            </div>
            <div className="nav-user-email">{user?.email}</div>
          </div>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>

      {/* PAGE */}
      <div className="page">
        {/* HEADER */}
        <div className="page-header">
          <div>
            <h1>
              My Trips<span>.</span>
            </h1>
            <p>All your AI-planned travel itineraries in one place</p>
          </div>
          <button className="btn-new" onClick={() => navigate("/dashboard")}>
            ＋ Plan New Trip
          </button>
        </div>

        {/* STATS */}
        <div className="stats">
          <div className="stat-card">
            <div className="stat-icon purple">✈️</div>
            <div>
              <div className="stat-val">{stats.total}</div>
              <div className="stat-lbl">Total Trips Planned</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon green">✅</div>
            <div>
              <div className="stat-val">{stats.completed}</div>
              <div className="stat-lbl">Completed</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon yellow">🗓️</div>
            <div>
              <div className="stat-val">{stats.upcoming}</div>
              <div className="stat-lbl">Upcoming</div>
            </div>
          </div>
        </div>

        {/* TABLE CARD */}
        <div className="table-card">
          {/* TOOLBAR */}
          <div className="table-toolbar">
            <div className="toolbar-left">
              <div className="search-box">
                <span>🔍</span>
                <input
                  type="text"
                  placeholder="Search trips..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div
                className={`filter-pill ${filter === "all" ? "active" : ""}`}
                onClick={() => setFilter("all")}
              >
                All
              </div>
              <div
                className={`filter-pill ${filter === "completed" ? "active" : ""}`}
                onClick={() => setFilter("completed")}
              >
                Completed
              </div>
              <div
                className={`filter-pill ${filter === "upcoming" ? "active" : ""}`}
                onClick={() => setFilter("upcoming")}
              >
                Upcoming
              </div>
              <div
                className={`filter-pill ${filter === "draft" ? "active" : ""}`}
                onClick={() => setFilter("draft")}
              >
                Draft
              </div>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
              Showing {filteredTrips.length} of {trips.length} trips
            </div>
          </div>

          {/* TABLE */}
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center" }}>
              <div className="spinner"></div>
              <p>Loading your trips...</p>
            </div>
          ) : filteredTrips.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--muted)" }}>
              <p>No trips found. Start planning your first trip!</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th style={{ width: "60px" }}>Sr. No</th>
                  <th>Trip</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Created On</th>
                  <th>Plan (PDF)</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrips.map((trip, index) => (
                  <tr key={trip.id}>
                    <td>
                      <div className="sr-no">{index + 1}</div>
                    </td>
                    <td>
                      <div className="trip-cell">
                        <div className="trip-thumb">{getEmoji(trip.destination)}</div>
                        <div>
                          <div className="trip-name">
                            {trip.duration_days}-Day Trip to {trip.destination}
                          </div>
                          <div className="trip-meta">{trip.destination}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ color: "var(--muted)", fontSize: ".82rem" }}>
                      {trip.duration_days} day{trip.duration_days > 1 ? "s" : ""}
                    </td>
                    <td>
                      {trip.status === "completed" && (
                        <span className="badge badge-done">
                          <span className="badge-dot"></span>Completed
                        </span>
                      )}
                      {trip.status === "upcoming" && (
                        <span className="badge badge-upcoming">
                          <span className="badge-dot"></span>Upcoming
                        </span>
                      )}
                      {trip.status === "draft" && (
                        <span className="badge badge-draft">
                          <span className="badge-dot"></span>Draft
                        </span>
                      )}
                    </td>
                    <td style={{ color: "var(--muted)", fontSize: ".82rem" }}>
                      {new Date(trip.created_at).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td>
                      <button
                        className="pdf-download-btn"
                        onClick={() => handleDownloadPDF(trip)}
                        disabled={generatingPdf === trip.id}
                        title="Download PDF"
                      >
                        {generatingPdf === trip.id ? (
                          <>
                            <span className="spinner-small"></span>
                            Generating...
                          </>
                        ) : (
                          <>
                            📥 Download PDF
                          </>
                        )}
                      </button>
                    </td>
                    <td>
                      <div className="actions">
                        <button
                          className="icon-btn"
                          title="View"
                          onClick={() => navigate(`/trip/${trip.id}`)}
                        >
                          👁️
                        </button>
                        <button
                          className="icon-btn danger"
                          title="Delete"
                          onClick={() => handleDelete(trip.id)}
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyTrips;
