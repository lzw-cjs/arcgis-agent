# Phase 8: 分发与部署

**目标:** 让 arcgis-agent 可以通过 MCP Server、PyPI 包和 Web API 三种方式分享给他人使用。

**需求:** DIST-01~03

**依赖:** Phase 5 (MCP Server), Phase 7 (Web UI/API)

## 交付物

### MCP Server 分发
- [ ] `config/claude_desktop_config.example.json` 示例配置文件
- [ ] MCP Server 安装文档 (`docs/mcp-setup.md`)
- [ ] 环境检测脚本 (`scripts/check-env.py`)

### PyPI 包分发
- [ ] 完善的 `pyproject.toml`（含 classifiers、keywords、license）
- [ ] `MANIFEST.in` 确保资源文件打包
- [ ] `LICENSE` 文件
- [ ] `CHANGELOG.md` 版本变更日志
- [ ] 面向 pip 用户的 `README.md`
- [ ] GitHub Actions 工作流：自动发布到 PyPI

### Web API 服务分发
- [ ] `Dockerfile`（含 arcpy 限制说明）
- [ ] `.env.example` 环境变量模板
- [ ] `pyproject.toml` extra deps
- [ ] 部署文档 (`docs/deployment.md`)
- [ ] Systemd 和 Windows 服务脚本

## 成功标准

- 新用户可以在 5 分钟内完成 MCP Server 配置并连接到 Claude Desktop
- `pip install arcgis-agent` 后 `arcgis-agent --help` 可用
- Web API 可通过 Docker 一键启动（在支持的环境中）
- 所有分发方式都有清晰的文档说明 arcpy 依赖和许可证要求

## 风险

| 风险 | 缓解措施 |
|------|----------|
| arcpy 不可 pip 安装 | 文档明确说明需要 ArcGIS Pro，提供环境检测脚本 |
| 中文路径问题 | 文档提醒，提供 UTF-8 配置指导 |
| 许可证限制 | 文档标注需要 ArcGIS Pro 许可证 |
| Windows 独占 | 文档明确标注仅支持 Windows |

## 计划

**Plans:** 3 plans

- [ ] 08-01-PLAN.md — MCP Server 分发配置
- [ ] 08-02-PLAN.md — PyPI 包分发
- [ ] 08-03-PLAN.md — Web API 部署
