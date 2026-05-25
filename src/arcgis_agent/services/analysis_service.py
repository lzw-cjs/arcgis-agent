"""Analysis service: summary statistics (GEO-10)."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


VALID_STATS = {"SUM", "MEAN", "MIN", "MAX", "COUNT", "STD", "MEDIAN"}


def parse_stat_fields(field_spec: str) -> list[list[str]]:
    """Parse 'pop:SUM,area:MEAN' into [['pop','SUM'],['area','MEAN']].

    Per D-14: field:STAT syntax, comma-separated.
    """
    result = []
    for item in field_spec.split(","):
        parts = item.strip().split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid field:STAT syntax: '{item}'. Expected 'field:STAT'."
            )
        field, stat = parts[0].strip(), parts[1].strip().upper()
        if stat not in VALID_STATS:
            raise ValueError(
                f"Invalid stat type: '{stat}'. Valid: {', '.join(sorted(VALID_STATS))}"
            )
        result.append([field, stat])
    return result


class AnalysisService(BaseService):
    """Analysis operations (GEO-10).

    Uses self._gp (IGeoProcessor) for summary_statistics
    and self._data (IDataAccessor) for get_count on output tables.
    """

    def __init__(self, gp=None, data=None):
        super().__init__(gp=gp, data=data)

    def summary_statistics(self, input_fc: str,
                           field_spec: str,
                           case_field: str | None = None,
                           no_overwrite: bool = False,
                           output_table: str | None = None) -> Result:
        """Compute summary statistics (GEO-10).

        Args:
            input_fc: Input feature class or table path.
            field_spec: Field:STAT specification (e.g., "pop:SUM,area:MEAN").
                        Per D-14: comma-separated field:stat pairs.
            case_field: Optional field to group by (per D-15).
            no_overwrite: Fail if output exists.
            output_table: Output table path. If None, auto-generate from input name.
        """
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")

        # Parse field:STAT syntax (D-14)
        try:
            statistics_fields = parse_stat_fields(field_spec)
        except ValueError as e:
            return Result.error(code="INVALID_FIELD_SPEC",
                                message=str(e))

        # Auto-generate output path if not provided
        if output_table is None:
            output_table = str(p_in.parent / f"{p_in.stem}_stats")

        if no_overwrite and Path(output_table).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_table}")

        t0 = time.perf_counter()
        try:
            result_path = self._gp.summary_statistics(
                input_fc, output_table, statistics_fields,
                case_field=case_field
            )
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Statistics computed: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)
