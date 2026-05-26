# Feature Landscape: ArcGIS Pro CLI Tool for AI Agent

**Domain:** GIS Geoprocessing Automation CLI
**Researched:** 2026-05-25
**Overall Confidence:** MEDIUM (based on arcgis-python-api repo structure + arcpy documentation knowledge)

## Executive Summary

ArcGIS Pro CLI tool for AI Agent needs to wrap the most common geoprocessing workflows into agent-friendly, JSON-outputting commands. Based on analysis of Esri's arcgis-python-api repository structure (59,930 code snippets) and arcpy module organization, the feature space breaks into four domains: Map Production, GIS Data Processing, Spatial Analysis, and Project Management.

Key insight: The arcgis-python-api already organizes functionality into clear modules (features, raster, geocoding, network analysis, mapping, geoenrichment). The CLI tool should follow similar organizational boundaries but expose them as discrete, composable commands rather than Python API calls.

---

## Feature Classification

### Table Stakes (Must Have)

Features users expect. Missing = product feels incomplete, agent cannot perform basic GIS tasks.

#### Domain 1: Map Production (地图生产)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `map create` - Create map from project | Basic map operations | Low | aprx.listMaps(), map.name |
| `map add-layer` - Add feature layer to map | Core map building | Low | map.addLayer() |
| `map remove-layer` - Remove layer from map | Map cleanup | Low | map.removeLayer() |
| `map list-layers` - List layers in map | Agent needs to discover state | Low | map.listLayers() |
| `map set-extent` - Set map view extent | Focus on area of interest | Low | map.extent = ... |
| `map export` - Export map to PDF/PNG/JPEG | Output deliverable | Medium | layout.exportToPDF() |
| `layout create` - Create layout | Map production | Medium | aprx.createLayout() |
| `layout add-element` - Add text/legend/scalebar | Cartographic elements | Medium | layout.addElement() |
| `layout export` - Export layout to image | Final output | Medium | layout.exportToPDF/PNG/JPEG() |
| `mapseries list` - List map series pages | Batch production | Low | layout.mapSeries |
| `mapseries export` - Export all pages | Batch output | Medium | mapSeries.exportToPDF() |

#### Domain 2: GIS Data Processing (GIS 数据处理)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `data list` - List datasets in workspace | Agent discovery | Low | arcpy.ListFeatureClasses() |
| `data describe` - Get metadata/schema | Agent needs structure info | Low | arcpy.Describe() |
| `data copy` - Copy feature class | Common operation | Low | arcpy.management.Copy() |
| `data delete` - Delete dataset | Cleanup | Low | arcpy.management.Delete() |
| `data rename` - Rename dataset | Organization | Low | arcpy.management.Rename() |
| `data project` - Project/reproject data | Coordinate system conversion | Medium | arcpy.management.Project() |
| `data clip` - Clip features to boundary | Extract subset | Medium | arcpy.analysis.Clip() |
| `data merge` - Merge multiple datasets | Combine data | Medium | arcpy.management.Merge() |
| `data dissolve` - Dissolve by attributes | Aggregate features | Medium | arcpy.management.Dissolve() |
| `data select` - Select by attributes/location | Query features | Medium | arcpy.management.SelectLayerByAttribute() |
| `data buffer` - Create buffer zones | Proximity analysis | Medium | arcpy.analysis.Buffer() |
| `data intersect` - Find overlapping areas | Overlay analysis | Medium | arcpy.analysis.Intersect() |
| `data union` - Combine polygon layers | Overlay analysis | Medium | arcpy.analysis.Union() |
| `data spatial-join` - Join by spatial relationship | Attribute transfer | Medium | arcpy.analysis.SpatialJoin() |
| `data convert` - Format conversion (shp/gdb/csv) | Interoperability | Medium | Various conversion tools |
| `data fields` - List/inspect fields | Schema discovery | Low | arcpy.ListFields() |
| `data count` - Count features | Basic statistics | Low | arcpy.management.GetCount() |
| `data extent` - Get dataset extent | Spatial reference | Low | arcpy.Describe().extent |

#### Domain 3: Spatial Analysis (空间分析)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `analysis buffer` - Buffer analysis | Most common proximity tool | Medium | arcpy.analysis.Buffer() |
| `analysis clip` - Clip analysis | Extract by area | Medium | arcpy.analysis.Clip() |
| `analysis intersect` - Intersection analysis | Find overlaps | Medium | arcpy.analysis.Intersect() |
| `analysis union` - Union analysis | Combine areas | Medium | arcpy.analysis.Union() |
| `analysis erase` - Erase analysis | Remove overlaps | Medium | arcpy.analysis.Erase() |
| `analysis spatial-join` - Spatial join | Attribute transfer by location | Medium | arcpy.analysis.SpatialJoin() |
| `analysis overlay` - Multiple overlay operations | Flexible overlay | Medium | Various overlay tools |
| `analysis near` - Calculate distances | Proximity measurement | Medium | arcpy.analysis.Near() |
| `analysis summary-statistics` - Summarize data | Statistical summary | Medium | arcpy.analysis.Statistics() |
| `analysis hot-spot` - Hot spot analysis | Pattern detection | High | arcpy.stats.OptimizedHotSpotAnalysis() |
| `analysis cluster` - Cluster analysis | Pattern detection | High | arcpy.stats.ClustersOutliers() |

#### Domain 4: Project Management (项目管理)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `project create` - Create new project | Start fresh | Low | arcpy.mp.ArcGISProject() |
| `project open` - Open existing project | Access project | Low | arcpy.mp.ArcGISProject(path) |
| `project save` - Save project | Persist changes | Low | aprx.save() |
| `project save-as` - Save copy | Backup/versioning | Low | aprx.saveACopy() |
| `project list` - List projects in folder | Discovery | Low | os.listdir() |
| `project info` - Get project metadata | Agent needs context | Low | aprx.homeFolder, etc. |
| `workspace set` - Set current workspace | Context switching | Low | arcpy.env.workspace |
| `workspace get` - Get current workspace | State awareness | Low | arcpy.env.workspace |
| `env list` - List environment settings | Configuration awareness | Low | arcpy.env |
| `env set` - Set environment settings | Configure behavior | Low | arcpy.env.xxx = value |

---

### Differentiators (Nice to Have)

Features that set product apart. Not expected, but valued by power users and advanced workflows.

#### Domain 1: Map Production

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `map symbolize` - Apply symbology | Automated styling | High | CIM symbols, renderer |
| `map label` - Configure labeling | Automated cartography | High | Label classes, expressions |
| `layout template` - Apply layout templates | Standardized output | Medium | Template management |
| `layout dynamic-text` - Dynamic text elements | Auto-populate metadata | Medium | Dynamic text expressions |
| `mapseries filter` - Filter map series pages | Selective export | Medium | Definition queries |
| `map animate` - Create time-enabled maps | Temporal visualization | High | Time slider, time-aware layers |

#### Domain 2: GIS Data Processing

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `data validate` - Validate topology/geometry | Data quality | High | Topology rules |
| `data repair-geometry` - Fix geometry issues | Data cleanup | Medium | arcpy.management.RepairGeometry() |
| `data simplify` - Simplify geometries | Performance optimization | Medium | arcpy.management.Simplify() |
| `data smooth` - Smooth geometries | Cartographic quality | Medium | arcpy.management.Smooth() |
| `data aggregate` - Aggregate points to polygons | Spatial aggregation | Medium | arcpy.analysis.AggregatePoints() |
| `data split` - Split features by attributes | Data partitioning | Medium | arcpy.management.Split() |
| `data multipart-to-singlepart` - Explode multipart | Geometry conversion | Medium | arcpy.management.MultipartToSinglepart() |
| `data add-xy` - Add coordinate fields | Enrichment | Low | arcpy.management.AddXY() |
| `data calculate-field` - Calculate field values | Attribute manipulation | Medium | arcpy.management.CalculateField() |

#### Domain 3: Spatial Analysis

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `analysis kernel-density` - Kernel density | Density surface | High | arcpy.sa.KernelDensity() |
| `analysis idw` - Inverse Distance Weighting | Interpolation | High | arcpy.sa.Idw() |
| `analysis kriging` - Kriging interpolation | Geostatistical interpolation | High | arcpy.sa.Kriging() |
| `analysis slope` - Slope analysis | Terrain analysis | Medium | arcpy.sa.Slope() |
| `analysis aspect` - Aspect analysis | Terrain analysis | Medium | arcpy.sa.Aspect() |
| `analysis hillshade` - Hillshade | Terrain visualization | Medium | arcpy.sa.Hillshade() |
| `analysis viewshed` - Viewshed analysis | Visibility analysis | High | arcpy.sa.Viewshed() |
| `analysis watershed` - Watershed delineation | Hydrological analysis | High | arcpy.sa.Watershed() |
| `analysis zonal-statistics` - Zonal statistics | Area-based statistics | Medium | arcpy.sa.ZonalStatistics() |
| `analysis extract-by-mask` - Extract raster by mask | Raster clipping | Medium | arcpy.sa.ExtractByMask() |
| `analysis reclassify` - Reclassify raster | Value reclassification | Medium | arcpy.sa.Reclassify() |
| `analysis raster-calculator` - Map algebra | Complex raster operations | High | Map algebra expression |
| `analysis cost-distance` - Cost distance | Least cost path | High | arcpy.sa.CostDistance() |
| `analysis least-cost-path` - Find optimal route | Path optimization | High | arcpy.sa.CostPath() |
| `analysis od-cost-matrix` - Origin-destination matrix | Travel time analysis | High | Network Analyst |
| `analysis service-area` - Service area | Accessibility analysis | High | Network Analyst |
| `analysis route` - Find routes | Routing | High | Network Analyst |
| `analysis closest-facility` - Find nearest | Facility location | High | Network Analyst |

#### Domain 4: Project Management

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `project clone` - Clone project | Project templating | Medium | aprx.saveACopy() + modifications |
| `project backup` - Backup project | Data safety | Low | Copy with timestamp |
| `project diff` - Compare project versions | Version control | High | Custom implementation |
| `project batch-process` - Process multiple projects | Automation | Medium | Loop + process |
| `project report` - Generate project report | Documentation | Medium | Custom report generation |
| `geodatabase create` - Create file geodatabase | Data organization | Low | arcpy.management.CreateFileGDB() |
| `geodatabase compact` - Compact geodatabase | Performance | Low | arcpy.management.Compact() |
| `geodatabase compress` - Compress geodatabase | Storage optimization | Low | arcpy.management.Compress() |
| `geodatabase version` - Manage versions | Multi-user editing | High | Version management |
| `geodatabase reconcile` - Reconcile versions | Version management | High | arcpy.management.ReconcileVersions() |

---

### Anti-Features (Do NOT Build)

Features to explicitly NOT build. Either too complex, too niche, or better handled by other tools.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full ArcGIS Pro GUI automation | Complex, fragile, not agent-friendly | Focus on geoprocessing commands, not UI |
| Real-time collaboration features | Requires ArcGIS Enterprise, complex scope | Let users use ArcGIS Online/Enterprise directly |
| Full map authoring (drag-drop) | GUI-centric, not CLI-appropriate | Provide template-based map creation |
| Network analysis solver configuration | Too many parameters, domain-specific | Expose common presets, document advanced usage |
| Geoprocessing model building | ModelBuilder is visual, not CLI | Support Python script execution instead |
| Full raster function chain editor | Complex visual programming | Provide preset raster functions |
| 3D scene authoring | Niche, complex | Support basic 3D export only |
| Full topology editing | Complex rules, GUI-intensive | Provide validation and reporting only |
| Real-time data streaming | Requires ArcGIS Velocity | Document integration patterns |
| Full deep learning training | Requires GPU, large datasets | Provide inference/prediction commands |

---

## Feature Dependencies

```
project open → workspace set → data list → data describe
project open → map list-layers → map add-layer → map export
data select → data clip → analysis buffer → data dissolve
analysis intersect → data spatial-join → analysis summary-statistics
layout create → layout add-element → layout export
geodatabase create → data copy → data project → map add-layer
```

---

## Agent-Specific Considerations

### JSON Output Format

All commands should return structured JSON:

```json
{
  "success": true,
  "command": "data clip",
  "input": { "features": "roads.shp", "clip": "boundary.shp" },
  "output": { "features": "roads_clipped.shp", "count": 1234 },
  "metadata": { "extent": {...}, "fields": [...] },
  "warnings": [],
  "errors": []
}
```

### Discovery Commands (Critical for Agent)

| Command | Purpose | Priority |
|---------|---------|----------|
| `workspace list-datasets` | Agent discovers available data | P0 |
| `data describe` | Agent understands data structure | P0 |
| `data fields` | Agent knows attribute schema | P0 |
| `data extent` | Agent knows spatial coverage | P0 |
| `map list-layers` | Agent discovers map contents | P0 |
| `project info` | Agent understands project context | P0 |
| `env list` | Agent knows current settings | P0 |
| `tools list` | Agent discovers available tools | P1 |
| `tools describe <tool>` | Agent understands tool parameters | P1 |

### Batch Operations (Important for Agent)

| Command | Purpose | Priority |
|---------|---------|----------|
| `batch <command> <file>` | Process multiple datasets | P1 |
| `pipeline <workflow>` | Chain multiple commands | P2 |
| `macro <name>` | Save reusable workflows | P2 |

---

## MVP Recommendation

### Phase 1: Core Discovery + Data Operations (P0)

Prioritize:
1. `workspace set/get/list` - Context management
2. `data list/describe/fields/extent` - Data discovery
3. `data copy/delete/rename` - Basic data management
4. `data convert` - Format conversion (shp/csv/gdb)
5. `project create/open/save` - Project management

### Phase 2: Essential Geoprocessing (P0)

Prioritize:
1. `data select/clip/buffer/intersect/union/dissolve` - Core overlay/proximity
2. `data spatial-join` - Attribute transfer
3. `data merge/project` - Data combination/transformation
4. `analysis summary-statistics` - Basic statistics

### Phase 3: Map Production (P1)

Prioritize:
1. `map create/add-layer/remove-layer/list-layers` - Map building
2. `layout create/add-element/export` - Layout output
3. `map export` - Quick map export
4. `mapseries list/export` - Batch production

### Phase 4: Advanced Analysis (P2)

Prioritize:
1. `analysis hot-spot/cluster` - Pattern analysis
2. `analysis kernel-density/idw` - Density/interpolation
3. `analysis slope/aspect/viewshed` - Terrain analysis
4. `analysis route/service-area` - Network analysis

Defer:
- Deep learning inference (P3)
- Knowledge graph operations (P3)
- Full raster function chains (P3)

---

## Complexity Assessment Summary

| Complexity | Count | Examples |
|------------|-------|---------|
| Low | 25 | workspace set, data list, project save |
| Medium | 35 | data clip, buffer, layout export |
| High | 20 | kernel density, kriging, network analysis |
| **Total** | **80** | |

---

## Sources

- Esri/arcgis-python-api GitHub repository (59,930 code snippets, High reputation)
- ArcGIS Pro arcpy module documentation
- ArcGIS REST APIs documentation
- Esri Developer documentation

## Confidence Notes

| Area | Confidence | Reason |
|------|------------|--------|
| Feature list completeness | MEDIUM | Based on repo structure analysis, not exhaustive tool reference |
| Complexity assessment | MEDIUM | Based on typical arcpy usage patterns |
| Agent-specific needs | LOW | Emerging field, limited precedent |
| Anti-features | MEDIUM | Based on common GIS automation pain points |
