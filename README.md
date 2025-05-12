# Zotero MCP Server

This is an MCP server that utilizes Zotero's local API to search, retrieve, and extract full text from PDFs in the Zotero library.
This README is for Mac/Linux users.
Windows users should refer to the following link because I am not detailed enough:
[For Server Developers - Model Context Protocol](https://modelcontextprotocol.io/quickstart/server#windows)
I use Cursor as my MCP client.


## Prerequisites

- uv (Python package manager)
- Zotero application (local API must be enabled)
- Git
- Only when local installation
  - Python 3.12 or higher (lower version might work, but I haven't tested it)

## How to Enable Zotero Local API

In Zotero's settings, check the following item:

- [ ] Allow other applications on this computer to communicate with Zotero

## Installation

### Quick Start

Add the following to your `mcp.json` or mcp configuration file:

```json
{
  "mcpServers": {
    "zotero-mcp": {
      "command": "uvx",
      "args": ["git+https://github.com/masaki39/zotero-mcp.git"]
    }
  }
}
```

> ![caution]
> This method temporarily installs the latest version of the server from this repository.
> In security-conscious environments, it is recommended to use the local installation method.

### Local Installation

Run the following commands to set up the environment:

```bash
git clone https://github.com/masaki39/zotero-mcp
cd zotero-mcp
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
```

Add the following to your `mcp.json` or mcp configuration file:
(Replace `path/to/zotero-mcp` with the actual cloned directory.)

```json
{
  "mcpServers": {
    "zotero-mcp": {
      "command": "uv",
      "args": ["--directory", "path/to/zotero-mcp", "run", "main.py"]
    }
  }
}
```

## List of Provided Commands

- zotero_search_items: Search items by author name or title (excluding attachments, up to 30 results)
- zotero_get_item: Retrieve item details by item key
- zotero_read_pdf: Extract and convert the full text of PDF attachments from an item key

## Details of Each Command

- zotero_search_items: Performs a partial match search for author names or titles using the `q` parameter.
- zotero_get_item: Retrieves detailed information for the specified item using the `itemKey` parameter.
- zotero_read_pdf: Extracts and returns the full text of PDF attachments under the specified item using the `itemKey` parameter.

## License

Refer to the LICENSE file in this repository for license information.


