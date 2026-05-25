# Requirements

## v1 Requirements

### Environment & Foundation (ENV)

- [ ] **ENV-01**: 克隆 `arcgispro-py3` conda 环境为 `arcgis-agent`，安装额外依赖
- [ ] **ENV-02**: 创建项目骨架（src layout, pyproject.toml, entry points）
- [x] **ENV-03**: 创建 wrapper `.bat` 脚本，激活 proenv 后调用 CLI
- [ ] **ENV-04**: 环境检测模块，启动时验证 arcpy 可用性和许可证状态

### CLI Core (CLI)

- [x] **CLI-01**: Click 主命令组，支持 `--help`, `--version`, `--json`, `--verbose`, `--quiet`
- [x] **CLI-02**: 插件加载器，通过 `entry_points("arcgis_agent.commands")` 自动发现命令
- [ ] **CLI-03**: 统一 Result 模型（success/code/message/data/warnings），JSON 输出
- [x] **CLI-04**: 退出码语义明确（0=成功, 1=用户错误, 2=系统错误, 3=arcpy 错误）
- [x] **CLI-05**: 强制 UTF-8 stdout/stderr，pathlib 处理所有路径
- [x] **CLI-06**: 日志系统，`--verbose`/`--quiet` 控制级别，日志输出到 stderr

### Adapter Layer (ADP)

- [x] **ADP-01**: arcpy 封装接口（IGeoProcessor, IMapDocument, IDataAccessor）
- [x] **ADP-02**: 真实 ArcPy 实现（lazy import arcpy，构造函数内导入）
- [x] **ADP-03**: Mock 实现（用于单元测试，不需要 ArcGIS 许可证）
- [ ] **ADP-04**: Base Service 类，依赖注入 Adapter

### Workspace & Project (PROJ)

- [ ] **PROJ-01**: `workspace set <path>` — 设置当前工作空间
- [ ] **PROJ-02**: `workspace get` — 获取当前工作空间
- [ ] **PROJ-03**: `project info` — 查看当前工程信息（路径、GDB、地图列表）
- [ ] **PROJ-04**: `project create/open/save` — 创建/打开/保存工程

### Data Discovery (DISC)

- [ ] **DISC-01**: `data list` — 列出工作空间中的数据集（支持过滤）
- [ ] **DISC-02**: `data describe <path>` — 描述数据集元数据（类型、坐标系、记录数）
- [ ] **DISC-03**: `data fields <path>` — 列出字段信息（名称、类型、长度）
- [ ] **DISC-04**: `data extent <path>` — 获取空间范围（xmin/ymin/xmax/ymax）
- [ ] **DISC-05**: `data count <path>` — 获取记录数

### Data Management (MGMT)

- [ ] **MGMT-01**: `data copy <src> <dst>` — 复制数据集
- [ ] **MGMT-02**: `data delete <path>` — 删除数据集
- [ ] **MGMT-03**: `data rename <old> <new>` — 重命名数据集
- [ ] **MGMT-04**: `data convert <src> <dst> --format` — 格式转换（shp/gdb/csv/geojson）

### Geoprocessing (GEO)

- [ ] **GEO-01**: `data select <in> <out> --where` — 按属性选择
- [ ] **GEO-02**: `data clip <in> <clip> <out>` — 裁剪
- [ ] **GEO-03**: `data buffer <in> <out> --distance` — 缓冲区分析
- [ ] **GEO-04**: `data intersect <inputs> <out>` — 叠加求交
- [ ] **GEO-05**: `data union <inputs> <out>` — 叠加求并
- [ ] **GEO-06**: `data dissolve <in> <out> --field` — 融合
- [ ] **GEO-07**: `data spatial-join <target> <join> <out>` — 空间连接
- [ ] **GEO-08**: `data merge <inputs> <out>` — 合并
- [ ] **GEO-09**: `data project <in> <out> --sr` — 投影变换
- [ ] **GEO-10**: `analysis summary-stats <in> --field --stat` — 汇总统计

### Map Production (MAP)

- [ ] **MAP-01**: `map create <name>` — 创建新地图
- [ ] **MAP-02**: `map add-layer <map> <data>` — 添加图层
- [ ] **MAP-03**: `map remove-layer <map> <layer>` — 移除图层
- [ ] **MAP-04**: `map list-layers <map>` — 列出图层
- [ ] **MAP-05**: `map set-extent <map> --xmin --ymin --xmax --ymax` — 设置范围
- [ ] **MAP-06**: `map export <map> <out> --format --dpi` — 导出地图（PNG/PDF）
- [ ] **MAP-07**: `map symbolize <map> <layer> --type --field` — 符号化
- [ ] **MAP-08**: `map label <map> <layer> --field` — 设置标注
- [ ] **MAP-09**: `layout create <name>` — 创建布局
- [ ] **MAP-10**: `layout add-element <layout> <type> --params` — 添加元素
- [ ] **MAP-11**: `layout export <layout> <out> --format --dpi` — 导出布局

### MCP Server (MCP)

- [ ] **MCP-01**: FastMCP 服务器骨架，stdio 传输
- [ ] **MCP-02**: MCP 插件加载器，通过 entry points 注册工具
- [ ] **MCP-03**: 将所有 v1 CLI 命令暴露为 MCP 工具（带完整类型注解）
- [ ] **MCP-04**: 异步处理：`asyncio.to_thread()` + 序列化锁（arcpy 非线程安全）
- [ ] **MCP-05**: BrokenPipeError 优雅处理

## v2 Requirements (Deferred)

- [ ] 高级空间分析：热点分析、核密度、IDW、克里金
- [ ] 地形分析：坡度、坡向、视域、流域
- [ ] 网络分析：路径、服务区、最近设施
- [ ] 批量/管道操作：workflow 自动化
- [ ] 数据质量：validate、repair-geometry、simplify、smooth
- [ ] MapSeries：批量出图
- [ ] 布局模板、动态文本

## Out of Scope

- ArcGIS Server / Enterprise 远程服务管理 — 聚焦本地 ArcGIS Pro
- 实时数据流处理 — ArcGIS Pro 不适合
- 3D 分析（Scene） — 初期聚焦 2D
- 自定义 GP 工具开发 — 可通过 CLI 调用已有工具
- Deep learning inference — 太复杂，不适合 CLI
- 知识图谱操作 — 小众需求
- Geodatabase 版本管理 — Enterprise 专属

## Traceability

| Phase | Requirements |
|-------|--------------|
| Phase 0 | ENV-01, ENV-02, ENV-03 |
| Phase 1 | CLI-01~06, ADP-01~04, ENV-04 |
| Phase 2 | PROJ-01~03, DISC-01~05, MGMT-01~04 |
| Phase 3 | GEO-01~10 |
| Phase 4 | MAP-01~11 |
| Phase 5 | MCP-01~05 |
| Phase 6 | v2 requirements |

---
*Last updated: 2026-05-25 after research synthesis*
