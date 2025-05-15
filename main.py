from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import PyPDF2
import urllib.parse
import os

# Initialize FastMCP server
mcp = FastMCP("zotero")

ZOTERO_API_BASE = "http://localhost:23119/api/users/0/"
USER_AGENT = "zotero-mcp/1.0"

async def make_zotero_request(endpoint: str) -> Any:
    """Make a request to the Zotero API."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    url = f"{ZOTERO_API_BASE}{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@mcp.tool()
async def zotero_search_items(q: str = "") -> str:
    """Search items in the Zotero library by author and title (excluding attachments, up to 30 results)."""
    # Build query parameters
    params = [
        "itemType=-attachment",
        "limit=30"
    ]
    if q:
        params.append(f"q={q}")
    param_str = "&".join(params)
    data = await make_zotero_request(f"items?{param_str}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"
    if not data:
        return "No items found."
    return data

@mcp.tool()
async def zotero_get_item(itemKey: str) -> str:
    """Retrieve the details of a specified item in the Zotero library by itemKey."""
    data = await make_zotero_request(f"items/{itemKey}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"
    return data

@mcp.tool()
async def zotero_read_pdf(itemKey: str) -> str:
    """From the children of the item specified by itemKey in the Zotero library, find the first PDF attachment, read it from the local file system, and return its full text."""
    # Get children
    children = await make_zotero_request(f"items/{itemKey}/children")
    if "error" in children:
        return f"Zotero API error: {children['error']}"
    # Search for PDF attachment
    pdf_path = None
    for child in children:
        if child['data'].get('itemType') == 'attachment' and child['data'].get('contentType') == 'application/pdf':
            enclosure = child.get('links', {}).get('enclosure', {})
            href = enclosure.get('href')
            if href and href.startswith('file:///'):
                # URLからファイルパスへの変換（クロスプラットフォーム対応）
                if os.name == 'nt':  # Windows
                    pdf_path = urllib.parse.unquote(href[8:])  # 'file:///' (8文字) を削除
                else:  # Unix系 (macOS, Linux)
                    pdf_path = urllib.parse.unquote(href[7:])  # 'file://' (7文字) を削除
                break
    if not pdf_path:
        return "No PDF attachment found."
    # Read PDF and extract text
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)} (Path: {pdf_path})"

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
