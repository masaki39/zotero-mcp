from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import PyPDF2

# FastMCPサーバの初期化
mcp = FastMCP("zotero")

ZOTERO_API_BASE = "http://localhost:23119/api/users/0/"
USER_AGENT = "zotero-mcp/1.0"

async def make_zotero_request(endpoint: str) -> Any:
    """Zotero APIへのリクエストを行う。"""
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
    """Zoteroライブラリ内のアイテムを著者名とタイトルで検索する（添付ファイルを除外、最大30件）。"""
    # クエリパラメータの組み立て
    params = [
        "itemType=-attachment",
        "limit=30"
    ]
    if q:
        params.append(f"q={q}")
    param_str = "&".join(params)
    data = await make_zotero_request(f"items?{param_str}")
    if "error" in data:
        return f"Zotero APIエラー: {data['error']}"
    if not data:
        return "アイテムが見つからなかった。"
    return data

@mcp.tool()
async def get_an_item(item_key: str) -> str:
    """Zoteroのライブラリ内の指定されたアイテムの詳細をitem_keyをキーに取得する。"""
    data = await make_zotero_request(f"items/{item_key}")
    if "error" in data:
        return f"Zotero APIエラー: {data['error']}"
    return data

@mcp.tool()
async def read_pdf(pdf_path: str) -> str:
    """指定されたpathのPDFファイルを読み込んで、テキストを返す。"""
    with open(pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

if __name__ == "__main__":
    mcp.run(transport='stdio')
