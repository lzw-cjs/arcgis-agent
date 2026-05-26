"""Click main entry point for arcgis-agent CLI."""
import sys
import click
from arcgis_agent import __version__

# Force UTF-8 on Windows to prevent GBK encoding crashes (Pitfall #1)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="arcgis-agent")
@click.option("--json", "output_json", is_flag=True, default=False,
              help="Output results as JSON.")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging (DEBUG level to stderr).")
@click.option("--quiet", "-q", is_flag=True, default=False,
              help="Suppress non-error output.")
@click.pass_context
def cli(ctx, output_json, verbose, quiet):
    """AI Agent CLI for ArcGIS Pro automation."""
    if verbose and quiet:
        click.echo("Error: --verbose and --quiet are mutually exclusive.",
                    err=True)
        sys.exit(1)
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    from arcgis_agent.logging_config import setup_logging
    setup_logging(verbose=verbose, quiet=quiet)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def main():
    """Entry point with exit code mapping."""
    try:
        cli()
    except click.exceptions.Exit:
        raise
    except click.Abort:
        sys.exit(1)
    except Exception as e:
        from arcgis_agent.exceptions import (
            UserError, SystemError_, ArcGISError
        )
        from arcgis_agent.models import Result
        if isinstance(e, ArcGISError):
            click.echo(Result.from_exception(e).to_json())
            sys.exit(3)
        elif isinstance(e, SystemError_):
            click.echo(Result.from_exception(e).to_json())
            sys.exit(2)
        elif isinstance(e, UserError):
            click.echo(Result.from_exception(e).to_json())
            sys.exit(1)
        else:
            raise


from arcgis_agent.plugins import load_plugins
load_plugins(cli)
