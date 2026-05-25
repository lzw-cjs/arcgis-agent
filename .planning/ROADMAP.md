# arcgis-agent 路线图

## 概览

| 阶段 | 名称 | 需求 | 状态 |
|------|------|------|------|
| Phase 0 | 项目搭建 & 环境准备 | ENV-01~03 | ✅ 完成 |
| Phase 1 | CLI 基础框架 & 核心基础设施 | CLI-01~06, ADP-01~04, ENV-04 | ✅ 完成 |
| Phase 2 | 数据操作（发现 + 管理） | PROJ-01~03, DISC-01~05, MGMT-01~04 | ✅ 完成 |
| Phase 3 | 地理处理操作 | GEO-01~10 | 待执行 |
| Phase 4 | 地图生产 | MAP-01~11 | 待执行 |
| Phase 5 | MCP Server | MCP-01~05 | 待执行 |
| Phase 6 | 高级分析 (v1.1) | v2 requirements | 延后 |

---

## Phase 0: 项目搭建 & 环境准备

**目标:** 建立可重复的开发环境和项目骨架，为后续所有阶段打下基础。

**需求:** ENV-01, ENV-02, ENV-03

### 交付物

- [ ] 克隆 `arcgispro-py3` conda 环境为 `arcgis-agent`，安装额外依赖（click, mcp, rich, pydantic）
- [ ] 创建项目骨架（src layout, pyproject.toml, entry points 配置）
- [ ] 创建 wrapper `.bat` 脚本，激活 proenv 后调用 CLI
- [ ] `environment.yml` 文件，可重复创建环境

### 成功标准

- `conda activate arcgis-agent` 后 `import arcpy` 成功
- `pip install -e .` 安装项目成功
- `arcgis-agent --version` 输出版本号
- wrapper `.bat` 脚本从干净 CMD 窗口可运行

### 风险

| 风险 | 缓解措施 |
|------|----------|
| Conda 依赖冲突破坏 arcpy | 先克隆环境再安装，使用 `pip install --no-deps` |
| Esri 钉死的 numpy/pandas 被覆盖 | 安装前 pin 住关键包版本 |

### 计划

**Plans:** 3 plans

- [x] 00-01-PLAN.md — conda 环境克隆 + 依赖安装
- [ ] 00-02-PLAN.md — 项目骨架 + pyproject.toml
- [x] 00-03-PLAN.md — wrapper .bat 脚本

---

## Phase 1: CLI 基础框架 & 核心基础设施

**目标:** 搭建 CLI 框架、插件系统、统一输出模型和 Adapter 接口，使 `arcgis-agent --help` 可用。

**需求:** CLI-01~06, ADP-01~04, ENV-04

### 交付物

- [ ] Click 主命令组，支持 `--help`, `--version`, `--json`, `--verbose`, `--quiet`
- [ ] 插件加载器，通过 `entry_points("arcgis_agent.commands")` 自动发现命令
- [ ] 统一 Result 模型（success/code/message/data/warnings），JSON 输出
- [ ] 退出码语义明确（0=成功, 1=用户错误, 2=系统错误, 3=arcpy 错误）
- [ ] 强制 UTF-8 stdout/stderr，pathlib 处理所有路径
- [ ] 日志系统，`--verbose`/`--quiet` 控制级别，日志输出到 stderr
- [x] arcpy 封装接口（IGeoProcessor, IMapDocument, IDataAccessor）
- [x] 真实 ArcPy 实现（lazy import arcpy，构造函数内导入）
- [x] Mock 实现（用于单元测试，不需要 ArcGIS 许可证）
- [ ] Base Service 类，依赖注入 Adapter
- [ ] 环境检测模块，启动时验证 arcpy 可用性和许可证状态

### 成功标准

- `arcgis-agent --help` 显示命令帮助
- `arcgis-agent --version` 显示版本
- `arcgis-agent --json some-command` 输出合法 JSON
- 所有 stdout 输出为 JSON，所有日志/警告输出到 stderr
- 单元测试可在无 ArcGIS 许可证环境下运行（使用 Mock Adapter）
- 中文路径可正确处理

### 风险

| 风险 | 缓解措施 |
|------|----------|
| arcpy 导入失败（PITFALL #1） | 启动时检测，清晰错误信息，wrapper 脚本 |
| 编码问题（PITFALL #6/#7） | 强制 UTF-8，pathlib，`PYTHONUTF8=1` |
| 插件导入副作用（PITFALL #14） | 延迟导入，arcpy 仅在函数内 import |
| 许可证不可用（PITFALL #2） | 启动检测，CheckOutExtension/CheckInExtension + try/finally |

### 计划

**Plans:** 5 plans

- [ ] 01-01-PLAN.md — Result 模型 + 异常体系 + 退出码映射
- [x] 01-02-PLAN.md — CLI 框架 (Click group + 全局选项 + 插件加载 + 日志 + UTF-8)
- [x] 01-03-PLAN.md — Adapter 接口 + ArcPy 真实实现 + Mock 实现
- [x] 01-04-PLAN.md — BaseService 依赖注入 + 环境检测模块
- [ ] 01-05-PLAN.md — 全模块单元测试 (无 ArcGIS 许可证可运行)

---

## Phase 2: 数据操作（发现 + 管理）

**目标:** 实现数据发现和管理命令，让 Agent 能够了解和操作工作空间中的数据。

**需求:** PROJ-01~03, DISC-01~05, MGMT-01~04

### 交付物

- [x] `workspace set <path>` — 设置当前工作空间
- [x] `workspace get` — 获取当前工作空间
- [x] `project info` — 查看当前工程信息（路径、GDB、地图列表）
- [x] `data list` — 列出工作空间中的数据集（支持过滤）
- [x] `data describe <path>` — 描述数据集元数据（类型、坐标系、记录数）
- [x] `data fields <path>` — 列出字段信息（名称、类型、长度）
- [x] `data extent <path>` — 获取空间范围（xmin/ymin/xmax/ymax）
- [x] `data count <path>` — 获取记录数
- [x] `data copy <src> <dst>` — 复制数据集
- [x] `data delete <path>` — 删除数据集
- [x] `data rename <old> <new>` — 重命名数据集
- [x] `data convert <src> <dst> --format` — 格式转换（shp/gdb/csv/geojson）

### 成功标准

- Agent 可通过 `data list` 发现工作空间中的所有数据集
- `data describe` 返回完整的元数据 JSON（类型、坐标系、范围、字段）
- `data convert` 支持 shp/gdb/csv/geojson 格式互转
- 所有写操作有 `--no-overwrite` 安全选项
- 工作空间通过 `WorkspaceConfig` 持久化管理

### 风险

| 风险 | 缓解措施 |
|------|----------|
| GDB schema 锁（PITFALL #3） | 上下文管理器关闭 cursor，ClearWorkspaceCache |
| workspace 未设置（PITFALL #4） | WorkspaceConfig 持久化，命令显式检查 |

### 计划

**Plans:** 3 plans

- [x] 02-01-PLAN.md — Adapter 扩展 + WorkspaceConfig + workspace/project 命令
- [x] 02-02-PLAN.md — DataDiscoveryService + data list/describe/fields/extent/count 命令
- [x] 02-03-PLAN.md — DataManagementService + data copy/delete/rename/convert 命令 + 全模块测试

---

## Phase 3: 地理处理操作

**目标:** 实现核心空间分析命令，覆盖缓冲区、叠加、融合等常用 GIS 工作流。

**需求:** GEO-01~10

### 交付物

- [ ] `data select <in> <out> --where` — 按属性选择
- [ ] `data clip <in> <clip> <out>` — 裁剪
- [ ] `data buffer <in> <out> --distance` — 缓冲区分析
- [ ] `data intersect <inputs> <out>` — 叠加求交
- [ ] `data union <inputs> <out>` — 叠加求并
- [ ] `data dissolve <in> <out> --field` — 融合
- [ ] `data spatial-join <target> <join> <out>` — 空间连接
- [ ] `data merge <inputs> <out>` — 合并
- [ ] `data project <in> <out> --sr` — 投影变换
- [ ] `analysis summary-stats <in> --field --stat` — 汇总统计

### 成功标准

- 所有地理处理命令返回结构化 JSON（包含输出路径、要素数量、处理时间）
- 缓冲区支持多种单位（Meters, Kilometers, Feet, Miles）
- 叠加操作自动检查输入图层坐标系一致性
- 许可证扩展（如需要）使用 try/finally 模式

### 风险

| 风险 | 缓解措施 |
|------|----------|
| 许可证扩展不可用（PITFALL #2） | CheckOutExtension + try/finally |
| 投影不匹配（PITFALL #13） | 预检查 CRS，不一致时报错而非静默处理 |
| 大数据集内存溢出（PITFALL #12） | 操作前检查要素数量，使用 cursor 分页 |

### 计划

**Plans:** 4 plans

- [x] 03-01-PLAN.md — Adapter 层扩展 (IGeoProcessor + ArcPyGeoProcessor + MockGeoProcessor) + 共享 data_group
- [x] 03-02-PLAN.md — GeoprocessingService (GEO-01~09) + AnalysisService (GEO-10)
- [x] 03-03-PLAN.md — CLI 命令注册 (geoprocessing.py + analysis.py) + pyproject.toml 入口点
- [x] 03-04-PLAN.md — 全模块单元测试 (test_geoprocessing.py + test_analysis.py)

---

## Phase 4: 地图生产

**目标:** 实现地图创建、图层管理和导出命令，支持自动化地图出图。

**需求:** MAP-01~11

### 交付物

- [ ] `map create <name>` — 创建新地图
- [ ] `map add-layer <map> <data>` — 添加图层
- [ ] `map remove-layer <map> <layer>` — 移除图层
- [ ] `map list-layers <map>` — 列出图层
- [ ] `map set-extent <map> --xmin --ymin --xmax --ymax` — 设置范围
- [ ] `map export <map> <out> --format --dpi` — 导出地图（PNG/PDF）
- [ ] `map symbolize <map> <layer> --type --field` — 符号化
- [ ] `map label <map> <layer> --field` — 设置标注
- [ ] `layout create <name>` — 创建布局
- [ ] `layout add-element <layout> <type> --params` — 添加元素
- [ ] `layout export <layout> <out> --format --dpi` — 导出布局

### 成功标准

- `map create` + `map add-layer` + `map export` 完整流程可自动执行
- 导出支持 PNG/PDF 格式，可设置 DPI
- 布局支持添加标题、图例、比例尺等元素
- .aprx 文件操作使用 try/finally 确保释放锁

### 风险

| 风险 | 缓解措施 |
|------|----------|
| .aprx 锁冲突（PITFALL #10） | try/finally 释放，预检查锁文件，警告用户关闭 Pro GUI |

---

## Phase 5: MCP Server

**目标:** 将所有 CLI 命令暴露为 MCP 工具，供 Claude Code / Claude Desktop 直接调用。

**需求:** MCP-01~05

### 交付物

- [ ] FastMCP 服务器骨架，stdio 传输
- [ ] MCP 插件加载器，通过 entry points 注册工具
- [ ] 将所有 v1 CLI 命令暴露为 MCP 工具（带完整类型注解）
- [ ] 异步处理：`asyncio.to_thread()` + 序列化锁（arcpy 非线程安全）
- [ ] BrokenPipeError 优雅处理

### 成功标准

- `python -m arcgis_agent.mcp_server` 可启动 MCP server
- Claude Code 可通过 MCP 协议调用所有工具
- MCP 工具具有完整的类型注解和 JSON Schema
- 并发请求被序列化，不会导致 arcpy 崩溃
- 客户端断开时服务器优雅退出

### 风险

| 风险 | 缓解措施 |
|------|----------|
| arcpy 非线程安全（PITFALL #5） | asyncio.to_thread + 序列化锁，绝不使用 threading |
| stdio BrokenPipe（PITFALL #15） | 信号处理，try/except 包裹所有工具处理器 |
| 工具发现失败（PITFALL #16） | 完整类型注解，JSON 可序列化返回值 |

---

## Phase 6: 高级分析 (v1.1)

**目标:** 扩展高级空间分析能力，包括密度分析、地形分析和网络分析。

**需求:** v2 requirements

### 候选功能

- 热点分析、聚类分析
- 核密度、IDW、克里金插值
- 坡度、坡向、视域、流域分析
- 路径分析、服务区、最近设施
- 批量/管道操作
- 数据质量：validate、repair-geometry

**状态:** 延后至 v1.1，待核心功能稳定后规划。

---

## 依赖关系

```
Phase 0 → Phase 1 → Phase 2 → Phase 3
                               → Phase 4
                    → Phase 5 (依赖 Phase 2-4 的 Service 层)
                               → Phase 6 (依赖 Phase 3 的分析基础)
```

- Phase 0 是所有阶段的前置条件
- Phase 1 是所有功能阶段的前置条件
- Phase 2/3/4 可部分并行（共享 Adapter 层）
- Phase 5 在 Phase 2-4 完成后进行（复用 Service 层）
- Phase 6 在 Phase 3 基础上扩展

---

## 约束

- **平台:** 仅 Windows（ArcGIS Pro 限制）
- **Python:** 必须使用 ArcGIS Pro conda 环境（3.9-3.11）
- **依赖:** 核心仅依赖 arcpy，额外依赖最小化
- **许可证:** 需要 ArcGIS Pro 有效许可证
- **编码:** 强制 UTF-8，支持中文路径

---

*创建时间: 2026-05-25*
*基于: PROJECT.md, REQUIREMENTS.md, 研究文档（5 份）*
