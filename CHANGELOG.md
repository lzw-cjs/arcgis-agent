# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-26

### Added
- CLI tool with 7 command groups: workspace, project, data, geoprocessing, analysis, map, layout
- MCP Server exposing 31 tools via FastMCP (stdio transport)
- FastAPI REST API with 33 tool endpoints, chat SSE, and async task support
- React Web UI with chat panel, ArcGIS map integration, and tool call visualization
- LangChain AI integration supporting OpenAI-compatible providers
- ArcPy adapter layer with thread-safety (serialization lock + asyncio.to_thread)
- Mock adapter for testing without ArcGIS Pro license
- 248 unit tests passing, 16 E2E MCP tests passing
- Windows batch wrapper scripts for CLI and MCP Server