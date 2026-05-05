# Zotero MCP Server

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/masaki39-zotero-mcp?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/masaki39-zotero-mcp)
![PyPI - Downloads](https://img.shields.io/pypi/dm/masaki39-zotero-mcp)

An MCP (Model Context Protocol) server that integrates with Zotero's local API to search, retrieve, read PDFs, and add items by DOI from your Zotero library.

## Prerequisites

- Zotero application with local API enabled
- uv (recommended) or Python 3.12+

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
      "args": ["masaki39-zotero-mcp@latest"]
    }
  }
}
```

## Available Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `zotero_search_items` | `q` (optional) | Search items in your Zotero library by author name or title. Returns up to 30 matching items (excluding attachments). |
| `zotero_get_item` | `itemKey` (required) | Retrieve detailed information about a specific item including title, authors, publication info, abstract, tags, etc. |
| `zotero_read_pdf` | `itemKey` (required), `page_number` (optional), `attachment_index` (optional, default=1) | Extract text from a PDF attachment. Specify a page number to read a single page, or omit to read all pages. Use `attachment_index` to select among multiple PDFs. |
| `confirm_doi` | `doi` (required) | Fetch metadata for a DOI from CrossRef. Use this to validate a DOI before adding it to Zotero. |
| `add_item_by_doi` | `doi` (required) | Add an item to Zotero by DOI. Validates via CrossRef and checks for duplicates before adding. |

## Example Usage

Once configured, you can use these tools through your MCP client:

- "Search my Zotero library for papers about spinal deformity"
- "Get details for item ABCD1234"
- "Read page 3 of the PDF attached to item ABCD1234"
- "Look up DOI 10.1038/s41586-021-03819-2 and add it to my Zotero library"

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests are welcome at https://github.com/masaki39/zotero-mcp
