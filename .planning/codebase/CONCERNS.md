# 已知问题与技术债

**分析日期：** 2026-05-27

## 严重问题

### arcpy.mp 中文路径静默失败

**位置：** `src/arcgis_agent/adapters/arcpy_adapter.py`、`src/arcgis_agent/services/map_service.py`、`src/arcgis_agent/services/layout_service.py`
**严重性：** 高
**描述：** arcpy.mp 操作在中文用户名路径的系统上会静默失败或抛出编码错误。代码捕获异常并记录警告，但不阻止用户尝试这些操作。8处 `aprx.save()` 错误被静默吞掉。
**影响：** 地图和布局功能在中文用户名系统上完全不可用。
**建议：** 检测中文路径并在这些操作前警告用户；在文档中记录此限制；在纯英文路径机器上验证。

### 无 API 认证

**位置：** `src/arcgis_agent/api/main.py`
**严重性：** 高
**描述：** REST API 没有 authentication/authorization 机制。任何可以访问 `localhost:8000` 的人都可以执行 GIS 操作、访问 LLM 提供商和操作文件。
**影响：** 在本地开发中风险较低，但在共享/网络环境中会很危险。
**建议：** 为 API 端点添加 API 密钥认证；实施速率限制。

### 上传路径未净化

**位置：** `src/arcgis_agent/api/routes/upload.py`
**严重性：** 高
**描述：** 上传的文件路径可能未正确净化，可能导致目录遍历攻击。用户可能上传带有 `../` 的文件名来逃逸上传目录。
**影响：** 可能通过文件上传暴露任意文件系统访问。
**建议：** 清理文件名，验证路径在上传目录内，拒绝可疑路径。

## 安全问题

### CORS 硬编码 localhost

**位置：** `src/arcgis_agent/api/main.py`
**严重性：** 中
**描述：** CORS 配置硬编码为 `http://localhost:5173`，不允许其他来源。无环境配置。
**影响：** 无法从其他域访问 API；阻止生产部署。
**建议：** 从环境变量配置 CORS 来源。

### 无速率限制

**位置：** `src/arcgis_agent/api/routes/`
**严重性：** 中
**描述：** 没有速率限制机制。用户可以无限调用 LLM 提供商和 GIS 工具。
**影响：** LLM API 成本失控；潜在的 DoS。
**建议：** 实施每个端点的速率限制，特别是聊天和工具执行。

### LLM API 密钥仅环境变量

**位置：** `src/arcgis_agent/config.py`
**严重性：** 低
**描述：** LLM API 密钥仅从环境变量加载。没有加密存储、密钥轮换或审计。
**影响：** 如果环境被攻破，密钥可能泄露。
**建议：** 考虑加密配置存储；添加密钥轮换机制。

## 性能问题

### SSE 流人为延迟

**位置：** `src/arcgis_agent/api/routes/chat.py`
**严重性：** 低
**描述：** SSE 流式传输中每个块有 10ms 的 `await asyncio.sleep()`。这是为了速率控制而添加的，但不必要地减慢了响应速度。
**影响：** 聊天响应感知延迟增加。
**建议：** 移除或减少睡眠时间；仅在需要时进行速率控制。

### 内存对话存储

**位置：** `src/arcgis_agent/api/dependencies.py`
**严重性：** 中
**描述：** 对话历史存储在内存中（`ConversationStore`），使用 `OrderedDict` LRU 淘汰（最多 100 个会话）。服务器重启时所有对话历史丢失。
**影响：** 重启丢失对话上下文；长对话的内存使用增长。
**建议：** 持久化对话历史到 SQLite 或文件；添加基于大小的淘汰。

### 无连接池

**位置：** `src/arcgis_agent/adapters/llm.py`
**严重性：** 低
**描述：** 每次聊天请求都会创建一个新的 LLM 客户端实例，没有连接重用。
**影响：** 由于 TLS 握手开销，首次 token 延迟增加。
**建议：** 缓存和重用 LLM 客户端实例。

## 代码质量问题

### 大型单体文件

**位置：** `src/arcgis_agent/adapters/arcpy_adapter.py`、`src/arcgis_agent/services/map_service.py`
**严重性：** 低
**描述：** 一些文件非常大（500+ 行），将多个关注点组合在一起。
**影响：** 更难维护和测试。
**建议：** 考虑按领域拆分大文件。

### 工具定义中的重复代码

**位置：** `src/arcgis_agent/adapters/gis_tools.py`、`src/arcgis_agent/api/routes/tools.py`、`src/arcgis_agent/mcp_server.py`
**严重性：** 中
**描述：** 33 个 GIS 工具在三个地方定义：LangChain 工具、REST 路由和 MCP 工具。每个工具的模式和描述必须手动保持同步。
**影响：** 添加新工具时容易遗漏同步更新。
**建议：** 从单一来源生成工具定义；创建共享的工具注册表。

### 混合中英文文档字符串

**位置：** 多个文件
**严重性：** 低
**描述：** API 文档字符串混合了中文和英文文本，导致编码问题和不一致的 OpenAPI 文档。
**影响：** Swagger UI 显示问题；维护困难。
**建议：** 标准化为英文代码注释，中文用户文档。

## 平台限制

### arcpy 仅限 Windows

**位置：** `src/arcgis_agent/adapters/arcpy_adapter.py`
**严重性：** 中（设计限制）
**描述：** arcpy 仅在安装了 ArcGIS Pro 的 Windows 上可用。代码库使用延迟导入以允许在其他平台上进行测试导入。
**影响：** 无法在 Linux/macOS 上运行 GIS 操作。
**建议：** 文档记录 Windows 要求；为非 Windows 开发提供模拟模式。

### 中文用户名系统不可用

**位置：** `src/arcgis_agent/adapters/arcpy_adapter.py`
**严重性：** 高
**描述：** 由于 arcpy.mp 编码错误，地图和布局功能在中文用户名系统上完全不可用。
**影响：** 中国市场的核心功能受限。
**建议：** 需要在纯英文用户名机器上验证；考虑 ArcGIS Pro 修复的变通方案。

## 功能缺失

### 无前端设置页面

**位置：** `web/src/`
**严重性：** 中
**描述：** 没有用于配置 API 密钥、工作空间路径或 LLM 提供商选择的 UI。所有配置必须通过环境变量或 API 调用完成。
**影响：** 非技术用户难以配置。
**建议：** 创建 React 设置页面（在项目记忆中列为待办事项）。

### 无对话持久化

**位置：** `src/arcgis_agent/api/dependencies.py`
**严重性：** 中
**描述：** 对话历史仅在内存中。重启时丢失。
**影响：** 用户体验差；无法恢复之前的对话。
**建议：** 持久化到 SQLite 或 JSON 文件。

### 无任务取消

**位置：** `src/arcgis_agent/services/task_service.py`
**严重性：** 低
**描述：** 无法取消正在运行的异步任务。
**影响：** 长时间运行的任务无法中止。
**建议：** 实施任务取消端点和逻辑。

### 无导出格式选项

**位置：** `src/arcgis_agent/services/map_service.py`
**严重性：** 低
**描述：** 地图/布局导出仅支持 PNG。不支持 PDF、SVG 或其他格式。
**影响：** 限制了专业地图制作工作流。
**建议：** 添加格式参数并支持多种导出格式。

## 代码中的 TODO/FIXME/HACK 注释

搜索代码库发现的标记注释：

**TODO：**
- `src/arcgis_agent/api/routes/tools.py` — em dash 编码错误需要替换为安全分隔符
- `src/arcgis_agent/mcp_server.py` — 一些工具签名可能需要更新

**HACK：**
- `src/arcgis_agent/adapters/arcpy_adapter.py` — 中文路径的变通方案
- `src/arcgis_agent/cli.py` — Windows UTF-8 重新配置

## 过时依赖

**未检测到主要过时依赖。** 所有依赖版本在 `pyproject.toml` 和 `web/package.json` 中都是最新的。

**注意：** ArcPy 版本与安装的 ArcGIS Pro 绑定，无法独立更新。

## 技术债总结

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🔴 严重 | arcpy.mp 中文路径静默失败 | 核心功能在中文系统不可用 |
| 🔴 严重 | 无 API 认证 | 安全风险 |
| 🔴 严重 | 上传路径未净化 | 安全风险 |
| 🟡 中等 | CORS 硬编码 | 阻止生产部署 |
| 🟡 中等 | 无速率限制 | LLM 成本失控风险 |
| 🟡 中等 | 内存对话存储 | 重启丢失历史 |
| 🟡 中等 | 工具定义重复 | 维护困难 |
| 🟡 中等 | 无前端设置页 | 非技术用户难配置 |
| 🟢 低 | SSE 人为延迟 | 响应稍慢 |
| 🟢 低 | 无连接池 | 首次 token 延迟 |
| 🟢 低 | 混合中英文文档 | 编码问题 |

---

*问题审计：2026-05-27*
