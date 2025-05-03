from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

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
async def get_all_items() -> str:
    """Zoteroライブラリ内の全アイテムを取得する。"""
    data = await make_zotero_request("items")
    if "error" in data:
        return f"Zotero APIエラー: {data['error']}"
    if not data:
        return "アイテムが見つからなかった。"
    # タイトルとIDのみを列挙
    items = [f"{item['data'].get('title', 'No Title')} (key: {item['key']})" for item in data]
    return "\n".join(items)

@mcp.tool()
async def filter_items(item_type: str = None, tag: str = None, title_contains: str = None) -> str:
    """Zoteroライブラリ内の全アイテムからitemType, tag, title部分一致で絞り込んだPDFのパスのみを返す。"""
    data = await make_zotero_request("items")
    if "error" in data:
        return f"Zotero APIエラー: {data['error']}"
    if not data:
        return "アイテムが見つからなかった。"
    results = []
    for item in data:
        d = item.get('data', {})
        if d.get('itemType') != 'attachment' or d.get('contentType') != 'application/pdf':
            continue
        if item_type and d.get('itemType') != item_type:
            continue
        if tag and tag not in [t.get('tag') for t in d.get('tags', [])]:
            continue
        if title_contains and title_contains not in d.get('title', ''):
            continue
        pdf_path = d.get('path') or d.get('url')
        if pdf_path:
            results.append(pdf_path)
    if not results:
        return "条件に合致するPDFが見つからなかった。"
    return "\n".join(results)

if __name__ == "__main__":
    mcp.run(transport='stdio')
