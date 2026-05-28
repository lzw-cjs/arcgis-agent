"""Environment check script for arcgis-agent.

Verifies that the runtime environment meets all requirements:
  - Python >= 3.9
  - arcpy importable
  - ArcGIS Pro license valid
  - arcgis-agent package installed

Usage:
    python scripts/check-env.py
    conda run -n arcgis-agent python scripts/check-env.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""
from __future__ import annotations

import sys


def _check_python_version() -> tuple[bool, str]:
    if sys.version_info >= (3, 9):
        return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return False, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (need >= 3.9)"


def _check_arcpy() -> tuple[bool, str]:
    try:
        import arcpy  # noqa: F401
        return True, "arcpy importable"
    except ImportError:
        return False, "arcpy not found — ArcGIS Pro must be installed and its Python environment activated"


def _check_license() -> tuple[bool, str]:
    try:
        import arcpy
        product_info = arcpy.ProductInfo()
        if product_info:
            return True, f"ArcGIS Pro license: {product_info}"
        return False, "ArcGIS Pro license not available — check that Pro is licensed and logged in"
    except Exception as e:
        return False, f"License check failed: {e}"


def _check_package() -> tuple[bool, str]:
    try:
        import arcgis_agent
        version = getattr(arcgis_agent, "__version__", "unknown")
        return True, f"arcgis-agent {version} installed"
    except ImportError:
        return False, "arcgis-agent not installed — run: pip install ."


def main() -> None:
    checks = [
        ("Python version", _check_python_version),
        ("arcpy", _check_arcpy),
        ("ArcGIS license", _check_license),
        ("arcgis-agent package", _check_package),
    ]

    all_passed = True
    for name, fn in checks:
        ok, msg = fn()
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_passed = False

    print()
    if all_passed:
        print("All checks passed. arcgis-agent is ready to use.")
        sys.exit(0)
    else:
        print("Some checks failed. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
