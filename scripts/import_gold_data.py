import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "avc_explorer.db"
REFERENCE_DIR = ROOT / "data" / "reference"


def dollars_to_cents(amount):
    """Convert JSON dollar values to exact integer cents."""
    return int(round(float(amount) * 100))


def get_or_create_respondent(conn, respondent):
    existing = conn.execute(
        """
        SELECT id
        FROM respondents
        WHERE legal_name = ?
        """,
        (respondent["legal_name"],),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = conn.execute(
        """
        INSERT INTO respondents (
            legal_name,
            normalized_name,
            entity_type,
            parent_entity
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            respondent["legal_name"],
            respondent.get("normalized_name"),
            respondent.get("entity_type"),
            respondent.get("parent_entity"),
        ),
    )

    return cursor.lastrowid


def get_or_create_authority(conn, authority):
    existing = conn.execute(
        """
        SELECT id
        FROM legal_authorities
        WHERE jurisdiction = ?
          AND normalized_citation = ?
        """,
        (
            authority.get("jurisdiction"),
            authority.get("normalized_citation"),
        ),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = conn.execute(
        """
        INSERT INTO legal_authorities (
            jurisdiction,
            citation,
            normalized_citation,
            description
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            authority.get("jurisdiction"),
            authority["citation"],
            authority.get("normalized_citation"),
            authority.get("description"),
        ),
    )

    return cursor.lastrowid


def get_or_create_category(conn, category):
    existing = conn.execute(
        """
        SELECT id
        FROM categories
        WHERE name = ?
        """,
        (category["name"],),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = conn.execute(
        """
        INSERT INTO categories (
            name,
            category_type
        )
        VALUES (?, ?)
        """,
        (
            category["name"],
            category.get("category_type"),
        ),
    )

    return cursor.lastrowid


def import_avc(conn, data):
    avc = data["avc"]

    cursor = conn.execute(
        """
        INSERT INTO avcs (
            title,
            case_number,
            execution_date,
            filing_date,
            effective_date,
            court_name,
            county,
            state,
            is_multistate,
            summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            avc["title"],
            avc.get("case_number"),
            avc.get("execution_date"),
            avc.get("filing_date"),
            avc.get("effective_date"),
            avc.get("court_name"),
            avc.get("county"),
            avc.get("state", "Oregon"),
            int(avc.get("is_multistate", False)),
            avc.get("summary"),
        ),
    )

    avc_id = cursor.lastrowid

    # --------------------------------------------------------
    # Respondents
    # --------------------------------------------------------

    for respondent in data.get("respondents", []):
        respondent_id = get_or_create_respondent(conn, respondent)

        conn.execute(
            """
            INSERT INTO avc_respondents (
                avc_id,
                respondent_id,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                avc_id,
                respondent_id,
                respondent.get("role", "respondent"),
            ),
        )

    # --------------------------------------------------------
    # Legal authorities
    # --------------------------------------------------------

    for authority in data.get("legal_authorities", []):
        authority_id = get_or_create_authority(conn, authority)

        conn.execute(
            """
            INSERT INTO avc_legal_authorities (
                avc_id,
                legal_authority_id,
                authority_role,
                source_text,
                source_page
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                avc_id,
                authority_id,
                authority.get("authority_role"),
                authority.get("source_text"),
                authority.get("source_page"),
            ),
        )

    # --------------------------------------------------------
    # Financial provisions
    #
    # fixture_id and parent_fixture_id exist only in the gold
    # fixture files. They allow us to create explicit financial
    # relationships without relying on array order or guessing
    # from descriptions.
    # --------------------------------------------------------

    financial_id_map = {}
    provisions = data.get("financial_provisions", [])

    # First pass: create every financial provision.
    for provision in provisions:
        cursor = conn.execute(
            """
            INSERT INTO financial_provisions (
                avc_id,
                amount_cents,
                relief_type,
                payment_status,
                parent_financial_provision_id,
                recipient,
                jurisdiction,
                description,
                source_page
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                avc_id,
                dollars_to_cents(provision["amount"]),
                provision.get("relief_type"),
                provision.get("payment_status"),
                None,
                provision.get("recipient"),
                provision.get("jurisdiction"),
                provision.get("description"),
                provision.get("source_page"),
            ),
        )

        fixture_id = provision.get("fixture_id")

        if fixture_id:
            if fixture_id in financial_id_map:
                raise ValueError(
                    f"Duplicate financial fixture_id: {fixture_id}"
                )

            financial_id_map[fixture_id] = cursor.lastrowid

    # Second pass: resolve explicit parent-child relationships.
    for provision in provisions:
        fixture_id = provision.get("fixture_id")
        parent_fixture_id = provision.get("parent_fixture_id")

        if not parent_fixture_id:
            continue

        if not fixture_id:
            raise ValueError(
                "Financial provision with a parent must have a fixture_id."
            )

        if fixture_id not in financial_id_map:
            raise ValueError(
                f"Unknown financial fixture_id: {fixture_id}"
            )

        if parent_fixture_id not in financial_id_map:
            raise ValueError(
                f"Unknown parent_fixture_id: {parent_fixture_id}"
            )

        conn.execute(
            """
            UPDATE financial_provisions
            SET parent_financial_provision_id = ?
            WHERE id = ?
            """,
            (
                financial_id_map[parent_fixture_id],
                financial_id_map[fixture_id],
            ),
        )

    # --------------------------------------------------------
    # Source document
    # --------------------------------------------------------

    document = data.get("document")

    if document:
        conn.execute(
            """
            INSERT INTO documents (
                avc_id,
                document_type,
                source_url,
                local_filename,
                publisher
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                avc_id,
                document.get("document_type", "AVC"),
                document["source_url"],
                document.get("local_filename"),
                document.get(
                    "publisher",
                    "Oregon Department of Justice",
                ),
            ),
        )

    # --------------------------------------------------------
    # Categories
    # --------------------------------------------------------

    for category in data.get("categories", []):
        category_id = get_or_create_category(conn, category)

        conn.execute(
            """
            INSERT INTO avc_categories (
                avc_id,
                category_id,
                classification_method,
                confidence,
                verified
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                avc_id,
                category_id,
                category.get("classification_method"),
                category.get("confidence"),
                int(category.get("verified", False)),
            ),
        )

    return avc_id


def main():
    fixture_files = sorted(
        REFERENCE_DIR.glob("*_expected.json")
    )

    if not fixture_files:
        raise RuntimeError("No gold fixture files found.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        for fixture_path in fixture_files:
            with fixture_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            avc_id = import_avc(conn, data)

            print(
                f"Imported {fixture_path.name} "
                f"as AVC id {avc_id}"
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print(
        f"\nImported {len(fixture_files)} gold AVCs."
    )
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()