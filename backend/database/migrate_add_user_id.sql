-- Migration: Add user_id and PDF columns to travel_plans table
-- Run this on production PostgreSQL database

-- Check if user_id column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'travel_plans' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE travel_plans ADD COLUMN user_id INTEGER;
        ALTER TABLE travel_plans ADD CONSTRAINT fk_travel_plans_user 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        CREATE INDEX idx_travel_plans_user ON travel_plans(user_id);
    END IF;
END $$;

-- Check if pdf_url column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'travel_plans' AND column_name = 'pdf_url'
    ) THEN
        ALTER TABLE travel_plans ADD COLUMN pdf_url TEXT;
    END IF;
END $$;

-- Check if pdf_filename column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'travel_plans' AND column_name = 'pdf_filename'
    ) THEN
        ALTER TABLE travel_plans ADD COLUMN pdf_filename VARCHAR(500);
    END IF;
END $$;

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'travel_plans' 
AND column_name IN ('user_id', 'pdf_url', 'pdf_filename')
ORDER BY column_name;
