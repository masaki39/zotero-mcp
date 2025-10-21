# Zotero MCP Server

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/masaki39-zotero-mcp?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/masaki39-zotero-mcp)
![PyPI - Downloads](https://img.shields.io/pypi/dm/masaki39-zotero-mcp)

An MCP (Model Context Protocol) server that integrates with Zotero's local API to search, retrieve, and extract full text from PDFs in your Zotero library.

## Prerequisites

- Zotero application with local API enabled
- uv (recommended) or Python 3.12+ with pip

## Enable Zotero Local API

In Zotero's settings (Preferences → Advanced → General), enable:

☑️ **Allow other applications on this computer to communicate with Zotero**

## Configuration

Add the following to your MCP client configuration file (e.g., `mcp.json` for Claude Desktop or Cursor):

```json
{
  "mcpServers": {
    "zotero": {
      "command": "uvx",
      "args": ["masaki39-zotero-mcp"]
    }
  }
}
```

## Available Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `zotero_search_items` | `q` (optional) | Search items in your Zotero library by author name or title. Returns up to 30 matching items (excluding attachments). |
| `zotero_get_item` | `itemKey` (required) | Retrieve detailed information about a specific item including title, authors, publication info, abstract, tags, etc. |
| `zotero_read_pdf` | `itemKey` (required) | Extract full text from a PDF attachment associated with a Zotero item. |
| `read_pdf` | `local_path` (required) | Extract full text from a PDF file at a local file path. Can be used with filesystem MCP servers. |

## Example Usage

Once configured, you can use these tools through your MCP client:

- "Search my Zotero library for papers about machine learning"
- "Get details for item ABCD1234"
- "Extract the text from the PDF attached to item ABCD1234"

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests are welcome at https://github.com/masaki39/zotero-mcp


