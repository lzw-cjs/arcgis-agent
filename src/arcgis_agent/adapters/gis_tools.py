"""GIS tool definitions for LLM function calling (Phase 7).

Each tool follows the LangChain StructuredTool pattern with name,
description, and args_schema for JSON Schema generation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GISTool:
    """Minimal tool definition compatible with LangChain StructuredTool pattern."""

    name: str
    description: str
    args_schema: type | None = None


# ── Tool Definitions (34 tools covering 33+ requirement D-04) ──

ALL_GIS_TOOLS: list[GISTool] = [
    # Workspace
    GISTool("workspace_set", "设置 ArcGIS 工作空间目录"),
    GISTool("workspace_get", "获取当前工作空间路径"),

    # Data operations
    GISTool("data_list", "列出工作空间中的所有地理数据集"),
    GISTool("data_describe", "描述数据集的元数据（字段、空间参考、范围）"),
    GISTool("data_fields", "获取数据集的字段定义列表"),
    GISTool("data_extent", "获取数据集的空间范围"),
    GISTool("data_count", "获取数据集的要素/记录计数"),
    GISTool("data_copy", "复制数据集到新位置"),
    GISTool("data_delete", "删除指定的数据集"),
    GISTool("data_rename", "重命名数据集"),
    GISTool("data_convert", "在不同格式之间转换数据（SHP/GDB/CSV/GeoJSON）"),

    # Geoprocessing
    GISTool("gp_select", "按属性条件选择要素（SQL WHERE）"),
    GISTool("gp_clip", "用裁剪边界裁剪要素"),
    GISTool("gp_buffer", "创建要素周围的缓冲区"),
    GISTool("gp_intersect", "计算要素类的交集"),
    GISTool("gp_union", "计算多边形要素类的并集"),
    GISTool("gp_dissolve", "按字段融合要素，合并相邻多边形"),
    GISTool("gp_spatial_join", "空间连接：将连接要素的属性转移到目标要素"),
    GISTool("gp_merge", "将多个要素类合并为一个（追加，非叠加）"),
    GISTool("gp_project", "将要素投影到不同的坐标系"),

    # Map operations
    GISTool("map_create", "在 ArcGIS Pro 工程中创建新地图"),
    GISTool("map_add_layer", "向地图添加图层"),
    GISTool("map_remove_layer", "从地图中移除图层"),
    GISTool("map_list_layers", "列出地图中的所有图层及其属性"),
    GISTool("map_set_extent", "通过缩放到指定图层来设置地图范围"),
    GISTool("map_export", "将地图导出为图像或 PDF"),
    GISTool("map_symbolize", "对图层应用符号化（单一符号、唯一值或分级色彩）"),
    GISTool("map_label", "在图层上设置标注，包含字段表达式和样式"),

    # Layout operations
    GISTool("layout_create", "创建具有指定页面尺寸的新布局"),
    GISTool("layout_add_element", "向布局添加元素（文本、图例、比例尺、指北针、地图框、图片）"),
    GISTool("layout_export", "将布局导出为 PNG 或 PDF"),

    # Analysis
    GISTool("analysis_summary_stats", "计算要素类或表的汇总统计信息"),

    # Project
    GISTool("project_info", "获取当前 ArcGIS Pro 工程信息"),
]

# Set args_schema to a simple dict type for all tools
_GENERIC_SCHEMA: Any = dict
for _t in ALL_GIS_TOOLS:
    _t.args_schema = _GENERIC_SCHEMA
