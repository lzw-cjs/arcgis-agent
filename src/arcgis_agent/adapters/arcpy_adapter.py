"""Real ArcPy adapter implementations with lazy import."""
from pathlib import Path
from typing import Any

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor, ILayoutDocument


class ArcPyGeoProcessor(IGeoProcessor):
    """Geoprocessing operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

        # Check out required license extensions (ROADMAP: CheckOutExtension + try/finally)
        self._checked_out_extensions = []
        for ext_name in ["spatial"]:
            try:
                status = self._arcpy.CheckExtension(ext_name)
                if status not in ("Available", "CheckedOut"):
                    continue
                if status == "CheckedOut":
                    self._checked_out_extensions.append(ext_name)
                    continue
                self._arcpy.CheckOutExtension(ext_name)
                self._checked_out_extensions.append(ext_name)
            except Exception:
                pass  # Non-fatal: individual tool calls will fail with clear arcpy errors if extension is truly needed

    def _check_crs_match(self, inputs: list[str]) -> None:
        """Verify all inputs share the same spatial reference (D-10, D-16).

        Raises UserError(code="CRS_MISMATCH") if inputs have different CRS.
        This is a pre-check before overlay operations (intersect/union/merge).
        When ArcPy is unavailable, ArcPyGeoProcessor cannot be constructed at all (D-16).
        """
        from arcgis_agent.exceptions import UserError

        codes = {}
        for fc in inputs:
            desc = self._arcpy.Describe(fc)
            sr = desc.spatialReference
            codes[fc] = (sr.factoryCode, sr.name)

        unique = set(code for code, _ in codes.values())
        if len(unique) > 1:
            details = ", ".join(
                f"{fc} ({name}, EPSG:{code})"
                for fc, (code, name) in codes.items()
            )
            raise UserError(
                code="CRS_MISMATCH",
                message=(
                    f"Input layers have different coordinate systems: {details}. "
                    f"Use 'data project' to reproject inputs to a common CRS first."
                ),
            )

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str,
               dissolve_field: str | None = None) -> Path:
        try:
            dist_str = f"{distance} {unit}"
            if dissolve_field:
                self._arcpy.analysis.Buffer(
                    input_fc, output_fc, dist_str,
                    dissolve_option="LIST", dissolve_field=[dissolve_field]
                )
            else:
                self._arcpy.analysis.Buffer(input_fc, output_fc, dist_str)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_BUFFER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def clip(self, input_fc: str, clip_fc: str,
             output_fc: str) -> Path:
        try:
            self._arcpy.analysis.Clip(input_fc, clip_fc, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_CLIP_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def intersect(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.analysis.Intersect(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_INTERSECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def select_by_attribute(self, input_fc: str, output_fc: str,
                            where_clause: str) -> Path:
        try:
            temp_layer = "temp_select_layer"
            self._arcpy.management.MakeFeatureLayer(input_fc, temp_layer)
            try:
                self._arcpy.management.SelectLayerByAttribute(
                    temp_layer, "NEW_SELECTION", where_clause
                )
                self._arcpy.management.CopyFeatures(temp_layer, output_fc)
            finally:
                self._arcpy.management.Delete(temp_layer)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_SELECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def union(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.analysis.Union(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_UNION_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def dissolve(self, input_fc: str, output_fc: str,
                 dissolve_field: str) -> Path:
        try:
            self._arcpy.management.Dissolve(
                input_fc, output_fc, dissolve_field
            )
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_DISSOLVE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def spatial_join(self, target_fc: str, join_fc: str,
                     output_fc: str) -> Path:
        try:
            self._arcpy.analysis.SpatialJoin(target_fc, join_fc, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_SPATIAL_JOIN_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def merge(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.management.Merge(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_MERGE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def project(self, input_fc: str, output_fc: str,
                spatial_reference: str) -> Path:
        try:
            sr = self._arcpy.SpatialReference(int(spatial_reference))
            self._arcpy.management.Project(input_fc, output_fc, sr)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_PROJECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def summary_statistics(self, input_fc: str, output_table: str,
                           statistics_fields: list[list[str]],
                           case_field: str | None = None) -> Path:
        try:
            if case_field:
                self._arcpy.analysis.Statistics(
                    input_fc, output_table, statistics_fields, case_field
                )
            else:
                self._arcpy.analysis.Statistics(
                    input_fc, output_table, statistics_fields
                )
            return Path(output_table)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_STATISTICS_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )


class ArcPyMapDocument(IMapDocument):
    """Map document operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def create_map(self, project_path: Path, map_name: str) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            aprx.createMap(map_name)
            aprx.save()
            return project_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_CREATE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def add_layer(self, project_path: Path, map_name: str,
                  layer_path: Path) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            m.addDataFromPath(str(layer_path))
            aprx.save()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_ADD_LAYER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def remove_layer(self, project_path: Path, map_name: str,
                     layer_name: str, layer_index: int | None = None) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            if layer_name:
                lyrs = m.listLayers(layer_name)
                if len(lyrs) == 0:
                    raise self._arcpy.ExecuteError(f"Layer not found: {layer_name}")
                lyr = lyrs[0]
            elif layer_index is not None:
                lyrs = m.listLayers()
                if layer_index < 0 or layer_index >= len(lyrs):
                    raise self._arcpy.ExecuteError(f"Layer index out of range: {layer_index}")
                lyr = lyrs[layer_index]
            else:
                raise self._arcpy.ExecuteError("Either layer_name or layer_index must be provided")
            m.removeLayer(lyr)
            aprx.save()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_REMOVE_LAYER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def list_layers(self, project_path: Path, map_name: str) -> list[dict]:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            result = []
            for lyr in m.listLayers():
                info = {"name": lyr.name, "datasource": "", "feature_count": 0}
                try:
                    info["datasource"] = lyr.dataSource if hasattr(lyr, 'dataSource') else str(lyr)
                except Exception:
                    info["datasource"] = str(lyr)
                try:
                    count_result = self._arcpy.GetCount_management(lyr)
                    info["feature_count"] = int(count_result[0])
                except Exception:
                    pass
                result.append(info)
            return result
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_LIST_LAYERS_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def set_extent(self, project_path: Path, map_name: str,
                   zoom_to_layer: str) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            lyr = m.listLayers(zoom_to_layer)[0]
            lyr_extent = self._arcpy.Describe(lyr).extent
            tmp_lyt = aprx.createLayout(210, 297, "MILLIMETER", "__gsd_tmp_extent")
            mf = tmp_lyt.createMapFrame(tmp_lyt.pageBounds, m, "__gsd_tmp_mf")
            mf.camera.setExtent(lyr_extent)
            aprx.save()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_SET_EXTENT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def symbolize_layer(self, project_path: Path, map_name: str,
                        layer_name: str, symbology_config: dict) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            lyr = m.listLayers(layer_name)[0]
            sym_type = symbology_config.get("type", "simple")

            sym = lyr.symbology

            if sym_type == "simple":
                color = symbology_config.get("color", [0, 0, 0])
                outline = symbology_config.get("outline_color", [0, 0, 0])
                size = symbology_config.get("size", 8)
                opacity = symbology_config.get("opacity", 100)
                sym.updateRenderer('SimpleRenderer')
                sym.renderer.symbol.color = {'RGB': [*color, opacity]}
                sym.renderer.symbol.outlineColor = {'RGB': [*outline, 100]}
                sym.renderer.symbol.size = size

            elif sym_type == "unique_values":
                field = symbology_config.get("field")
                if not field:
                    raise ValueError("unique_values symbology requires --field")
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = [field]
                color_ramp_name = symbology_config.get("color_ramp")
                if color_ramp_name:
                    ramps = aprx.listColorRamps(f"*{color_ramp_name}*")
                    if ramps:
                        sym.renderer.colorRamp = ramps[0]
                manual_values = symbology_config.get("values")
                if manual_values:
                    for grp in sym.renderer.groups:
                        for itm in grp.items:
                            val_key = str(itm.values[0][0])
                            for mv in manual_values:
                                if str(mv.get("value")) == val_key:
                                    c = mv.get("color")
                                    if c:
                                        itm.symbol.color = {'RGB': [*c, 100]}
                                    sz = mv.get("size")
                                    if sz is not None:
                                        itm.symbol.size = sz

            elif sym_type == "graduated_colors":
                field = symbology_config.get("field")
                if not field:
                    raise ValueError("graduated_colors symbology requires --field")
                sym.updateRenderer('GraduatedColorsRenderer')
                renderer = sym.renderer
                renderer.classificationField = field
                renderer.breakCount = symbology_config.get("break_count", 5)
                renderer.classificationMethod = symbology_config.get(
                    "classification_method", "NaturalBreaks"
                )
                color_ramp_name = symbology_config.get("color_ramp")
                if color_ramp_name:
                    ramps = aprx.listColorRamps(f"*{color_ramp_name}*")
                    if ramps:
                        renderer.colorRamp = ramps[0]
                outline = symbology_config.get("outline_color")
                if outline:
                    for brk in renderer.classBreaks:
                        brk.symbol.outlineColor = {'RGB': [*outline, 100]}

            else:
                raise ValueError(f"Unsupported symbology type: {sym_type}")

            lyr.symbology = sym
            aprx.save()

        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_SYMBOLIZE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def set_label(self, project_path: Path, map_name: str,
                  layer_name: str, label_config: dict) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            lyr = m.listLayers(layer_name)[0]

            if not lyr.supports("SHOWLABELS"):
                raise self._arcpy.ExecuteError(
                    f"Layer '{layer_name}' does not support labeling"
                )

            field = label_config.get("field")
            if not field:
                raise ValueError("label requires --field")
            font_size = label_config.get("font_size", 10)
            color = label_config.get("color", [0, 0, 0])
            bold = label_config.get("bold", False)

            lyr.showLabels = True
            for lblClass in lyr.listLabelClasses():
                lblClass.expression = f"[{field}]"
                lblClass.visible = True

            try:
                cim = lyr.getDefinition("V3")
                for lblClass in cim.labelClasses:
                    if hasattr(lblClass, 'textSymbol') and lblClass.textSymbol:
                        sym = lblClass.textSymbol.symbol
                        sym.fontFamilyName = "Arial"
                        sym.fontSize = font_size
                        sym.symbol.color = {'RGB': [*color, 100]}
                        if bold:
                            sym.fontStyle = "Bold"
                lyr.setDefinition(cim)
            except Exception:
                pass

            aprx.save()

        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_SET_LABEL_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def export_map(self, project_path: Path, map_name: str,
                   output_path: Path, format: str, dpi: int,
                   transparent: bool = False) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            fmt = format.upper()
            if fmt == "PNG":
                m.exportToPNG(
                    str(output_path),
                    resolution=dpi,
                    transparent_background=transparent,
                    world_file=False,
                )
            elif fmt == "PDF":
                m.exportToPDF(
                    str(output_path),
                    resolution=dpi,
                    image_quality="BEST",
                    embed_fonts=True,
                )
            else:
                raise ValueError(f"Unsupported export format: {format}. Use PNG or PDF.")
            return output_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_EXPORT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx


class ArcPyDataAccessor(IDataAccessor):
    """Data access operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def list_feature_classes(self, workspace: Path) -> list[str]:
        try:
            self._arcpy.env.workspace = str(workspace)
            return self._arcpy.ListFeatureClasses()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_LIST_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def describe(self, dataset_path: Path) -> dict[str, Any]:
        try:
            desc = self._arcpy.Describe(str(dataset_path))
            return {
                "dataType": desc.dataType,
                "name": desc.name,
                "catalogPath": desc.catalogPath,
            }
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_DESCRIBE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def convert(self, input_path: Path, output_path: Path,
                output_format: str) -> Path:
        try:
            self._arcpy.conversion.FeatureClassToFeatureClass(
                str(input_path), str(output_path.parent),
                output_path.name
            )
            return output_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_CONVERT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def get_count(self, dataset_path) -> int:
        try:
            result = self._arcpy.management.GetCount(str(dataset_path))
            return int(result[0])
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_COUNT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )


class ArcPyLayoutDocument(ILayoutDocument):
    """Layout document operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def create_layout(self, project_path: Path, layout_name: str,
                      page_width: float, page_height: float,
                      page_units: str) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            aprx.createLayout(page_width, page_height, page_units, layout_name)
            aprx.save()
            return project_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="LAYOUT_CREATE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def add_element(self, project_path: Path, layout_name: str,
                    element_type: str, element_config: dict) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            lyt = aprx.listLayouts(layout_name)[0]
            m = aprx.listMaps()[0]  # Default: first map

            x = element_config.get("x", 0.5)
            y = element_config.get("y", 10.5)
            w = element_config.get("width", 6.0)
            h = element_config.get("height", 1.0)
            geometry = self._arcpy.CreateObject("Array", [
                self._arcpy.CreateObject("Point", x, y),
                self._arcpy.CreateObject("Point", x + w, y + h),
            ])

            position = element_config.get("position")
            if position:
                pw = lyt.pageWidth
                ph = lyt.pageHeight
                presets = {
                    "top-left":     (0.5, ph - h - 0.5),
                    "top-center":   ((pw - w) / 2, ph - h - 0.5),
                    "top-right":    (pw - w - 0.5, ph - h - 0.5),
                    "center-left":  (0.5, (ph - h) / 2),
                    "center":       ((pw - w) / 2, (ph - h) / 2),
                    "center-right": (pw - w - 0.5, (ph - h) / 2),
                    "bottom-left":  (0.5, 0.5),
                    "bottom-center":((pw - w) / 2, 0.5),
                    "bottom-right": (pw - w - 0.5, 0.5),
                }
                if position in presets:
                    px, py = presets[position]
                    x, y = (px, py)
                    geometry = self._arcpy.CreateObject("Array", [
                        self._arcpy.CreateObject("Point", x, y),
                        self._arcpy.CreateObject("Point", x + w, y + h),
                    ])

            if element_type == "text":
                text = element_config.get("text", "")
                font_size = element_config.get("font_size", 12)
                color_rgb = element_config.get("color", [0, 0, 0])
                bold = element_config.get("bold", False)
                italic = element_config.get("italic", False)
                txt = aprx.createTextElement(
                    lyt, geometry, "TEXT", text, font_size, "Arial",
                    "Bold" if bold else "Regular", None, text[:50]
                )
                if italic:
                    try:
                        cim = txt.getDefinition("V3")
                        cim.textSymbol.symbol.fontStyle = "Italic"
                        txt.setDefinition(cim)
                    except Exception:
                        pass

            elif element_type == "legend":
                title = element_config.get("title", "Legend")
                mf = lyt.listElements("MAPFRAME_ELEMENT")[0]
                lyt.createMapSurroundElement(geometry, "LEGEND", mf, title)

            elif element_type == "scale-bar":
                style = element_config.get("style", "Alternating")
                style_map = {
                    "Alternating": "Alternating Scale Bar 1",
                    "Bar": "Scale Bar 1",
                    "DoubleAlternating": "Double Alternating Scale Bar 1",
                }
                scale_style = style_map.get(style, "Alternating Scale Bar 1")
                mf = lyt.listElements("MAPFRAME_ELEMENT")[0]
                lyt.createMapSurroundElement(geometry, "SCALE_BAR", mf,
                                             scale_style, "Scale Bar")

            elif element_type == "north-arrow":
                style = element_config.get("style", "Default")
                style_map = {
                    "Default": "ArcGIS 2D",
                    "Arrow": "ArcGIS 2D North 1",
                }
                arrow_style = style_map.get(style, "ArcGIS 2D")
                mf = lyt.listElements("MAPFRAME_ELEMENT")[0]
                lyt.createMapSurroundElement(geometry, "NORTH_ARROW", mf,
                                             arrow_style, "North Arrow")

            elif element_type == "map-frame":
                map_name = element_config.get("map", m.name)
                target_map = aprx.listMaps(map_name)[0]
                extent_mode = element_config.get("extent", "full_extent")
                mf = lyt.createMapFrame(geometry, target_map, "Map Frame")
                if extent_mode == "full_extent":
                    mf.camera.setExtent(mf.getLayerExtent(target_map, True, True))

            elif element_type == "image":
                source = element_config.get("source", "")
                if not source:
                    raise ValueError("image element requires --source path")
                img_path = Path(source)
                if not img_path.exists():
                    raise self._arcpy.ExecuteError(f"Image file not found: {source}")
                aprx.createPictureElement(lyt, geometry, str(img_path),
                                          img_path.stem, True)

            else:
                raise ValueError(
                    f"Unsupported element type: {element_type}. "
                    f"Use: text, legend, scale-bar, north-arrow, map-frame, image"
                )
            aprx.save()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="LAYOUT_ADD_ELEMENT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx

    def export_layout(self, project_path: Path, layout_name: str,
                      output_path: Path, format: str, dpi: int,
                      **kwargs) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            lyt = aprx.listLayouts(layout_name)[0]
            fmt = format.upper()
            if fmt == "PNG":
                lyt.exportToPNG(
                    str(output_path),
                    resolution=dpi,
                    transparent_background=kwargs.get("transparent", False),
                )
            elif fmt == "PDF":
                lyt.exportToPDF(
                    str(output_path),
                    resolution=dpi,
                    image_quality="BEST",
                    embed_fonts=True,
                )
            else:
                raise ValueError(f"Unsupported export format: {format}. Use PNG or PDF.")
            return output_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="LAYOUT_EXPORT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx
