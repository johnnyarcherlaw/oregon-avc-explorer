from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_connection


app = FastAPI(
    title="Oregon AVC Explorer",
    description="Search Oregon Assurances of Voluntary Compliance.",
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(
    directory="app/templates"
)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/search")
def search(
    request: Request,
    q: str = Query(default=""),
):
    query = q.strip()

    if not query:
        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context={
                "query": query,
                "results": [],
            },
        )

    search_term = f"%{query}%"

    connection = get_connection()

    try:
        results = connection.execute(
            """
            SELECT DISTINCT
                a.id,
                a.title,
                a.case_number,
                a.execution_date,
                a.is_multistate
            FROM avcs a

            LEFT JOIN avc_respondents ar
                ON ar.avc_id = a.id

            LEFT JOIN respondents r
                ON r.id = ar.respondent_id

            LEFT JOIN avc_legal_authorities ala
                ON ala.avc_id = a.id

            LEFT JOIN legal_authorities la
                ON la.id = ala.legal_authority_id

            LEFT JOIN avc_categories ac
                ON ac.avc_id = a.id

            LEFT JOIN categories c
                ON c.id = ac.category_id

            WHERE
                a.title LIKE ? COLLATE NOCASE
                OR a.case_number LIKE ? COLLATE NOCASE
                OR r.legal_name LIKE ? COLLATE NOCASE
                OR r.normalized_name LIKE ? COLLATE NOCASE
                OR la.citation LIKE ? COLLATE NOCASE
                OR la.normalized_citation LIKE ? COLLATE NOCASE
                OR c.name LIKE ? COLLATE NOCASE

            ORDER BY a.execution_date DESC
            """,
            (
                search_term,
                search_term,
                search_term,
                search_term,
                search_term,
                search_term,
                search_term,
            ),
        ).fetchall()

    finally:
        connection.close()

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "query": query,
            "results": results,
        },
    )
@app.get("/avcs/{avc_id}")
def avc_detail(
    request: Request,
    avc_id: int,
):
    connection = get_connection()

    try:
        avc = connection.execute(
            """
            SELECT *
            FROM avcs
            WHERE id = ?
            """,
            (avc_id,),
        ).fetchone()

        if avc is None:
            return templates.TemplateResponse(
                request=request,
                name="avc_detail.html",
                context={
                    "avc": None,
                },
                status_code=404,
            )

        respondents = connection.execute(
            """
            SELECT
                r.legal_name,
                r.normalized_name,
                r.entity_type,
                ar.role
            FROM respondents r
            JOIN avc_respondents ar
                ON ar.respondent_id = r.id
            WHERE ar.avc_id = ?
            ORDER BY r.legal_name
            """,
            (avc_id,),
        ).fetchall()

        authorities = connection.execute(
            """
            SELECT
                la.citation,
                la.normalized_citation,
                la.jurisdiction,
                ala.authority_role,
                ala.source_text,
                ala.source_page
            FROM legal_authorities la
            JOIN avc_legal_authorities ala
                ON ala.legal_authority_id = la.id
            WHERE ala.avc_id = ?
            ORDER BY la.normalized_citation
            """,
            (avc_id,),
        ).fetchall()

        financial_provisions = connection.execute(
            """
            SELECT
                fp.id,
                fp.amount_cents,
                fp.relief_type,
                fp.payment_status,
                fp.recipient,
                fp.jurisdiction,
                fp.description,
                fp.source_page,
                parent.amount_cents
                    AS parent_amount_cents
            FROM financial_provisions fp
            LEFT JOIN financial_provisions parent
                ON parent.id =
                    fp.parent_financial_provision_id
            WHERE fp.avc_id = ?
            ORDER BY fp.id
            """,
            (avc_id,),
        ).fetchall()

        categories = connection.execute(
            """
            SELECT
                c.name,
                c.category_type
            FROM categories c
            JOIN avc_categories ac
                ON ac.category_id = c.id
            WHERE ac.avc_id = ?
            ORDER BY c.name
            """,
            (avc_id,),
        ).fetchall()

        documents = connection.execute(
            """
            SELECT
                document_type,
                source_url,
                publisher
            FROM documents
            WHERE avc_id = ?
            ORDER BY id
            """,
            (avc_id,),
        ).fetchall()

    finally:
        connection.close()

    return templates.TemplateResponse(
        request=request,
        name="avc_detail.html",
        context={
            "avc": avc,
            "respondents": respondents,
            "authorities": authorities,
            "financial_provisions": financial_provisions,
            "categories": categories,
            "documents": documents,
        },
    )