"""Environment detection: check arcpy availability and license status."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentStatus:
    """Result of environment check."""
    available: bool
    message: str
    arcpy_version: str | None = None
    license_level: str | None = None


def check_environment() -> EnvironmentStatus:
    """Check if arcpy is available and license is valid.

    Returns EnvironmentStatus with:
    - available=True if arcpy imports and GetInstallInfo() works
    - available=False with helpful message if arcpy is missing or broken
    """
    try:
        import arcpy
        info = arcpy.GetInstallInfo()
        version = info.get("Version", "unknown")
        license_level = info.get("LicenseLevel", "unknown")
        return EnvironmentStatus(
            available=True,
            message=f"ArcGIS Pro {version} ({license_level})",
            arcpy_version=version,
            license_level=license_level,
        )
    except ImportError:
        return EnvironmentStatus(
            available=False,
            message=(
                "arcpy not found. Run inside ArcGIS Pro Python environment.\n"
                "Activate with: proenv.bat  or  conda activate arcgispro-py3"
            ),
        )
    except Exception as e:
        return EnvironmentStatus(
            available=False,
            message=f"arcpy error: {e}",
        )
