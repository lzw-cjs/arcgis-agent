# Phase 4: 地图生产 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 04-map-production
**Areas discussed:** 接口拆分/架构 (prior), 符号化设计深度, 布局元素类型与参数, 导出格式与CLI分组

---

## 符号化设计深度

### Simple 参数范围

| Option | Description | Selected |
|--------|-------------|----------|
| 颜色 + 轮廓 + 大小 | --color, --outline-color, --size | |
| 以上 + 透明度 | 加 --opacity 0-100 | ✓ |
| 以上 + 符号库 | 加 --symbol-gallery | |
| 全部 + 逐图层类型参数 | 几何类型差异化参数 | |

**User's choice:** 颜色 + 轮廓 + 大小 + 透明度
**Notes:** 透明度独立于颜色 Alpha 值

### 颜色格式

| Option | Description | Selected |
|--------|-------------|----------|
| R,G,B 逗号分隔 | --color 255,0,0 | ✓ |
| R,G,B,A 带透明度 | --color 255,0,0,50 | |
| 十六进制 #RRGGBB | --color '#FF0000' | |

**User's choice:** R,G,B 逗号分隔

### UniqueValues 字段配置

| Option | Description | Selected |
|--------|-------------|----------|
| 单字段 | --field "Type" | ✓ |
| 多字段组合 | --field "A" --field "B" | |

**User's choice:** 单字段

### UniqueValues 颜色分配

| Option | Description | Selected |
|--------|-------------|----------|
| 自动色带 | --color-ramp 自动分配 | |
| 自动色带 + 手动覆盖 | --color-ramp + --values JSON | ✓ |
| 纯手动指定 | 每个值通过 --values JSON | |

**User's choice:** 自动色带 + 手动覆盖

### GraduatedColors 分类方法

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 NaturalBreaks | Jenks 自然断点 | |
| NaturalBreaks + Quantile + EqualInterval | 最常用三种 | ✓ |
| 全部 7 种 | 完整 arcpy 方法 | |

**User's choice:** NaturalBreaks + Quantile + EqualInterval

### GraduatedColors 分级数

| Option | Description | Selected |
|--------|-------------|----------|
| 2-7 级，默认 5 | 制图学推荐范围 | ✓ |
| 2-32 级，默认 5 | arcpy 全范围 | |

**User's choice:** 2-7 级，默认 5

### 色带指定

| Option | Description | Selected |
|--------|-------------|----------|
| 按名称字符串匹配 | --color-ramp "Yellow to Red" | ✓ |
| 名称 + 列出可用色带 | 额外 list-color-ramps 命令 | |
| 名称 + 默认色带 | 不指定时用默认 | |

**User's choice:** 按名称字符串匹配（无默认色带，无查询命令）

### GraduatedColors 轮廓

| Option | Description | Selected |
|--------|-------------|----------|
| 支持 --outline-color | 统一轮廓颜色 | ✓ |
| 不需要轮廓控制 | 由 ArcGIS Pro 默认 | |
| 支持 --outline-color 和 --outline-size | 颜色 + 宽度 | |

**User's choice:** --outline-color 统一轮廓

---

## 布局元素类型与参数

### 元素类型

| Option | Description | Selected |
|--------|-------------|----------|
| 核心 5 种 | text, legend, scale-bar, north-arrow, map-frame | |
| 核心 5 种 + 图片 | 额外 image | ✓ |
| 核心 5 种 + 图片 + 动态文本 | 额外 dynamic-text | |

**User's choice:** text, legend, scale-bar, north-arrow, map-frame, image (6 种)

### 定位方式

| Option | Description | Selected |
|--------|-------------|----------|
| XY坐标 + 宽高 | 手动精确定位 | |
| 预设位置 + XY坐标 | --position + 手动坐标 | ✓ |
| 仅预设位置 | --position only | |

**User's choice:** 预设位置 + XY坐标

### 文本参数

| Option | Description | Selected |
|--------|-------------|----------|
| 内容 + 字号 + 颜色 | 基础 | |
| 以上 + 粗体/斜体 | 加 --bold --italic | ✓ |
| 以上 + 字体 | 加 --font-family | |

**User's choice:** 内容 + 字号 + 颜色 + 粗体/斜体

### 装饰元素参数

| Option | Description | Selected |
|--------|-------------|----------|
| 图例：仅标题 | --title "Legend" | |
| 比例尺：无参数 | 默认样式 | |
| 三者各自选项 | Legend title + ScaleBar style + NorthArrow style | ✓ |

**User's choice:** 各自独立参数

### MapFrame / Image 参数

| Option | Description | Selected |
|--------|-------------|----------|
| MapFrame: map名, Image: 路径 | 最简 | |
| 以上 + MapFrame 缩放控制 | --extent full_extent|current_view | ✓ |
| 以上 + Image 缩放模式 | --fit stretch/fit/uniform | |

**User's choice:** MapFrame 含缩放控制

### 页面尺寸

| Option | Description | Selected |
|--------|-------------|----------|
| 预设纸张大小 | --page-size A4|A3|Letter|Tabloid | |
| 预设纸张 + 方向 | 加 --orientation portrait|landscape | ✓ |
| 自定义宽高 | --width --height --unit | |
| 预设 + 自定义 | 预设快捷 + 自定义兜底 | |

**User's choice:** 预设纸张 + 方向

---

## 导出格式与CLI分组

### DPI 设置

| Option | Description | Selected |
|--------|-------------|----------|
| 固定 DPI 选项 | 96|150|300|600, 默认 300 | ✓ |
| 自由 DPI + 默认 300 | 任意整数 | |
| 仅默认 300 | 不提供 --dpi | |

**User's choice:** 固定 DPI 选项

### 导出命令

| Option | Description | Selected |
|--------|-------------|----------|
| 独立命令，共享参数 | map export + layout export | ✓ |
| 统一 export 命令 | --type map|layout | |

**User's choice:** 独立命令

### PNG 透明

| Option | Description | Selected |
|--------|-------------|----------|
| 支持 --transparent | 透明背景标志 | ✓ |
| 不需要透明 | 默认背景 | |

**User's choice:** 支持 --transparent

### CLI 分组

| Option | Description | Selected |
|--------|-------------|----------|
| map 和 layout 同级组 | arcgis-agent map ... / arcgis-agent layout ... | ✓ |
| layout 是 map 的子组 | arcgis-agent map layout ... | |

**User's choice:** map 和 layout 同级组

### 导出命令签名

| Option | Description | Selected |
|--------|-------------|----------|
| 确认，没问题 | `map export <map_name> <output> [--format PNG|PDF] [--dpi 96|150|300|600] [--transparent]` | ✓ |
| 需要确认输出路径行为 | 文件路径 vs 文件名 | |
| 需要确认 overwrite 行为 | --no-overwrite 策略 | |

**User's choice:** 签名确认

---

## Claude's Discretion

- Adapter 接口方法的具体签名（IMapDocument.symbolize_layer, ILayoutDocument 方法定义）
- ArcPyMapDocument 和 MockMapDocument 的实现细节
- Service 层分拆粒度
- CLI 命令参数验证逻辑
- 单元测试用例设计

## Deferred Ideas

None
