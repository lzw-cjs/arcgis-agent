# Phase 3: 地理处理操作 - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

实现 10 个核心空间分析命令（GEO-01~10），覆盖缓冲区、叠加、融合、裁剪、空间连接、投影变换和汇总统计等常用 GIS 工作流。所有命令遵循四层架构（Entry → Command → Service → Adapter），返回结构化 JSON。

</domain>

<decisions>
## Implementation Decisions

### CLI 命令分组
- **D-01:** GEO-01~09 放在 `data` 组（如 `data buffer`、`data clip`），新建 `geoprocessing.py` 命令文件
- **D-02:** GEO-10 放在 `analysis` 组（`analysis summary-stats`），新建 `analysis.py` 命令文件
- **D-03:** 新建 `data_group.py` 共享 Click 子组定义，解决 data.py 和 geoprocessing.py 的组冲突问题
- **D-04:** 取消注释 pyproject.toml 中的 `analysis` entry point

### 缓冲区单位设计
- **D-05:** 支持完整 ArcPy 单位：Meters, Kilometers, Feet, Miles, Yards, DecimalDegrees
- **D-06:** CLI 格式为 `--distance 100 --unit Meters`（分开参数，非字符串格式）
- **D-07:** 支持 `--dissolve-field` 参数，按指定字段融合重叠缓冲区
- **D-08:** 不支持 side type（FULL/LEFT/RIGHT）和 end type（ROUND/FLAT）高级选项

### 多输入操作设计
- **D-09:** 多输入使用逗号分隔：`data intersect a.shp,b.shp,c.shp out.shp`
- **D-10:** 叠加操作（intersect/union）预检查输入图层坐标系一致性，不一致时报错（PITFALL #13）
- **D-11:** 所有操作返回标准三要素：输出路径、输出要素数量、处理时间
- **D-12:** 多输入操作最少需要 2 个输入图层

### 汇总统计设计
- **D-13:** 支持完整 ArcPy 统计类型：SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN
- **D-14:** 多字段语法：`--field pop:SUM,area:MEAN`（字段名:统计类型，逗号分隔）
- **D-15:** 支持 `--case-field` 参数，按指定字段分组后分别统计

### CRS 检查降级策略
- **D-16:** 当 ArcPy 不可用时，坐标系一致性检查报错退出（不允许跳过检查，安全优先）

### 依赖声明
- **D-17:** ArcPy 为可选依赖，需手动配置 ArcGIS 环境。在 pyproject.toml 中备注说明，避免其他协作者安装时报错

### Claude's Discretion
- Adapter 方法的具体签名和内部实现
- Mock Adapter 的模拟行为细节
- 单元测试的组织方式和覆盖范围
- 错误码命名（沿用 GP_<TOOL>_FAILED 模式）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目架构
- `.planning/PROJECT.md` — 四层架构定义、插件设计、约束条件
- `.planning/REQUIREMENTS.md` — GEO-01~10 完整需求定义
- `.planning/ROADMAP.md` — Phase 3 交付物和成功标准

### 已有实现（模式参考）
- `src/arcgis_agent/adapters/base.py` — IGeoProcessor 接口（已有 buffer/clip/intersect）
- `src/arcgis_agent/adapters/arcpy_adapter.py` — ArcPyGeoProcessor 实现模式
- `src/arcgis_agent/adapters/mock_adapter.py` — MockGeoProcessor 模式
- `src/arcgis_agent/services/base.py` — BaseService 依赖注入
- `src/arcgis_agent/services/data_management.py` — Pattern A（完整 BaseService）参考
- `src/arcgis_agent/commands/data.py` — CLI 命令注册和服务创建模式

### Phase 2 决策（继承）
- `.planning/phases/02-data-operations/CONTEXT.md` — 架构决策、Pitfall 处理、测试模式

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `IGeoProcessor` 接口：已定义 buffer/clip/intersect 3 个方法，需扩展 7 个新方法
- `BaseService`：支持 `self._gp`（IGeoProcessor）和 `self._data`（IDataAccessor）注入
- `Result.ok()` / `Result.from_exception()`：标准返回模式
- `WorkspaceConfig`：工作空间路径解析

### Established Patterns
- 服务类继承 BaseService，构造函数 lazy import arcpy
- CLI 命令在函数内 import 服务（延迟导入）
- 错误码格式：GP_<TOOL>_FAILED
- 测试用 Mock Adapter，不需要 ArcGIS 许可证

### Integration Points
- `pyproject.toml` entry_points：需新增 `geoprocessing` 和取消注释 `analysis`
- `data_group.py`：新建共享 Click 子组，data.py 和 geoprocessing.py 都向它注册

</code_context>

<specifics>
## Specific Ideas

- 所有地理处理命令统一使用 `--no-overwrite` 安全选项（与 Phase 2 一致）
- 缓冲区的 `--dissolve-field` 对应 ArcPy Buffer 工具的 dissolve_field 参数
- 汇总统计的输出为表格形式的 JSON（每行一个分组的统计结果）

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 3-地理处理操作*
*Context gathered: 2026-05-26*
