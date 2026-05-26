# Phase 4: 地图生产 - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

实现地图创建、图层管理、符号化、标注和导出命令，覆盖 MAP-01~11 全流程。地图操作（map 组）和布局操作（layout 组）为同级 CLI 命令组。支持三种符号化类型（Simple / UniqueValues / GraduatedColors）和六种布局元素。导出支持 PNG/PDF 格式。

</domain>

<decisions>
## Implementation Decisions

### 接口架构
- **D-01:** CLI 合并 + 底层接口分离 — IMapDocument (地图操作) + ILayoutDocument (布局操作)
- **D-02:** 图层引用：名称优先，fallback 到索引
- **D-03:** 范围设置：缩放至图层 (`--zoom-to LAYER`)，非四独立坐标选项
- **D-04:** 工程上下文：隐式 (`workspace set` 后自动查找 `.aprx`)
- **D-05:** ArcPy 连接：各自独立（每个 Adapter 管理自己的 aprx 连接）
- **D-06:** 锁管理：方法级 try/finally
- **D-07:** `list-layers` 输出：名称 + 数据源 + 要素数
- **D-08:** CLI 结构：`map` 和 `layout` 为同级命令组
  - `map create|add-layer|remove-layer|list-layers|set-extent|export|symbolize|label`
  - `layout create|add-element|export`

### 符号化设计
- **D-09:** 支持三种类型：Simple / UniqueValues / GraduatedColors
- **D-10:** Simple 参数：`--color R,G,B --outline-color R,G,B --size N --opacity 0-100`
- **D-11:** 颜色格式：R,G,B 逗号分隔（如 `255,0,0`），透明度单独 `--opacity 0-100`
- **D-12:** UniqueValues：单字段 `--field`；`--color-ramp` 自动分配 + `--values JSON` 手动覆盖
- **D-13:** GraduatedColors：分类方法 NaturalBreaks / Quantile / EqualInterval；分级 2-7，默认 5
- **D-14:** GraduatedColors 色带：`--color-ramp "Cyan to Purple"` 按名称字符串匹配
- **D-15:** GraduatedColors 轮廓：`--outline-color` 统一轮廓颜色
- **D-16:** 标注：字段 + 基本样式 (`--font-size, --color, --bold`)
- **D-17:** 不提供 `list-color-ramps` 命令，无默认色带

### 布局元素
- **D-18:** 支持 6 种元素：text, legend, scale-bar, north-arrow, map-frame, image
- **D-19:** 定位方式：预设位置 + XY坐标 (`--position top-left|...` + `--params "x=1.0,y=2.0,width=6.0,height=0.5"`)
- **D-20:** 文本参数：`text=My Map,font_size=24,color=0,0,0,bold=true,italic=false`
- **D-21:** 图例参数：`title=Legend` (内容自动从图层符号化生成)
- **D-22:** 比例尺参数：`style=Alternating|Bar|DoubleAlternating`
- **D-23:** 指北针参数：`style=Default|Arrow`
- **D-24:** MapFrame 参数：`map=Map1,extent=full_extent|current_view`
- **D-25:** Image 参数：`source=path/to/logo.png`
- **D-26:** 页面尺寸：`--page-size A4|A3|Letter|Tabloid` + `--orientation portrait|landscape`
- **D-27:** 元素参数格式：key=value 对（逗号分隔在 --params 内）

### 导出
- **D-28:** 导出格式：PNG + PDF
- **D-29:** `map export` 和 `layout export` 为独立命令
- **D-30:** DPI：固定选项 96|150|300|600，默认 300
- **D-31:** PNG 支持 `--transparent` 透明背景标志

### Claude's Discretion
- Adapter 接口方法的具体签名（IMapDocument.symbolize_layer, ILayoutDocument 方法定义）
- ArcPyMapDocument 和 MockMapDocument 的实现细节
- Service 层分拆粒度（MapService, LayoutService）
- CLI 命令参数验证逻辑
- 单元测试用例设计

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目架构
- `.planning/PROJECT.md` — 四层架构定义、插件设计、约束条件
- `.planning/REQUIREMENTS.md` — MAP-01~11 完整需求定义
- `.planning/ROADMAP.md` — Phase 4 交付物和成功标准

### 已有实现（直接扩展）
- `src/arcgis_agent/adapters/base.py` — IMapDocument 接口（已有 create_map/add_layer/export_map，需新增）
- `src/arcgis_agent/adapters/arcpy_adapter.py` — ArcPyMapDocument 实现（需扩展符号化/布局方法）
- `src/arcgis_agent/adapters/mock_adapter.py` — MockMapDocument（需同步扩展）

### ArcPy API 参考
- arcpy.mp Symbology 类 — `symbology.updateRenderer()` / `symbology.renderer` 模式
- arcpy.mp Layout 类 — `project.createLayout()` / `layout.listElements()`

### Phase 3 决策（继承模式）
- `.planning/phases/03-geoprocessing/03-CONTEXT.md` — 四层架构模式、错误码规范、测试隔离策略

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `IMapDocument` 接口：已有 create_map/add_layer/export_map，需新增 symbolize_layer/remove_layer/list_layers/set_extent/set_label
- `ILayoutDocument` 接口：待新建，方法 create_layout/add_element/export_layout
- `Result.ok()` / `Result.from_exception()`：标准返回模式
- `BaseService`：依赖注入模式

### Established Patterns
- ArcPy lazy import（构造函数内导入，非模块级）
- 方法级 try/finally 管理 aprx 锁
- 错误码格式：MAP_<OP>_FAILED / LAYOUT_<OP>_FAILED
- 测试用 Mock Adapter，不需要 ArcGIS 许可证

### Integration Points
- `pyproject.toml` entry_points：需新增 `map` 和 `layout` 命令入口
- CLI 端创建 `src/arcgis_agent/commands/map.py` 和 `layout.py`
- Service 端创建 `src/arcgis_agent/services/map_service.py` 和 `layout_service.py`

</code_context>

<specifics>
## Specific Ideas

- `map symbolize` 的 CLI 结构：`map symbolize <map_name> <layer_name> --type simple|unique|graduated --field FIELD [其他类型相关参数]`
- UniqueValues 的 `--values` JSON 格式：`'[{"value":"A","color":"255,0,0","size":5}]'`
- 布局元素的 `--params` 使用逗号分隔的 key=value 字符串
- 色带匹配使用模糊搜索（`project.listColorRamps()` 的部分名称匹配）

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 4-地图生产*
*Context gathered: 2026-05-26*
