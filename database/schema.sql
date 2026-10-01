-- Oregon AVC Explorer
-- Database Schema v0.1
--
-- Schema frozen after manual validation against five
-- Oregon DOJ Assurances of Voluntary Compliance:
-- Omnicare (2010)
-- United Telecom (2011)
-- Gustafson & Company (2021)
-- Avalon Healthcare Management (2022)
-- Verizon / TracFone (2024)
--
-- Source documents remain the authoritative record.
-- Structured and derived data must not be interpreted
-- as replacing or modifying the underlying AVC.

PRAGMA foreign_keys = ON;

-- ============================================================
-- AVCs
-- One row = one Assurance of Voluntary Compliance
-- ============================================================

CREATE TABLE avcs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    case_number TEXT,
    execution_date TEXT,
    filing_date TEXT,
    effective_date TEXT,

    court_name TEXT,
    county TEXT,
    state TEXT DEFAULT 'Oregon',

    is_multistate INTEGER NOT NULL DEFAULT 0,
    summary TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Respondents
-- A respondent may appear in more than one AVC.
-- An AVC may contain more than one respondent.
-- ============================================================

CREATE TABLE respondents (
    id INTEGER PRIMARY KEY,
    legal_name TEXT NOT NULL,
    normalized_name TEXT,
    entity_type TEXT,
    parent_entity TEXT
);

CREATE TABLE avc_legal_authorities (
    avc_id INTEGER NOT NULL,
    legal_authority_id INTEGER NOT NULL,

    authority_role TEXT,
    source_text TEXT,
    source_page INTEGER,

    PRIMARY KEY (avc_id, legal_authority_id, authority_role),

    FOREIGN KEY (avc_id) REFERENCES avcs(id),
    FOREIGN KEY (legal_authority_id) REFERENCES legal_authorities(id)
);

-- ============================================================
-- Legal Authorities
-- Statutes, regulations, etc. referenced by an AVC.
-- ============================================================

CREATE TABLE legal_authorities (
    id INTEGER PRIMARY KEY,
    jurisdiction TEXT,
    citation TEXT NOT NULL,
    normalized_citation TEXT,
    description TEXT
);


CREATE TABLE avc_legal_authorities (
    avc_id INTEGER NOT NULL,
    legal_authority_id INTEGER NOT NULL,

    source_text TEXT,
    source_page INTEGER,

    PRIMARY KEY (avc_id, legal_authority_id),

    FOREIGN KEY (avc_id) REFERENCES avcs(id),
    FOREIGN KEY (legal_authority_id) REFERENCES legal_authorities(id)
);


-- ============================================================
-- Financial Provisions
-- IMPORTANT:
-- Do not treat every dollar amount as a "penalty."
-- ============================================================

CREATE TABLE financial_provisions (
    id INTEGER PRIMARY KEY,
    avc_id INTEGER NOT NULL,

    amount_cents INTEGER NOT NULL

    relief_type TEXT,
    payment_status TEXT,

    parent_financial_provision_id INTEGER,

    recipient TEXT,
    jurisdiction TEXT,
    description TEXT,

    source_page INTEGER,

    FOREIGN KEY (avc_id) REFERENCES avcs(id),
    FOREIGN KEY (parent_financial_provision_id)
        REFERENCES financial_provisions(id)
);
-- ============================================================
-- Documents
-- Original source documents and provenance.
-- ============================================================

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    avc_id INTEGER NOT NULL,

    document_type TEXT DEFAULT 'AVC',
    source_url TEXT NOT NULL,
    local_filename TEXT,

    sha256 TEXT,
    date_acquired TEXT,

    publisher TEXT DEFAULT 'Oregon Department of Justice',

    FOREIGN KEY (avc_id) REFERENCES avcs(id)
);


-- ============================================================
-- Categories
-- These are classifications created by AVC Explorer,
-- NOT necessarily classifications supplied by Oregon DOJ.
-- ============================================================

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category_type TEXT
);


CREATE TABLE avc_categories (
    avc_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,

    classification_method TEXT,
    confidence REAL,
    verified INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (avc_id, category_id),

    FOREIGN KEY (avc_id) REFERENCES avcs(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);