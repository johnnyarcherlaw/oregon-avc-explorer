# AVC Explorer Data Methodology

## Core Principle

The original Assurance of Voluntary Compliance is the primary source.

AVC Explorer distinguishes between information contained in the
original source and information derived by the project.

## Data Levels

### 1. Source Data

Information reproduced directly from an official source, including:

- respondent names
- dates
- case numbers
- statutory citations
- monetary provisions
- court information
- original document URLs

### 2. Extracted / Normalized Data

Information standardized without changing its substantive meaning.

Examples:

- "ORS 646.608 (1) (e)" → "ORS 646.608(1)(e)"
- "$50,000.00" → 50000
- normalization of respondent names for search

The original value should be preserved whenever practical.

### 3. Derived Data

Information created through AVC Explorer's analysis.

Examples:

- industry classifications
- subject-matter categories
- plain-language summaries
- Oregon-led vs. multistate classification
- analytical tags

Derived information must not be presented as though it originated
from the Oregon Department of Justice.

## Missing Data

Missing information is NULL.

Missing information must never be represented as:

- 0
- $0
- "None"

unless the source affirmatively establishes that value.

## Financial Data

Dollar amounts must retain their legal context.

AVC Explorer does not automatically characterize a monetary provision
as a civil penalty, restitution, attorney fee, or other form of relief
unless supported by the source.

Multistate settlement totals and Oregon-specific allocations are
recorded separately.

## Source Documents

Whenever possible, every AVC record should retain:

- official source URL
- local source filename
- date acquired
- SHA-256 hash of downloaded source
- publisher/source agency

Original source files must not be modified.