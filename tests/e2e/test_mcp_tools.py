"""MCP E2E tests: verify all 33 tools are callable via MCP protocol.

Run with: pytest tests/e2e/test_mcp_tools.py -v

These tests connect to the MCP server via stdio transport and verify:
1. All 33 required tools are registered with correct names (D-29)
2. Every tool has a description and inputSchema
3. Key tools have the correct parameter schema (input validation)

Note: Most tests are inspection-only (verify tool exists and accepts params).
Execution tests that require arcpy are in test_e2e_english_path.py.
"""
from __future__ import annotations

import pytest
from mcp import ClientSession

pytestmark = pytest.mark.anyio

# ═══════════════════════════════════════════════════════════════
# Tool Registration Tests
# ═══════════════════════════════════════════════════════════════


class TestToolDiscovery:
    """Verify all expected tools are registered in the MCP server."""

    REQUIRED_TOOLS = [
        # Workspace (2)
        "workspace_set", "workspace_get",
        # Project (1)
        "project_info",
        # Data Discovery (5)
        "data_list", "data_describe", "data_fields", "data_extent", "data_count",
        # Data Management (4)
        "data_copy", "data_delete", "data_rename", "data_convert",
        # Geoprocessing (9)
        "gp_select", "gp_clip", "gp_buffer", "gp_intersect",
        "gp_union", "gp_dissolve", "gp_spatial_join", "gp_merge", "gp_project",
        # Analysis (1)
        "analysis_summary_stats",
        # Map (8)
        "map_create", "map_add_layer", "map_remove_layer", "map_list_layers",
        "map_set_extent", "map_export", "map_symbolize", "map_label",
        # Layout (3)
        "layout_create", "layout_add_element", "layout_export",
    ]

    async def test_all_tools_registered(self, mcp_tools):
        """Verify all 33 required tools are available (D-29)."""
        for tool_name in self.REQUIRED_TOOLS:
            assert tool_name in mcp_tools, f"Missing tool: {tool_name}"
        assert len(mcp_tools) >= len(self.REQUIRED_TOOLS), (
            f"Expected >= {len(self.REQUIRED_TOOLS)} tools, got {len(mcp_tools)}"
        )

    async def test_tool_has_description(self, mcp_tools):
        """Verify every tool has a description string."""
        for name, tool in mcp_tools.items():
            assert tool.description, (
                f"Tool '{name}' has no description"
            )

    async def test_tool_has_input_schema(self, mcp_tools):
        """Verify every tool has an inputSchema (JSON Schema)."""
        for name, tool in mcp_tools.items():
            assert tool.inputSchema is not None, (
                f"Tool '{name}' has no input schema"
            )


# ═══════════════════════════════════════════════════════════════
# Workspace Tools (2)
# ═══════════════════════════════════════════════════════════════


class TestWorkspaceTools:
    """Tests for workspace_set and workspace_get."""

    async def test_workspace_set_schema(self, mcp_tools):
        """workspace_set must have a 'path' parameter."""
        tool = mcp_tools["workspace_set"]
        props = tool.inputSchema.get("properties", {})
        assert "path" in props, "workspace_set must have 'path' parameter"

    async def test_workspace_get_schema(self, mcp_tools):
        """workspace_get must exist (no required params)."""
        tool = mcp_tools["workspace_get"]
        assert tool.name == "workspace_get"


# ═══════════════════════════════════════════════════════════════
# Project Tools (1)
# ═══════════════════════════════════════════════════════════════


class TestProjectTools:
    """Tests for project_info."""

    async def test_project_info_schema(self, mcp_tools):
        """project_info must have a 'project_path' parameter."""
        tool = mcp_tools["project_info"]
        props = tool.inputSchema.get("properties", {})
        assert "project_path" in props, (
            "project_info must have 'project_path' parameter"
        )


# ═══════════════════════════════════════════════════════════════
# Data Discovery Tools (5)
# ═══════════════════════════════════════════════════════════════


class TestDataDiscoveryTools:
    """Tests for data_list, data_describe, data_fields, data_extent, data_count."""

    async def test_data_list_schema(self, mcp_tools):
        """data_list must exist and have optional filter params."""
        tool = mcp_tools["data_list"]
        assert tool.inputSchema is not None

    async def test_data_describe_schema(self, mcp_tools):
        """data_describe must have 'path' parameter."""
        tool = mcp_tools["data_describe"]
        props = tool.inputSchema.get("properties", {})
        param_names = list(props.keys())
        assert len(param_names) >= 1, "data_describe must have at least one parameter"
        assert "path" in props, (
            f"data_describe must have 'path' parameter, got: {param_names}"
        )

    async def test_data_fields_schema(self, mcp_tools):
        """data_fields must have 'path' parameter."""
        tool = mcp_tools["data_fields"]
        props = tool.inputSchema.get("properties", {})
        assert "path" in props, "data_fields must have 'path' parameter"

    async def test_data_extent_schema(self, mcp_tools):
        """data_extent must have 'path' parameter."""
        tool = mcp_tools["data_extent"]
        props = tool.inputSchema.get("properties", {})
        assert "path" in props, "data_extent must have 'path' parameter"

    async def test_data_count_schema(self, mcp_tools):
        """data_count must have 'path' parameter."""
        tool = mcp_tools["data_count"]
        props = tool.inputSchema.get("properties", {})
        assert "path" in props, "data_count must have 'path' parameter"


# ═══════════════════════════════════════════════════════════════
# Data Management Tools (4)
# ═══════════════════════════════════════════════════════════════


class TestDataManagementTools:
    """Tests for data_copy, data_delete, data_rename, data_convert."""

    @pytest.mark.parametrize("tool_name", [
        "data_copy", "data_delete", "data_rename", "data_convert",
    ])
    async def test_data_mgmt_tool_exists(self, mcp_tools, tool_name):
        """Each data management tool must be registered."""
        assert tool_name in mcp_tools, f"Missing tool: {tool_name}"

    async def test_data_copy_schema(self, mcp_tools):
        """data_copy must have source and destination params."""
        tool = mcp_tools["data_copy"]
        props = tool.inputSchema.get("properties", {})
        assert "source" in props, "data_copy must have 'source' parameter"
        assert "destination" in props, "data_copy must have 'destination' parameter"

    async def test_data_convert_schema(self, mcp_tools):
        """data_convert must have source, destination, and output_format params."""
        tool = mcp_tools["data_convert"]
        props = tool.inputSchema.get("properties", {})
        assert "source" in props, "data_convert must have 'source' parameter"
        assert "destination" in props, "data_convert must have 'destination' parameter"
        assert "output_format" in props, "data_convert must have 'output_format' parameter"


# ═══════════════════════════════════════════════════════════════
# Geoprocessing Tools (9)
# ═══════════════════════════════════════════════════════════════


class TestGeoprocessingTools:
    """Tests for gp_select, gp_clip, gp_buffer, gp_intersect, gp_union,
    gp_dissolve, gp_spatial_join, gp_merge, gp_project."""

    @pytest.mark.parametrize("tool_name", [
        "gp_select", "gp_clip", "gp_buffer", "gp_intersect",
        "gp_union", "gp_dissolve", "gp_spatial_join", "gp_merge", "gp_project",
    ])
    async def test_geoprocessing_tool_exists(self, mcp_tools, tool_name):
        """Each geoprocessing tool must be registered."""
        assert tool_name in mcp_tools, f"Missing tool: {tool_name}"

    async def test_gp_buffer_parameter_validation(self, mcp_tools):
        """gp_buffer must have input_fc, output_fc, distance, and unit params."""
        tool = mcp_tools["gp_buffer"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "gp_buffer must have 'input_fc' parameter"
        assert "output_fc" in props, "gp_buffer must have 'output_fc' parameter"
        assert "distance" in props, "gp_buffer must have 'distance' parameter"
        assert "unit" in props, "gp_buffer must have 'unit' parameter"

    async def test_gp_clip_parameter_validation(self, mcp_tools):
        """gp_clip must have input_fc, clip_features, and output_fc params."""
        tool = mcp_tools["gp_clip"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "gp_clip must have 'input_fc' parameter"
        assert "clip_features" in props, "gp_clip must have 'clip_features' parameter"
        assert "output_fc" in props, "gp_clip must have 'output_fc' parameter"

    async def test_gp_intersect_parameter_validation(self, mcp_tools):
        """gp_intersect must have inputs (list) and output_fc params."""
        tool = mcp_tools["gp_intersect"]
        props = tool.inputSchema.get("properties", {})
        assert "inputs" in props, "gp_intersect must have 'inputs' parameter"
        assert "output_fc" in props, "gp_intersect must have 'output_fc' parameter"

    async def test_gp_select_parameter_validation(self, mcp_tools):
        """gp_select must have input_fc, output_fc, and where_clause params."""
        tool = mcp_tools["gp_select"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "gp_select must have 'input_fc' parameter"
        assert "output_fc" in props, "gp_select must have 'output_fc' parameter"
        assert "where_clause" in props, "gp_select must have 'where_clause' parameter"

    async def test_gp_union_parameter_validation(self, mcp_tools):
        """gp_union must have inputs (list) and output_fc params."""
        tool = mcp_tools["gp_union"]
        props = tool.inputSchema.get("properties", {})
        assert "inputs" in props, "gp_union must have 'inputs' parameter"
        assert "output_fc" in props, "gp_union must have 'output_fc' parameter"

    async def test_gp_dissolve_parameter_validation(self, mcp_tools):
        """gp_dissolve must have input_fc, output_fc, and dissolve_field params."""
        tool = mcp_tools["gp_dissolve"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "gp_dissolve must have 'input_fc' parameter"
        assert "output_fc" in props, "gp_dissolve must have 'output_fc' parameter"
        assert "dissolve_field" in props, "gp_dissolve must have 'dissolve_field' parameter"

    async def test_gp_spatial_join_parameter_validation(self, mcp_tools):
        """gp_spatial_join must have target_fc, join_fc, and output_fc params."""
        tool = mcp_tools["gp_spatial_join"]
        props = tool.inputSchema.get("properties", {})
        assert "target_fc" in props, "gp_spatial_join must have 'target_fc' parameter"
        assert "join_fc" in props, "gp_spatial_join must have 'join_fc' parameter"
        assert "output_fc" in props, "gp_spatial_join must have 'output_fc' parameter"

    async def test_gp_merge_parameter_validation(self, mcp_tools):
        """gp_merge must have inputs (list) and output_fc params."""
        tool = mcp_tools["gp_merge"]
        props = tool.inputSchema.get("properties", {})
        assert "inputs" in props, "gp_merge must have 'inputs' parameter"
        assert "output_fc" in props, "gp_merge must have 'output_fc' parameter"

    async def test_gp_project_parameter_validation(self, mcp_tools):
        """gp_project must have input_fc, output_fc, and spatial_ref_wkid params."""
        tool = mcp_tools["gp_project"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "gp_project must have 'input_fc' parameter"
        assert "output_fc" in props, "gp_project must have 'output_fc' parameter"
        assert "spatial_ref_wkid" in props, "gp_project must have 'spatial_ref_wkid' parameter"


# ═══════════════════════════════════════════════════════════════
# Map Tools (8)
# ═══════════════════════════════════════════════════════════════


class TestMapTools:
    """Tests for map_create, map_add_layer, map_remove_layer, map_list_layers,
    map_set_extent, map_export, map_symbolize, map_label."""

    @pytest.mark.parametrize("tool_name", [
        "map_create", "map_add_layer", "map_remove_layer", "map_list_layers",
        "map_set_extent", "map_export", "map_symbolize", "map_label",
    ])
    async def test_map_tool_exists(self, mcp_tools, tool_name):
        """Each map tool must be registered."""
        assert tool_name in mcp_tools, f"Missing tool: {tool_name}"

    async def test_map_export_schema(self, mcp_tools):
        """map_export must have map_name, output_path, and project_path params."""
        tool = mcp_tools["map_export"]
        props = tool.inputSchema.get("properties", {})
        assert "map_name" in props, "map_export must have 'map_name' parameter"
        assert "output_path" in props, "map_export must have 'output_path' parameter"
        assert "project_path" in props, "map_export must have 'project_path' parameter"

    async def test_map_symbolize_schema(self, mcp_tools):
        """map_symbolize must have map_name, layer_name, and project_path params."""
        tool = mcp_tools["map_symbolize"]
        props = tool.inputSchema.get("properties", {})
        assert "map_name" in props, "map_symbolize must have 'map_name' parameter"
        assert "layer_name" in props, "map_symbolize must have 'layer_name' parameter"
        assert "project_path" in props, "map_symbolize must have 'project_path' parameter"

    async def test_map_create_schema(self, mcp_tools):
        """map_create must have map_name param."""
        tool = mcp_tools["map_create"]
        props = tool.inputSchema.get("properties", {})
        assert "map_name" in props, "map_create must have 'map_name' parameter"

    async def test_map_label_schema(self, mcp_tools):
        """map_label must have map_name, layer_name, field, and project_path params."""
        tool = mcp_tools["map_label"]
        props = tool.inputSchema.get("properties", {})
        assert "map_name" in props, "map_label must have 'map_name' parameter"
        assert "layer_name" in props, "map_label must have 'layer_name' parameter"
        assert "field" in props, "map_label must have 'field' parameter"
        assert "project_path" in props, "map_label must have 'project_path' parameter"


# ═══════════════════════════════════════════════════════════════
# Layout Tools (3)
# ═══════════════════════════════════════════════════════════════


class TestLayoutTools:
    """Tests for layout_create, layout_add_element, layout_export."""

    @pytest.mark.parametrize("tool_name", [
        "layout_create", "layout_add_element", "layout_export",
    ])
    async def test_layout_tool_exists(self, mcp_tools, tool_name):
        """Each layout tool must be registered."""
        assert tool_name in mcp_tools, f"Missing tool: {tool_name}"

    async def test_layout_create_schema(self, mcp_tools):
        """layout_create must have layout_name and project_path params."""
        tool = mcp_tools["layout_create"]
        props = tool.inputSchema.get("properties", {})
        assert "layout_name" in props, "layout_create must have 'layout_name' parameter"
        assert "project_path" in props, "layout_create must have 'project_path' parameter"

    async def test_layout_export_schema(self, mcp_tools):
        """layout_export must have layout_name, output_path, and project_path params."""
        tool = mcp_tools["layout_export"]
        props = tool.inputSchema.get("properties", {})
        assert "layout_name" in props, "layout_export must have 'layout_name' parameter"
        assert "output_path" in props, "layout_export must have 'output_path' parameter"
        assert "project_path" in props, "layout_export must have 'project_path' parameter"

    async def test_layout_add_element_schema(self, mcp_tools):
        """layout_add_element must have layout_name, element_type, and project_path params."""
        tool = mcp_tools["layout_add_element"]
        props = tool.inputSchema.get("properties", {})
        assert "layout_name" in props, "layout_add_element must have 'layout_name' parameter"
        assert "element_type" in props, "layout_add_element must have 'element_type' parameter"
        assert "project_path" in props, "layout_add_element must have 'project_path' parameter"


# ═══════════════════════════════════════════════════════════════
# Analysis Tools (1)
# ═══════════════════════════════════════════════════════════════


class TestAnalysisTools:
    """Tests for analysis_summary_stats."""

    async def test_analysis_summary_stats_exists(self, mcp_tools):
        """analysis_summary_stats must be registered."""
        assert "analysis_summary_stats" in mcp_tools, "Missing tool: analysis_summary_stats"

    async def test_analysis_summary_stats_schema(self, mcp_tools):
        """analysis_summary_stats must have input_fc, field_spec, and optional params."""
        tool = mcp_tools["analysis_summary_stats"]
        props = tool.inputSchema.get("properties", {})
        assert "input_fc" in props, "analysis_summary_stats must have 'input_fc' parameter"
        assert "field_spec" in props, "analysis_summary_stats must have 'field_spec' parameter"
