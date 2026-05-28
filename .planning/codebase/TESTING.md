# 测试基础设施

**分析日期：** 2026-05-27

## 测试框架

**后端（Python）：**
- 框架：pytest
- 配置：`pyproject.toml` 中的 `[tool.pytest.ini_options]`（如果存在）或默认配置
- 插件：pytest-asyncio（用于异步测试）
- 测试目录：`tests/`
- 测试发现：`test_*.py` 或 `*_test.py`

**前端（TypeScript/React）：**
- 框架：Vitest ^3.0.0
- 配置：`web/vite.config.ts` 或 `web/vitest.config.ts`
- 测试目录：`web/src/__tests__/`
- 测试发现：`*.test.ts`

## 测试目录结构

```
tests/
├── conftest.py                  # 共享夹具（模拟适配器、测试客户端）
├── __init__.py
├── unit/                        # 单元测试
│   ├── __init__.py
│   ├── conftest.py              # 单元测试专用夹具
│   ├── test_adapters.py         # 模拟适配器实现
│   ├── test_analysis.py         # AnalysisService（GEO-10）
│   ├── test_api_core.py         # FastAPI 应用、中间件、ConversationStore
│   ├── test_api_schemas.py      # Pydantic 模式（聊天/任务/事件）
│   ├── test_chat_api.py         # SSE 流式传输、JSON 模式、历史
│   ├── test_cli.py              # CLI 选项、标志、退出码
│   ├── test_cli_geoprocessing.py # CLI 地理处理命令
│   ├── test_config.py           # WorkspaceConfig 持久化
│   ├── test_data_commands.py    # 数据命令 CLI 集成
│   ├── test_data_discovery.py   # DataDiscoveryService
│   ├── test_data_management.py  # DataManagementService
│   ├── test_env_check.py        # 环境检测
│   ├── test_geoprocessing.py    # GeoprocessingService（GEO-01~GEO-09）
│   ├── test_layout_commands.py  # 布局 CLI 命令
│   ├── test_layout_service.py   # LayoutService（MAP-09~MAP-11）
│   ├── test_map_commands.py     # 地图 CLI 命令
│   ├── test_map_service.py      # MapService（MAP-01~MAP-08）
│   ├── test_plugins.py          # 插件加载器
│   ├── test_project_service.py  # ProjectService
│   ├── test_result.py           # Result 模型
│   ├── test_services.py         # BaseService 依赖注入
│   ├── test_workspace_service.py # WorkspaceService
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── test_llm_adapter.py  # LLM 提供商适配器
│   ├── api/
│   │   ├── __init__.py
│   │   └── test_routes.py       # FastAPI REST 路由（33 个工具）
│   └── services/
│       ├── __init__.py
│       ├── test_chat_service.py  # ChatService SSE/代理循环
│       └── test_task_service.py  # TaskStore SQLite 持久化
└── e2e/                         # 端到端测试
    ├── __init__.py
    ├── conftest.py              # MCP E2E 夹具
    ├── INTEGRATION_CHECKLIST.md # 人工验证清单
    ├── test_chat_loop.py        # ChatService 集成测试
    ├── test_e2e_english_path.py # 完整地图/布局/GP 工作流（需 arcpy）
    └── test_mcp_tools.py        # MCP 协议工具注册（33 个工具）
```

**前端测试目录：**
```
web/src/__tests__/
├── chatApi.test.ts              # SSE API 客户端测试
├── chatStore.test.ts            # Zustand 存储测试
└── types.test.ts                # TypeScript 类型测试
```

## 测试覆盖范围

**总体状态：** 248/358 测试通过（截至 2026-05-27）

### 按领域覆盖

**适配器层：**
- 模拟适配器实现（`test_adapters.py`）
- LLM 提供商适配器（`test_llm_adapter.py`）
- 覆盖：ABC 接口、模拟行为、提供商切换

**服务层：**
- GeoprocessingService（GEO-01~GEO-09）：缓冲区、裁剪、相交、联合、融合、空间连接、合并、投影、选择
- MapService（MAP-01~MAP-08）：创建地图、添加/移除图层、符号化、标注、导出、设置范围、列出图层
- LayoutService（MAP-09~MAP-11）：创建布局、添加元素、导出
- DataDiscoveryService：列出、描述、字段、范围、计数
- DataManagementService：复制、删除、重命名、转换
- AnalysisService（GEO-10）：汇总统计
- ProjectService：项目信息
- WorkspaceService：工作空间 get/set
- ChatService：SSE 流式传输、代理循环
- TaskStore：SQLite 持久化、CRUD

**API 层：**
- FastAPI 应用创建和生命周期（`test_api_core.py`）
- 中间件（请求指标、慢请求日志）
- ConversationStore（LRU、线程安全）
- REST 路由（33 个工具端点）
- SSE 聊天路由（流式传输、JSON 模式、对话历史）
- Pydantic 模式验证（聊天、任务、事件）

**CLI 层：**
- 命令选项和标志（`test_cli.py`）
- 地理处理命令（`test_cli_geoprocessing.py`）
- 数据命令（`test_data_commands.py`）
- 布局命令（`test_layout_commands.py`）
- 地图命令（`test_map_commands.py`）

**端到端：**
- MCP 工具注册（33 个工具）
- ChatService 集成（聊天循环）
- 完整地图/布局/GP 工作流（`test_e2e_english_path.py` - 需 arcpy）

### 前端覆盖

- SSE API 客户端：事件流解析、错误处理
- Zustand 存储：状态转换、消息追加、工具调用更新
- TypeScript 类型：接口一致性

## 测试夹具

**核心夹具（`tests/conftest.py`）：**
- `mock_gp`：模拟的 IGeoProcessor
- `mock_map`：模拟的 IMapDocument
- `mock_data`：模拟的 IDataAccessor
- `mock_layout`：模拟的 ILayoutBuilder
- `mock_llm`：模拟的 ILLMProvider
- `client`：带有模拟依赖项的 FastAPI TestClient
- `task_store`：临时 TaskStore（测试后清理）

**单元测试夹具（`tests/unit/conftest.py`）：**
- 特定领域的服务实例，带有模拟适配器

**E2E 夹具（`tests/e2e/conftest.py`）：**
- MCP 服务器连接夹具
- arcpy 需要英文路径工作空间

## 测试模式

### 模拟适配器模式

大多数单元测试使用注入到服务中的模拟适配器：
```python
def test_buffer(self, mock_gp):
    service = GeoprocessingService(gp=mock_gp)
    mock_gp.buffer.return_value = Result.ok(data={"output": "buffer.shp"})
    result = service.buffer(input_path="input.shp", distance="1 km")
    assert result.success
    mock_gp.buffer.assert_called_once()
```

### FastAPI TestClient 模式

API 测试使用 TestClient，带有覆盖的依赖项：
```python
def test_endpoint(client):
    response = client.post("/api/v1/tools/buffer", json={...})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### SSE 流测试模式

聊天 API 测试验证 SSE 事件流：
```python
def test_chat_sse(client):
    response = client.post("/api/v1/chat", json={"message": "..."})
    events = parse_sse_events(response)
    assert any(e["type"] == "token" for e in events)
    assert any(e["type"] == "done" for e in events)
```

### SQLite 测试模式

任务存储测试使用临时数据库：
```python
def test_task_store(tmp_path):
    store = TaskStore(db_path=str(tmp_path / "test.db"))
    task = store.create(tool_name="buffer", arguments={...})
    assert store.get(task["task_id"]) is not None
```

## CI 集成

**当前状态：** 未检测到 CI/CD 管道

**本地运行：**
- Python 测试：`pytest`（从项目根目录）
- 前端测试：`cd web && npm test`
- 特定测试：`pytest tests/unit/test_map_service.py`

## 测试数据

**模拟数据：**
- 模拟适配器返回预定义的 Result 对象
- 无外部测试数据文件（夹具中硬编码）

**E2E 数据：**
- 需要 ArcGIS Pro 工作空间和 arcpy
- `E2E_WORKSPACE` 环境变量指向测试数据目录
- 英文路径系统需要用于地图/布局 E2E 测试

## 已知测试问题

**失败的测试（110/358）：**
- 与 arcpy.mp 中文路径编码错误相关（地图/布局服务测试）
- 一些 SSE 流式传输边缘情况
- LLM 提供商模拟不匹配

**跳过的测试：**
- 需要 arcpy 的 E2E 测试（在没有 ArcGIS Pro 的 CI 中跳过）
- 需要英文路径系统的测试（在中文用户名机器上跳过）

**人工验证：**
- 5/5 人工验证项已通过（Phase 0-5、7）
- 清单：`tests/e2e/INTEGRATION_CHECKLIST.md`

## 测试命令

```bash
# 运行所有后端测试
pytest

# 运行特定测试文件
pytest tests/unit/test_map_service.py

# 运行特定测试
pytest tests/unit/test_map_service.py::TestMapService::test_create_map

# 运行 E2E 测试（需要 arcpy）
pytest tests/e2e/

# 运行前端测试
cd web && npm test

# 详细输出
pytest -v

# 带覆盖率
pytest --cov=arcgis_agent
```

---

*测试基础设施分析：2026-05-27*
