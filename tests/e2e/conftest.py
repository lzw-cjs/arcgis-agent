"""Shared fixtures for MCP E2E tests.

Provides MCP ClientSession fixtures via stdio transport and workspace
management for end-to-end validation of the 33 MCP tools.

Usage:
    pytest tests/e2e/test_mcp_tools.py -v
    pytest tests/e2e/test_chat_loop.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ── Helpers ──────────────────────────────────────────────────────

def _require_mcp():
    """Skip tests if MCP SDK is not available."""
    try:
        import mcp  # noqa: F401
    except ImportError:
        pytest.skip("mcp SDK not available")


def _require_arcpy():
    """Skip tests if arcpy is not available (requires ArcGIS Pro conda environment)."""
    try:
        import arcpy  # noqa: F401
    except ImportError:
        pytest.skip("arcpy not available (requires ArcGIS Pro conda environment)")


# ── MCP ClientSession Fixture ───────────────────────────────────

@pytest.fixture
async def mcp_session():
    """Create an MCP ClientSession connected to arcgis-agent-mcp via stdio.

    Starts the MCP server as a subprocess, connects via stdio transport,
    and yields an initialized ClientSession. The server is automatically
    terminated when the fixture is torn down.

    Requires: mcp SDK installed (pip install mcp).
    """
    _require_mcp()

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "arcgis_agent.mcp_server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# ── Tool Discovery ──────────────────────────────────────────────

@pytest.fixture
async def mcp_tools(mcp_session: ClientSession):
    """List all available MCP tools from the connected server.

    Returns a dict mapping tool name -> Tool object for easy lookup.
    """
    result = await mcp_session.list_tools()
    return {tool.name: tool for tool in result.tools}


# ── Test Workspace Fixture ──────────────────────────────────────

@pytest.fixture(scope="module")
def e2e_workspace():
    """Module-scope workspace for MCP E2E tests.

    Creates a temporary workspace directory for test data. Cleaned up
    automatically unless KEEP_TEST_OUTPUT=1 is set in the environment.
    """
    _require_arcpy()
    ws = Path("./test_e2e_workspace")
    ws.mkdir(exist_ok=True)
    yield ws
    # Cleanup unless KEEP_TEST_OUTPUT=1
    if os.environ.get("KEEP_TEST_OUTPUT") != "1":
        import shutil
        shutil.rmtree(str(ws), ignore_errors=True)
