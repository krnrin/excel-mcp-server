"""GitHub Excel reading tools for the MCP server.

This module is imported after ``excel_mcp.server`` so that the FastMCP
instance ``mcp`` is already initialised. The ``@mcp.tool`` decorators below
register the tools at import time, so simply importing this module is
enough to expose them to MCP clients.
"""
import os
import logging
import tempfile
from typing import Optional

import requests
from mcp.types import ToolAnnotations

from excel_mcp.server import mcp

logger = logging.getLogger("excel-mcp")

RAW_BASE = "https://raw.githubusercontent.com"


def _convert_github_url_to_raw(github_url: str) -> str:
    """Convert a GitHub web URL to a raw.githubusercontent.com URL.

    Accepts either:
      - https://github.com/<owner>/<repo>/blob/<branch>/<path>
      - https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>
    """
    if "raw.githubusercontent.com" in github_url:
        return github_url
    if "github.com" in github_url:
        cleaned = github_url.replace("https://", "").replace("http://", "")
        cleaned = cleaned.replace("github.com/", "", 1)
        parts = cleaned.split("/blob/")
        if len(parts) == 2:
            repo_path = parts[0]
            branch_and_path = parts[1]
            return RAW_BASE + "/" + repo_path + "/" + branch_and_path
    raise ValueError("Invalid GitHub URL format: " + github_url)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Read Excel from GitHub",
        readOnlyHint=True,
    ),
)
def read_excel_from_github(
    github_url: str,
    sheet_name: str,
    start_cell: str = "A1",
    end_cell: Optional[str] = None,
    github_token: Optional[str] = None,
) -> str:
    """Read Excel data directly from a GitHub repository.

    Args:
        github_url: GitHub URL to the .xlsx file. Either a web URL
            (https://github.com/owner/repo/blob/main/data/file.xlsx) or a
            raw URL (https://raw.githubusercontent.com/owner/repo/main/data/file.xlsx).
        sheet_name: Name of the worksheet to read.
        start_cell: Starting cell (default A1).
        end_cell: Ending cell (optional; auto-expands if not provided).
        github_token: Optional GitHub personal access token, required for
            private repositories.

    Returns:
        JSON string containing structured cell data with metadata.
    """
    tmp_path = None
    try:
        raw_url = _convert_github_url_to_raw(github_url)
        headers = {"Authorization": "token " + github_token} if github_token else {}
        response = requests.get(raw_url, headers=headers, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        from excel_mcp.data import read_excel_range_with_metadata
        result = read_excel_range_with_metadata(
            tmp_path, sheet_name, start_cell, end_cell
        )
        if not result or not result.get("cells"):
            return "No data found in specified range"
        import json
        return json.dumps(result, indent=2, default=str)
    except requests.exceptions.RequestException as e:
        return "Error downloading file from GitHub: " + str(e)
    except ValueError as e:
        return "Error: " + str(e)
    except Exception as e:
        logger.error("Error reading from GitHub: %s", e)
        raise
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@mcp.tool(
    annotations=ToolAnnotations(
        title="List Sheets in GitHub Excel",
        readOnlyHint=True,
    ),
)
def list_sheets_from_github(
    github_url: str,
    github_token: Optional[str] = None,
) -> str:
    """List sheet names and dimensions for an Excel file on GitHub.

    Useful as a first step when you don't know the sheet names yet. Call this
    tool with the GitHub URL, then use ``read_excel_from_github`` with one of
    the returned sheet names.

    Args:
        github_url: GitHub web URL or raw URL to the .xlsx file.
        github_token: Optional GitHub PAT for private repositories.

    Returns:
        JSON string with workbook info (sheet names, dimensions, named ranges).
    """
    tmp_path = None
    try:
        raw_url = _convert_github_url_to_raw(github_url)
        headers = {"Authorization": "token " + github_token} if github_token else {}
        response = requests.get(raw_url, headers=headers, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        from excel_mcp.workbook import get_workbook_info
        result = get_workbook_info(tmp_path, include_ranges=True)
        import json
        return json.dumps(result, indent=2, default=str)
    except requests.exceptions.RequestException as e:
        return "Error downloading file from GitHub: " + str(e)
    except ValueError as e:
        return "Error: " + str(e)
    except Exception as e:
        logger.error("Error listing sheets from GitHub: %s", e)
        raise
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
