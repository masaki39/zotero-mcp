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

if __name__ == "__main__":
    mcp.run(transport='stdio')
