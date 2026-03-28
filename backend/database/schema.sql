-- Travel Buddy Database Schema (PostgreSQL)
-- Stores structured travel plans with relationships

-- ============================================================================
-- USER AUTHENTICATION TABLES
-- ============================================================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- OTP table for password reset
CREATE TABLE IF NOT EXISTS password_reset_otps (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER DEFAULT 0,
    UNIQUE(email, otp)
);

-- Index for OTP lookups
CREATE INDEX IF NOT EXISTS idx_otp_email ON password_reset_otps(email);
CREATE INDEX IF NOT EXISTS idx_otp_expires ON password_reset_otps(expires_at);

-- ============================================================================
-- TRAVEL PLANNING TABLES
-- ============================================================================

-- Main travel plans table
CREATE TABLE IF NOT EXISTS travel_plans (
    id VARCHAR(255) PRIMARY KEY,  -- UUID from request_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Request metadata
    user_query TEXT NOT NULL,
    session_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,  -- success, error, partial
    version VARCHAR(10) DEFAULT '1.0',
    
    -- Plan details
    destination VARCHAR(255),
    duration_days INTEGER,
    
    -- Execution metadata
    execution_time_ms INTEGER,
    llm_tokens_used INTEGER,
    agents_called TEXT,  -- JSON array of agent names
    
    -- Full response
    display_text TEXT,
    display_format VARCHAR(50) DEFAULT 'markdown',
    error_message TEXT
);

-- Budget breakdown table
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) NOT NULL,
    
    -- Budget categories
    transport DECIMAL(10,2) NOT NULL DEFAULT 0,
    accommodation DECIMAL(10,2) NOT NULL DEFAULT 0,
    food DECIMAL(10,2) NOT NULL DEFAULT 0,
    activities DECIMAL(10,2) NOT NULL DEFAULT 0,
    miscellaneous DECIMAL(10,2) NOT NULL DEFAULT 0,
    
    -- Totals
    total DECIMAL(10,2) NOT NULL,
    leftover DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'INR',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plan_id) REFERENCES travel_plans(id) ON DELETE CASCADE
);

-- Itinerary days table
CREATE TABLE IF NOT EXISTS itinerary_days (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) NOT NULL,
    
    day_number INTEGER NOT NULL,
    date VARCHAR(50),
    total_cost DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plan_id) REFERENCES travel_plans(id) ON DELETE CASCADE,
    UNIQUE(plan_id, day_number)
);

-- Activities table
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    day_id INTEGER NOT NULL,
    
    time VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    cost DECIMAL(10,2),
    duration_minutes INTEGER,
    
    -- Location details
    location_name VARCHAR(500) NOT NULL,
    location_latitude DECIMAL(10,8),
    location_longitude DECIMAL(11,8),
    location_address TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (day_id) REFERENCES itinerary_days(id) ON DELETE CASCADE
);

-- Activity tips table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS activity_tips (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL,
    tip TEXT NOT NULL,
    
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Maps table
CREATE TABLE IF NOT EXISTS maps (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) NOT NULL,
    
    url TEXT NOT NULL,  -- Path to HTML file
    total_locations INTEGER NOT NULL,
    html_content TEXT,  -- Store full HTML for embedding
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plan_id) REFERENCES travel_plans(id) ON DELETE CASCADE
);

-- Map locations table
CREATE TABLE IF NOT EXISTS map_locations (
    id SERIAL PRIMARY KEY,
    map_id INTEGER NOT NULL,
    
    name VARCHAR(500) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    day INTEGER NOT NULL,
    time VARCHAR(20),
    description TEXT,
    image_url TEXT,  -- Wikipedia image URL
    
    FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE
);

-- Knowledge base queries (RAG)
CREATE TABLE IF NOT EXISTS knowledge_queries (
    id VARCHAR(255) PRIMARY KEY,  -- UUID from request_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence DECIMAL(5,4),
    
    -- Metadata
    session_id VARCHAR(255),
    execution_time_ms INTEGER,
    
    display_text TEXT
);

-- Knowledge sources (RAG)
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    
    source_name VARCHAR(500) NOT NULL,
    page_number VARCHAR(20),
    relevance_score DECIMAL(5,4),
    
    FOREIGN KEY (query_id) REFERENCES knowledge_queries(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_travel_plans_session ON travel_plans(session_id);
CREATE INDEX IF NOT EXISTS idx_travel_plans_created ON travel_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_travel_plans_destination ON travel_plans(destination);
CREATE INDEX IF NOT EXISTS idx_budgets_plan ON budgets(plan_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_days_plan ON itinerary_days(plan_id);
CREATE INDEX IF NOT EXISTS idx_activities_day ON activities(day_id);
CREATE INDEX IF NOT EXISTS idx_maps_plan ON maps(plan_id);
CREATE INDEX IF NOT EXISTS idx_map_locations_map ON map_locations(map_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_queries_session ON knowledge_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_queries_created ON knowledge_queries(created_at DESC);

-- Conversation history for memory
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_number INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'agent'
    content TEXT NOT NULL,
    plan_id VARCHAR(255),  -- Link to travel_plans if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, message_number)
);

-- Indexes for conversation queries
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id, message_number DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_plan ON conversation_history(plan_id);

-- Views for easy querying

-- Complete travel plan view
CREATE OR REPLACE VIEW v_complete_travel_plans AS
SELECT 
    tp.id,
    tp.created_at,
    tp.user_query,
    tp.destination,
    tp.duration_days,
    tp.status,
    b.total as budget_total,
    b.currency,
    COUNT(DISTINCT id_days.id) as total_days,
    COUNT(DISTINCT a.id) as total_activities,
    m.url as map_url
FROM travel_plans tp
LEFT JOIN budgets b ON tp.id = b.plan_id
LEFT JOIN itinerary_days id_days ON tp.id = id_days.plan_id
LEFT JOIN activities a ON id_days.id = a.day_id
LEFT JOIN maps m ON tp.id = m.plan_id
GROUP BY tp.id, tp.created_at, tp.user_query, tp.destination, tp.duration_days, tp.status, b.total, b.currency, m.url;

-- Activity summary view
CREATE OR REPLACE VIEW v_activity_summary AS
SELECT 
    a.id,
    a.title,
    a.time,
    a.location_name,
    id_days.day_number,
    tp.destination,
    tp.id as plan_id
FROM activities a
JOIN itinerary_days id_days ON a.day_id = id_days.id
JOIN travel_plans tp ON id_days.plan_id = tp.id;
