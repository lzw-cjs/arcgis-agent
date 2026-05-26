"""Base service class with adapter dependency injection."""
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor, ILayoutDocument


class BaseService:
    """Base class for all services.

    Accepts optional adapter instances for dependency injection.
    When not provided, lazily creates real ArcPy adapters.
    Subclasses use self._gp, self._map, self._data, self._layout to access adapters.

    Usage:
        # Production (lazy real adapters):
        svc = BaseService()

        # Testing (injected mocks):
        svc = BaseService(
            gp=MockGeoProcessor(),
            map_doc=MockMapDocument(),
            data=MockDataAccessor(),
            layout_doc=MockLayoutDocument(),
        )
    """

    def __init__(
        self,
        gp: IGeoProcessor | None = None,
        map_doc: IMapDocument | None = None,
        data: IDataAccessor | None = None,
        layout_doc: ILayoutDocument | None = None,
    ):
        self._gp = gp if gp is not None else self._make_gp()
        self._map = map_doc if map_doc is not None else self._make_map()
        self._data = data if data is not None else self._make_data()
        self._layout = layout_doc if layout_doc is not None else self._make_layout()

    @staticmethod
    def _make_gp() -> IGeoProcessor:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyGeoProcessor
        return ArcPyGeoProcessor()

    @staticmethod
    def _make_map() -> IMapDocument:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyMapDocument
        return ArcPyMapDocument()

    @staticmethod
    def _make_data() -> IDataAccessor:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyDataAccessor
        return ArcPyDataAccessor()

    @staticmethod
    def _make_layout() -> ILayoutDocument:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyLayoutDocument
        return ArcPyLayoutDocument()
