-- ================================
-- TABLE 1: resumes (raw uploads)
-- ================================
CREATE TABLE IF NOT EXISTS resumes (
    id VARCHAR(100) PRIMARY KEY,
    file_name VARCHAR(255),
    file_path TEXT,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    skills TEXT,
    years_experience INT,
    education VARCHAR(255),
    raw_text LONGTEXT,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- TABLE 2: parsed_resumes (AI data)
-- ================================
CREATE TABLE IF NOT EXISTS parsed_resumes (
    resume_id VARCHAR(100) PRIMARY KEY,
    full_name VARCHAR(255),
    email_id VARCHAR(255),
    github_portfolio TEXT,
    linkedin_id TEXT,
    skills JSON,
    education JSON,
    key_projects JSON,
    internships JSON,
    parsed_text_length INT,
    key_categories JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
