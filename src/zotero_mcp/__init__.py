from typing import Any
import httpx
import re
from mcp.server.fastmcp import FastMCP
import PyPDF2
import urllib.parse
import os

__version__ = "0.2.0"

mcp = FastMCP("zotero")

ZOTERO_API_BASE = "http://localhost:23119/api/users/0/"
CROSSREF_API_BASE = "https://api.crossref.org/works/"
USER_AGENT = "zotero-mcp/1.0"

CROSSREF_TYPE_MAP = {
    "journal-article": "journalArticle",
    "book": "book",
    "book-chapter": "bookSection",
    "proceedings-article": "conferencePaper",
    "dissertation": "thesis",
    "report": "report",
    "preprint": "preprint",
    "dataset": "dataset",
}


def _validate_item_key(item_key: str) -> bool:
    return bool(re.fullmatch(r'[A-Z0-9]{8}', item_key))


def _sanitize_doi(doi: str) -> str:
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi


def _crossref_to_zotero_item(message: dict) -> dict:
    item_type = CROSSREF_TYPE_MAP.get(message.get("type", ""), "journalArticle")
    title_list = message.get("title", [])
    creators = [
        {"creatorType": "author", "firstName": a.get("given", ""), "lastName": a.get("family", "")}
        for a in message.get("author", [])
    ]
    date_parts = message.get("published", {}).get("date-parts", [[]])
    year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""
    container = message.get("container-title", [])
    issn_list = message.get("ISSN", [])
    abstract = re.sub(r'<[^>]+>', '', message.get("abstract", ""))
    item = {
        "itemType": item_type,
        "title": title_list[0] if title_list else "",
        "creators": creators,
        "date": year,
        "publicationTitle": container[0] if container else "",
        "publisher": message.get("publisher", ""),
        "DOI": message.get("DOI", ""),
        "ISSN": issn_list[0] if issn_list else "",
        "abstractNote": abstract,
        "volume": message.get("volume", ""),
        "issue": message.get("issue", ""),
        "pages": message.get("page", ""),
    }
    return {k: v for k, v in item.items() if v != "" or k in ("itemType", "title", "creators")}


async def make_zotero_request(endpoint: str) -> Any:
    """Make a GET request to the Zotero local API."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    url = f"{ZOTERO_API_BASE}{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def make_connector_save(items: list, uri: str) -> Any:
    """POST to Zotero connector saveItems endpoint."""
    import time
    payload = {
        "sessionID": str(int(time.time() * 1000)),
        "items": items,
        "uri": uri,
    }
    url = "http://localhost:23119/connector/saveItems"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
                json=payload,
                timeout=30.0,
            )
            if response.status_code == 201:
                return {"success": True}
            response.raise_for_status()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}


async def make_crossref_request(doi: str) -> Any:
    """Make a GET request to the CrossRef API for a given DOI."""
    url = f"{CROSSREF_API_BASE}{doi}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=30.0,
            )
            if response.status_code == 404:
                return {"error": "DOI not found in CrossRef"}
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def zotero_search_items(q: str = "") -> str:
    """Search items in the Zotero library by author and title (excluding attachments, up to 30 results)."""
    params = ["itemType=-attachment", "limit=30"]
    if q:
        params.append(f"q={urllib.parse.quote(q, safe='')}")
    data = await make_zotero_request(f"items?{'&'.join(params)}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"
    if not data:
        return "No items found."

    result_lines = [f"Found {len(data)} items:\n"]
    for idx, item in enumerate(data, 1):
        item_data = item.get("data", {})
        meta = item.get("meta", {})
        item_key = item_data.get("key", "N/A")
        title = item_data.get("title", "No title")
        item_type = item_data.get("itemType", "N/A")
        date = item_data.get("date", "N/A")
        creators = item_data.get("creators", [])
        if creators:
            authors = ", ".join(f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators)
        else:
            authors = meta.get("creatorSummary", "N/A")
        publication = item_data.get("publicationTitle", item_data.get("bookTitle", ""))
        doi = item_data.get("DOI", "")
        result_lines.append(f"[{idx}] Item Key: {item_key}")
        result_lines.append(f"    Title: {title}")
        result_lines.append(f"    Authors: {authors}")
        result_lines.append(f"    Date: {date}")
        result_lines.append(f"    Type: {item_type}")
        if publication:
            result_lines.append(f"    Publication: {publication}")
        if doi:
            result_lines.append(f"    DOI: {doi}")
        result_lines.append("")
    return "\n".join(result_lines)


@mcp.tool()
async def zotero_get_item(itemKey: str) -> str:
    """Retrieve the details of a specified item in the Zotero library by itemKey."""
    if not _validate_item_key(itemKey):
        return "Invalid itemKey format. Expected 8 uppercase alphanumeric characters."
    data = await make_zotero_request(f"items/{itemKey}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"

    item_data = data.get("data", {})
    meta = data.get("meta", {})
    result_lines = []
    result_lines.append(f"Item Key: {item_data.get('key', 'N/A')}")
    result_lines.append(f"Type: {item_data.get('itemType', 'N/A')}")
    result_lines.append(f"Title: {item_data.get('title', 'No title')}")
    creators = item_data.get("creators", [])
    if creators:
        author_names = [f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators]
        result_lines.append(f"Authors: {', '.join(author_names)}")
    elif meta.get("creatorSummary"):
        result_lines.append(f"Authors: {meta['creatorSummary']}")
    if item_data.get("date"):
        result_lines.append(f"Date: {item_data['date']}")
    if item_data.get("publicationTitle"):
        result_lines.append(f"Publication: {item_data['publicationTitle']}")
    elif item_data.get("bookTitle"):
        result_lines.append(f"Book Title: {item_data['bookTitle']}")
    if item_data.get("DOI"):
        result_lines.append(f"DOI: {item_data['DOI']}")
    if item_data.get("ISBN"):
        result_lines.append(f"ISBN: {item_data['ISBN']}")
    if item_data.get("ISSN"):
        result_lines.append(f"ISSN: {item_data['ISSN']}")
    if item_data.get("url"):
        result_lines.append(f"URL: {item_data['url']}")
    if item_data.get("pages"):
        result_lines.append(f"Pages: {item_data['pages']}")
    if item_data.get("volume"):
        result_lines.append(f"Volume: {item_data['volume']}")
    if item_data.get("issue"):
        result_lines.append(f"Issue: {item_data['issue']}")
    if item_data.get("publisher"):
        result_lines.append(f"Publisher: {item_data['publisher']}")
    if item_data.get("language"):
        result_lines.append(f"Language: {item_data['language']}")
    if item_data.get("abstractNote"):
        result_lines.append(f"\nAbstract:")
        result_lines.append(item_data['abstractNote'])
    tags = item_data.get("tags", [])
    if tags:
        result_lines.append(f"\nTags: {', '.join(tag.get('tag', '') for tag in tags)}")
    if item_data.get("dateAdded"):
        result_lines.append(f"\nDate Added: {item_data['dateAdded']}")
    if item_data.get("dateModified"):
        result_lines.append(f"Date Modified: {item_data['dateModified']}")
    return "\n".join(result_lines)


@mcp.tool()
async def zotero_read_pdf(
    itemKey: str,
    page_number: int | None = None,
    attachment_index: int = 1,
) -> str:
    """Read a PDF attachment from a Zotero item. attachment_index selects which PDF (1-indexed, default=1). page_number reads a single page (1-indexed); if omitted, all pages are read."""
    if not _validate_item_key(itemKey):
        return "Invalid itemKey format. Expected 8 uppercase alphanumeric characters."
    children = await make_zotero_request(f"items/{itemKey}/children")
    if "error" in children:
        return f"Zotero API error: {children['error']}"

    pdf_paths = []
    for child in children:
        if child['data'].get('itemType') == 'attachment' and child['data'].get('contentType') == 'application/pdf':
            href = child.get('links', {}).get('enclosure', {}).get('href', '')
            if href.startswith('file:///'):
                if os.name == 'nt':
                    pdf_paths.append(urllib.parse.unquote(href[8:]))
                else:
                    pdf_paths.append(urllib.parse.unquote(href[7:]))

    if not pdf_paths:
        return "No PDF attachment found."
    if attachment_index < 1 or attachment_index > len(pdf_paths):
        return f"Attachment index {attachment_index} out of range. Found {len(pdf_paths)} PDF(s)."

    pdf_path = pdf_paths[attachment_index - 1]
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            if page_number is not None:
                if page_number < 1 or page_number > total_pages:
                    return f"Page {page_number} out of range. PDF has {total_pages} page(s)."
                text = pdf_reader.pages[page_number - 1].extract_text() or ""
                header = f"[PDF attachment {attachment_index}, page {page_number}/{total_pages}]\n"
            else:
                text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
                header = f"[PDF attachment {attachment_index}, all {total_pages} page(s)]\n"
        return header + text
    except Exception as e:
        return f"Error reading PDF: {str(e)} (Path: {pdf_path})"


@mcp.tool()
async def confirm_doi(doi: str) -> str:
    """Fetch metadata for a DOI from CrossRef to validate it exists before adding to Zotero."""
    doi = _sanitize_doi(doi)
    if not doi:
        return "Invalid DOI: empty string."
    data = await make_crossref_request(doi)
    if "error" in data:
        return f"CrossRef error: {data['error']}"

    message = data.get("message", {})
    title_list = message.get("title", [])
    title = title_list[0] if title_list else "No title"
    authors = [
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in message.get("author", [])
    ]
    date_parts = message.get("published", {}).get("date-parts", [[]])
    year = str(date_parts[0][0]) if date_parts and date_parts[0] else "N/A"
    container = message.get("container-title", [])
    journal = container[0] if container else "N/A"
    abstract = re.sub(r'<[^>]+>', '', message.get("abstract", ""))

    lines = [
        f"DOI: {message.get('DOI', doi)}",
        f"Type: {message.get('type', 'N/A')}",
        f"Title: {title}",
        f"Authors: {', '.join(authors) if authors else 'N/A'}",
        f"Year: {year}",
        f"Journal: {journal}",
        f"Publisher: {message.get('publisher', 'N/A')}",
    ]
    if abstract:
        lines.append(f"\nAbstract: {abstract}")
    return "\n".join(lines)


@mcp.tool()
async def add_item_by_doi(doi: str) -> str:
    """Add an item to the Zotero library by DOI. Fetches metadata from CrossRef, checks for duplicates by DOI, and creates the item only if it does not already exist."""
    doi = _sanitize_doi(doi)
    if not doi:
        return "Invalid DOI: empty string."

    crossref_data = await make_crossref_request(doi)
    if "error" in crossref_data:
        return f"DOI not found in CrossRef: {crossref_data['error']}"

    message = crossref_data.get("message", {})
    canonical_doi = message.get("DOI", doi)

    # Paginate through all items to find DOI match (q parameter does not search DOI field)
    start = 0
    limit = 100
    found_key = None
    while True:
        page = await make_zotero_request(f"items?itemType=-attachment&limit={limit}&start={start}")
        if isinstance(page, dict) and "error" in page:
            break
        if not page:
            break
        for item in page:
            existing_doi = item.get("data", {}).get("DOI", "")
            if existing_doi.strip().lower() == canonical_doi.strip().lower():
                found_key = item.get("data", {}).get("key", "?")
                break
        if found_key or len(page) < limit:
            break
        start += limit
    if found_key:
        return f"Item already exists in Zotero (key: {found_key})."

    zotero_item = _crossref_to_zotero_item(message)
    uri = f"https://doi.org/{canonical_doi}"
    result = await make_connector_save([zotero_item], uri)
    if "error" in result:
        return f"Zotero API error while adding item: {result['error']}"

    title_list = message.get("title", [""])
    title = title_list[0] if title_list else "(no title)"
    return f'Successfully added: "{title}" (DOI: {canonical_doi})'


def main():
    mcp.run(transport='stdio')
