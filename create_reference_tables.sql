-- Reference tables that can be joined with ACS tables via geographic identifiers

-- 1. States reference table
CREATE TABLE IF NOT EXISTS states (
    state_code VARCHAR(2) PRIMARY KEY,
    state_name VARCHAR(100),
    state_fips VARCHAR(2),
    region VARCHAR(50),
    division VARCHAR(50)
);

-- 2. Counties reference table  
CREATE TABLE IF NOT EXISTS counties (
    state_fips VARCHAR(2),
    county_fips VARCHAR(3),
    county_name VARCHAR(100),
    state_code VARCHAR(2),
    PRIMARY KEY (state_fips, county_fips)
);

-- 3. Metropolitan Statistical Areas (MSA)
CREATE TABLE IF NOT EXISTS metro_areas (
    cbsa_code VARCHAR(10) PRIMARY KEY,
    cbsa_name VARCHAR(200),
    metro_micro VARCHAR(20),
    state_codes TEXT
);

-- Insert sample data for states
INSERT INTO states (state_code, state_name, state_fips, region, division) VALUES
('AL', 'Alabama', '01', 'South', 'East South Central'),
('AK', 'Alaska', '02', 'West', 'Pacific'),
('AZ', 'Arizona', '04', 'West', 'Mountain'),
('AR', 'Arkansas', '05', 'South', 'West South Central'),
('CA', 'California', '06', 'West', 'Pacific'),
('CO', 'Colorado', '08', 'West', 'Mountain'),
('CT', 'Connecticut', '09', 'Northeast', 'New England'),
('DE', 'Delaware', '10', 'South', 'South Atlantic'),
('FL', 'Florida', '12', 'South', 'South Atlantic'),
('GA', 'Georgia', '13', 'South', 'South Atlantic'),
('HI', 'Hawaii', '15', 'West', 'Pacific'),
('ID', 'Idaho', '16', 'West', 'Mountain'),
('IL', 'Illinois', '17', 'Midwest', 'East North Central'),
('IN', 'Indiana', '18', 'Midwest', 'East North Central'),
('IA', 'Iowa', '19', 'Midwest', 'West North Central'),
('KS', 'Kansas', '20', 'Midwest', 'West North Central'),
('KY', 'Kentucky', '21', 'South', 'East South Central'),
('LA', 'Louisiana', '22', 'South', 'West South Central'),
('ME', 'Maine', '23', 'Northeast', 'New England'),
('MD', 'Maryland', '24', 'South', 'South Atlantic'),
('MA', 'Massachusetts', '25', 'Northeast', 'New England'),
('MI', 'Michigan', '26', 'Midwest', 'East North Central'),
('MN', 'Minnesota', '27', 'Midwest', 'West North Central'),
('MS', 'Mississippi', '28', 'South', 'East South Central'),
('MO', 'Missouri', '29', 'Midwest', 'West North Central'),
('MT', 'Montana', '30', 'West', 'Mountain'),
('NE', 'Nebraska', '31', 'Midwest', 'West North Central'),
('NV', 'Nevada', '32', 'West', 'Mountain'),
('NH', 'New Hampshire', '33', 'Northeast', 'New England'),
('NJ', 'New Jersey', '34', 'Northeast', 'Middle Atlantic'),
('NM', 'New Mexico', '35', 'West', 'Mountain'),
('NY', 'New York', '36', 'Northeast', 'Middle Atlantic'),
('NC', 'North Carolina', '37', 'South', 'South Atlantic'),
('ND', 'North Dakota', '38', 'Midwest', 'West North Central'),
('OH', 'Ohio', '39', 'Midwest', 'East North Central'),
('OK', 'Oklahoma', '40', 'South', 'West South Central'),
('OR', 'Oregon', '41', 'West', 'Pacific'),
('PA', 'Pennsylvania', '42', 'Northeast', 'Middle Atlantic'),
('RI', 'Rhode Island', '43', 'Northeast', 'New England'),
('SC', 'South Carolina', '44', 'South', 'South Atlantic'),
('SD', 'South Dakota', '46', 'Midwest', 'West North Central'),
('TN', 'Tennessee', '47', 'South', 'East South Central'),
('TX', 'Texas', '48', 'South', 'West South Central'),
('UT', 'Utah', '49', 'West', 'Mountain'),
('VT', 'Vermont', '50', 'Northeast', 'New England'),
('VA', 'Virginia', '51', 'South', 'South Atlantic'),
('WA', 'Washington', '53', 'West', 'Pacific'),
('WV', 'West Virginia', '54', 'South', 'South Atlantic'),
('WI', 'Wisconsin', '55', 'Midwest', 'East North Central'),
('WY', 'Wyoming', '56', 'West', 'Mountain'),
('DC', 'District of Columbia', '11', 'South', 'South Atlantic')
ON CONFLICT (state_code) DO NOTHING;

-- Insert sample counties for Georgia (since your data has GA)
INSERT INTO counties (state_fips, county_fips, county_name, state_code) VALUES
('13', '121', 'Fulton', 'GA'),
('13', '089', 'DeKalb', 'GA'),
('13', '135', 'Gwinnett', 'GA'),
('13', '067', 'Cobb', 'GA'),
('13', '151', 'Clayton', 'GA')
ON CONFLICT (state_fips, county_fips) DO NOTHING;

-- Insert sample metro areas
INSERT INTO metro_areas (cbsa_code, cbsa_name, metro_micro, state_codes) VALUES
('12060', 'Atlanta-Sandy Springs-Roswell, GA', 'Metropolitan', 'GA'),
('31080', 'Los Angeles-Long Beach-Anaheim, CA', 'Metropolitan', 'CA'),
('35620', 'New York-Newark-Jersey City, NY-NJ-PA', 'Metropolitan', 'NY,NJ,PA'),
('16980', 'Chicago-Naperville-Elgin, IL-IN-WI', 'Metropolitan', 'IL,IN,WI'),
('19100', 'Dallas-Fort Worth-Arlington, TX', 'Metropolitan', 'TX')
ON CONFLICT (cbsa_code) DO NOTHING;





