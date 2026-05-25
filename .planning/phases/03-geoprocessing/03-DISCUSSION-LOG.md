# Phase 3: 地理处理操作 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 3-地理处理操作
**Areas discussed:** CLI 命令分组, 缓冲区单位设计, 多输入操作设计, 汇总统计设计

---

## CLI 命令分组

### Q1: GEO-01~09 和 GEO-10 的命令分组

| Option | Description | Selected |
|--------|-------------|----------|
| 按 ROADMAP 原样 | GEO-01~09 放在 data 组，GEO-10 用 analysis 组 | ✓ |
| 单独 geoprocessing 组 | 新建 gp 组（gp buffer, gp clip） | |
| 全部放 data 组 | 所有 10 个命令统一放在 data 组 | |

**User's choice:** 按 ROADMAP 原样（推荐）
**Notes:** 保持与 ROADMAP.md 一致

### Q2: GEO-01~09 命令代码文件

| Option | Description | Selected |
|--------|-------------|----------|
| 新建 geoprocessing.py | 注册到 data 组，data.py 保持不变 | ✓ |
| 追加到 data.py | 在现有文件中追加 | |
| 新建 geo.py | 更短的文件名 | |

**User's choice:** 新建 geoprocessing.py（推荐）
**Notes:** 职责清晰分离

### Q3: GEO-10 实现位置

| Option | Description | Selected |
|--------|-------------|----------|
| 新建 analysis.py | 注册 analysis 入口 | ✓ |
| 放在 geoprocessing.py | 作为 data summary-stats 子命令 | |

**User's choice:** 新建 analysis.py（推荐）
**Notes:** analysis 入口已在 pyproject.toml 中预留

### Q4: 注册方式

| Option | Description | Selected |
|--------|-------------|----------|
| 直接注册到 data 组 | register() 向 data 组添加子命令 | ✓ |
| 创建 data gp 子组 | 命令变为 data gp buffer | |

**User's choice:** 直接注册到 data 组（推荐）

### Q5: 组冲突解决方案

| Option | Description | Selected |
|--------|-------------|----------|
| 共享 data_group.py | 新建共享模块定义 data 组 | ✓ |
| 用 Click get_command | 通过 Click 机制添加 | |
| 导出 data_group | data.py 导出组引用 | |

**User's choice:** 共享 data_group.py（推荐）
**Notes:** 最干净的解决方案

---

## 缓冲区单位设计

### Q1: 支持的距离单位

| Option | Description | Selected |
|--------|-------------|----------|
| 完整 ArcPy 单位 | Meters, Kilometers, Feet, Miles, Yards, DecimalDegrees | ✓ |
| 常用 4 种 | Meters, Kilometers, Feet, Miles | |
| 仅 Meters | 最简单 | |

**User's choice:** 完整 ArcPy 单位（推荐）

### Q2: 距离参数格式

| Option | Description | Selected |
|--------|-------------|----------|
| 分开参数 | --distance 100 --unit Meters | ✓ |
| 字符串格式 | --distance "100 Meters" | |
| 默认 Meters | --distance 100，默认单位 | |

**User's choice:** 分开参数（推荐）

### Q3: side type / end type 高级选项

| Option | Description | Selected |
|--------|-------------|----------|
| 不支持 | 仅生成标准缓冲区 | ✓ |
| 支持 side+end | --side (FULL/LEFT/RIGHT) --end (ROUND/FLAT) | |

**User's choice:** 不支持（推荐）
**Notes:** Phase 3 保持简单

### Q4: dissolve_field 支持

| Option | Description | Selected |
|--------|-------------|----------|
| 不支持 | 每个要素独立缓冲区 | |
| 支持 dissolve-field | 按字段融合重叠缓冲区 | ✓ |

**User's choice:** 支持 dissolve-field
**Notes:** 有用的功能

---

## 多输入操作设计

### Q1: 多输入 CLI 格式

| Option | Description | Selected |
|--------|-------------|----------|
| 逗号分隔 | data intersect a.shp,b.shp,c.shp out.shp | ✓ |
| 重复 --input | --input a.shp --input b.shp | |
| 空格分隔 | 需要 nargs=-1 或引号 | |

**User's choice:** 逗号分隔（推荐）

### Q2: CRS 一致性检查

| Option | Description | Selected |
|--------|-------------|----------|
| 预检查 + 报错 | 不一致时报错并提示用户 | ✓ |
| 不检查 | 让 ArcPy 自己处理 | |
| 检查 + 警告 | 只警告继续执行 | |

**User's choice:** 预检查 + 报错（推荐）
**Notes:** PITFALL #13

### Q3: Result 输出信息

| Option | Description | Selected |
|--------|-------------|----------|
| 标准三要素 | 输出路径、要素数量、处理时间 | ✓ |
| 最小信息 | 仅路径和成功/失败 | |
| 详细信息 | 额外返回输入数量、坐标系等 | |

**User's choice:** 标准三要素（推荐）

### Q4: 最少输入数量

| Option | Description | Selected |
|--------|-------------|----------|
| 至少 2 个 | intersect/union/merge 都需要 2+ | ✓ |
| merge 允许 1 个 | merge 允许 1 个输入（直接复制） | |

**User's choice:** 至少 2 个（推荐）

---

## 汇总统计设计

### Q1: 统计类型

| Option | Description | Selected |
|--------|-------------|----------|
| 完整 ArcPy 统计 | SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN | ✓ |
| 常用 5 种 | SUM, MEAN, MIN, MAX, COUNT | |
| 基础 3 种 | SUM, MEAN, COUNT | |

**User's choice:** 完整 ArcPy 统计（推荐）

### Q2: 字段支持

| Option | Description | Selected |
|--------|-------------|----------|
| 多字段语法 | --field pop:SUM,area:MEAN | ✓ |
| 单字段 | --field pop --stat SUM | |
| 单字段多统计 | --field pop --stat SUM,MEAN | |

**User's choice:** 多字段语法（推荐）

### Q3: 分组统计

| Option | Description | Selected |
|--------|-------------|----------|
| 支持 case-field | 按字段分组后分别统计 | ✓ |
| 不支持 | 只做全局统计 | |

**User's choice:** 支持 case-field（推荐）

---

## 补充讨论

### CRS 检查降级策略

**Question:** 当 ArcPy 不可用时，坐标系一致性检查如何降级？

| Option | Description | Selected |
|--------|-------------|----------|
| 报错退出 | 没有 ArcPy 时报错退出 | ✓ |
| 跳过检查 + 警告 | 跳过检查继续执行 | |
| 跳过 + 日志 | 跳过但记录日志 | |

**User's choice:** 报错退出（推荐）
**Notes:** 安全优先

### 依赖声明

**Question:** ArcPy 无法通过 pip 安装，如何处理依赖声明？

**User's decision:** ArcPy 为可选依赖，在 pyproject.toml 中备注说明

---

## Claude's Discretion

- Adapter 方法的具体签名和内部实现
- Mock Adapter 的模拟行为细节
- 单元测试的组织方式和覆盖范围
- 错误码命名（沿用 GP_<TOOL>_FAILED 模式）

## Deferred Ideas

None — discussion stayed within phase scope
