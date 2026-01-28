-- Create meaningful views for ACS tables
-- This allows us to use readable names while keeping the original table names

-- View for population/demographics data (r50031872_sl140)
CREATE OR REPLACE VIEW acs_demographics AS
SELECT * FROM r50031872_sl140;

-- View for housing data (r50031874_sl140)
CREATE OR REPLACE VIEW acs_housing AS
SELECT * FROM r50031874_sl140;

-- Grant permissions if needed
GRANT SELECT ON acs_demographics TO postgres;
GRANT SELECT ON acs_housing TO postgres;





