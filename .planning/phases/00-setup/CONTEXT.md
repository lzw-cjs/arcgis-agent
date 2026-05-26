# Phase 0: 项目搭建 & 环境准备 — 上下文

## 目标

建立可重复的开发环境和项目骨架。

## 关键约束

- 必须在 ArcGIS Pro 的 conda 环境中工作
- 不能使用 uv/poetry/pdm（会绕过 ArcGIS conda 环境）
- 使用 hatchling 作为 build backend
- 使用 src layout

## 技术决策

- Python 版本由 ArcGIS Pro 决定（3.9-3.11）
- 先克隆 `arcgispro-py3` 环境再安装额外依赖
- 使用 `pip install --no-deps` 避免覆盖 Esri 钉死的包

## 验证方式

1. `conda activate arcgis-agent` 后 `import arcpy` 成功
2. `pip install -e .` 安装成功
3. wrapper `.bat` 从干净 CMD 可运行
