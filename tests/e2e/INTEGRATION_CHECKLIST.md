# arcgis-agent MCP Integration Checklist

## Claude Code Manual Tests (D-30)

This checklist provides step-by-step manual test procedures for verifying
arcgis-agent MCP tools work correctly through Claude Code.

### Prerequisites

- [ ] arcgis-agent MCP server configured in Claude Code MCP settings
- [ ] ArcGIS Pro with valid license running
- [ ] Test workspace with sample data available (e.g., D:/arcgis_e2e_test)
- [ ] `arcgis-agent-mcp` entry point working (`python -m arcgis_agent.mcp_server`)

### Test Cases

#### 1. Workspace Management

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 1.1 | Set workspace | "Set the workspace to D:/test_data" | Workspace set confirmation message with path | [ ] |
| 1.2 | Get workspace | "What is the current workspace?" | Returns the current workspace path | [ ] |

#### 2. Project Information

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 2.1 | Get project info | "What maps are in my project at D:/myproject.aprx?" | Returns list of maps, databases, and project path | [ ] |

#### 3. Data Discovery

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 3.1 | List datasets | "List all datasets in the workspace" | Returns list of feature classes and tables | [ ] |
| 3.2 | Describe dataset | "Describe the roads layer" | Returns metadata (type, spatial reference, field count, extent) | [ ] |
| 3.3 | Get fields | "What fields does the parcels layer have?" | Returns field names, types, and lengths | [ ] |
| 3.4 | Get extent | "What is the geographic extent of the buildings layer?" | Returns xmin, ymin, xmax, ymax bounding box | [ ] |
| 3.5 | Get feature count | "How many features in the cities layer?" | Returns integer feature count | [ ] |

#### 4. Data Management

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 4.1 | Copy data | "Copy the roads layer to roads_backup" | Copy confirmation with destination path | [ ] |
| 4.2 | Delete data (confirm) | "Delete the temp_layer dataset" | Delete confirmation after user confirms | [ ] |
| 4.3 | Rename data | "Rename cities_old to cities_new" | Rename confirmation with new path | [ ] |
| 4.4 | Convert format | "Convert the parcels layer to GeoJSON format" | Conversion confirmation with output path | [ ] |

#### 5. Geoprocessing

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 5.1 | Select by attribute | "Select buildings where type is 'commercial' and save to commercial_buildings" | Selection result with feature count | [ ] |
| 5.2 | Clip | "Clip the parcels layer to the county boundary" | Clip result with feature count | [ ] |
| 5.3 | Buffer | "Create a 100 meter buffer around roads" | Buffer created with feature count and elapsed time | [ ] |
| 5.4 | Intersect | "Find where roads and flood zones intersect" | Intersection result with feature count | [ ] |
| 5.5 | Union | "Union the two land use layers together" | Union result with feature count | [ ] |
| 5.6 | Dissolve | "Dissolve counties by state name" | Dissolve result with feature count | [ ] |
| 5.7 | Spatial join | "Join county attributes to each parcel based on location" | Spatial join result with feature count | [ ] |
| 5.8 | Merge | "Merge the north and south parcels into one dataset" | Merge result with feature count | [ ] |
| 5.9 | Project | "Reproject the cities layer to Web Mercator (EPSG:3857)" | Project result with feature count | [ ] |

#### 6. Map Production

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 6.1 | Create map | "Create a new map called Analysis Map" | Map creation confirmation | [ ] |
| 6.2 | Add layer to map | "Add the cities layer to the Analysis Map" | Layer added confirmation | [ ] |
| 6.3 | List map layers | "What layers are in the Analysis Map?" | List of layer names with data sources and counts | [ ] |
| 6.4 | Zoom to layer | "Zoom the Analysis Map to the cities layer" | Extent set confirmation | [ ] |
| 6.5 | Simple symbology | "Color the cities layer red" | Symbology applied confirmation | [ ] |
| 6.6 | Unique values symbology | "Color the land use layer by type field" | Unique values symbology confirmation | [ ] |
| 6.7 | Graduated colors symbology | "Show population as graduated colors on the counties layer" | Graduated colors symbology confirmation | [ ] |
| 6.8 | Set labels | "Label the cities with their names" | Label applied confirmation | [ ] |
| 6.9 | Export map to PNG | "Export the Analysis Map as PNG at 300 DPI" | PNG file created at specified path | [ ] |
| 6.10 | Remove layer | "Remove the temp_layer from the Analysis Map" | Layer removed confirmation | [ ] |

#### 7. Layout Production

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 7.1 | Create layout | "Create an A4 landscape layout called Final Map" | Layout creation confirmation | [ ] |
| 7.2 | Add map frame | "Add a map frame of the Analysis Map to the Final Map layout" | Map frame added confirmation | [ ] |
| 7.3 | Add title text | "Add a title 'City Analysis' to the Final Map layout" | Text element added confirmation | [ ] |
| 7.4 | Add legend | "Add a legend to the Final Map layout" | Legend added confirmation | [ ] |
| 7.5 | Add scale bar | "Add a scale bar to the Final Map layout" | Scale bar added confirmation | [ ] |
| 7.6 | Add north arrow | "Add a north arrow to the Final Map layout" | North arrow added confirmation | [ ] |
| 7.7 | Export layout to PDF | "Export the Final Map layout as PDF at 300 DPI" | PDF file created at specified path | [ ] |
| 7.8 | Export layout to PNG | "Export the Final Map layout as PNG at 150 DPI" | PNG file created at specified path | [ ] |

#### 8. Analysis

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 8.1 | Summary statistics | "Calculate sum, mean, min, and max of POP field in cities" | Statistics output table with computed values | [ ] |

#### 9. Chat Loop Integration

| # | Test Description | What to Say | Expected Result | Status |
|---|-----------------|-------------|-----------------|--------|
| 9.1 | Simple chat | "Hello, what can you help me with?" | Friendly introduction mentioning GIS capabilities | [ ] |
| 9.2 | Multi-turn conversation | "Set workspace to D:/data", then "What's in the workspace?" | Context preserved across turns, lists datasets | [ ] |
| 9.3 | Tool suggestion | After buffer operation, check for follow-up suggestion | Suggestion about overlay analysis appears | [ ] |
| 9.4 | Error handling | "Delete a file that doesn't exist" | Graceful error message, no crash | [ ] |
| 9.5 | Complex workflow | "Find all parcels within 500m of schools, export as map" | Multi-step execution with tool calls, final map export | [ ] |

### Test Completion Report

- **Date:** ___________
- **Tester:** ___________
- **Environment:** ArcGIS Pro version: _____ / MCP SDK version: _____
- **Total Tests:** 45
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___

### Notes

- Chinese character paths may cause arcpy.mp failures (known bug with arcpy)
- Map/Layout tools require arcpy.mp (may not work on systems with Chinese Windows usernames)
- All geoprocessing tools require a valid ArcGIS Pro license
- Workspace must exist before running workspace_set
