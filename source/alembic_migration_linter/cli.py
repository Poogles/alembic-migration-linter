from __future__ import annotations

import sys
from pathlib import Path

import click

from .config import get_linter_config, parse_alembic_config
from .linter import AlembicMigrationLinter


@click.command()
@click.option(
    "--config",
    "-c",
    default="alembic.ini",
    type=click.Path(exists=True),
    help="Path to alembic.ini",
)
@click.option(
    "--dialect",
    "-d",
    default=None,
    help="Target database dialect",
)
@click.option(
    "--revision",
    "-r",
    default=None,
    help="Lint a single revision",
)
@click.option(
    "--since-revision",
    "-s",
    default=None,
    help="Lint only migrations after this revision",
)
@click.option(
    "--exclude-test",
    "-e",
    multiple=True,
    help="Exclude a test code (e.g., ALTER_COLUMN)",
)
@click.option(
    "--warnings-as-errors",
    is_flag=True,
    default=None,
    help="Treat all warnings as errors",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress OK output",
)
@click.option(
    "--ignore-revision",
    "ignore_revisions",
    multiple=True,
    help="Skip migration by revision ID (can be specified multiple times)",
)
@click.option(
    "--ignore-revision-contains",
    "ignore_revision_contains",
    default=None,
    help="Skip migrations whose revision ID or filename contains this string",
)
def main(
    config: str,
    dialect: str | None,
    revision: str | None,
    since_revision: str | None,
    exclude_test: tuple[str, ...],
    warnings_as_errors: bool | None,
    no_cache: bool,
    quiet: bool,
    ignore_revisions: tuple[str, ...],
    ignore_revision_contains: str | None,
) -> None:
    """Detect backward incompatible Alembic migrations."""
    config_path = Path(config)

    # Load [linters] section from alembic.ini
    ini_config = parse_alembic_config(config_path)
    linter_config = get_linter_config(ini_config)

    # CLI options override config file
    effective_dialect = dialect or linter_config.get("dialect", "postgresql")

    exclude_tests = list(exclude_test)
    if "exclude_tests" in linter_config:
        config_excludes = [
            code.strip()
            for code in linter_config["exclude_tests"].split(",")
            if code.strip()
        ]
        exclude_tests.extend(config_excludes)

    if warnings_as_errors is None:
        warnings_as_errors = (
            linter_config.get("warnings_as_errors", "false").lower() == "true"
        )

    linter = AlembicMigrationLinter(
        config_path=config_path,
        dialect=effective_dialect,
        exclude_tests=exclude_tests,
        no_cache=no_cache,
        ignore_revisions=list(ignore_revisions),
        ignore_revision_contains=ignore_revision_contains,
    )

    if revision:
        migration = linter.loader.get_migration(revision)
        if not migration:
            click.echo(f"Revision {revision!r} not found", err=True)
            sys.exit(1)
        results = [linter.lint_migration(migration)]
    else:
        results = linter.lint_all(since_revision=since_revision)

    valid = erroneous = warned = skipped = 0
    for result in results:
        if result.skipped:
            click.echo(f"({result.migration_revision})... IGNORE")
            skipped += 1
            continue

        error_codes = [e.code for e in result.errors]
        warning_codes = [w.code for w in result.warnings]

        if warnings_as_errors:
            error_codes.extend(warning_codes)
            warning_codes = []

        if error_codes:
            click.echo(f"({result.migration_revision})... ERR")
            for code in error_codes:
                click.echo(f"\t{code}")
            erroneous += 1
        elif warning_codes:
            click.echo(f"({result.migration_revision})... WARNING")
            for code in warning_codes:
                click.echo(f"\t{code}")
            warned += 1
        else:
            if not quiet:
                click.echo(f"({result.migration_revision})... OK")
            valid += 1

    total = valid + erroneous + warned + skipped
    click.echo("")
    click.echo("*** Summary ***")
    click.echo(f"Valid migrations: {valid}/{total}")
    click.echo(f"Erroneous migrations: {erroneous}/{total}")
    click.echo(f"Migrations with warnings: {warned}/{total}")
    click.echo(f"Ignored migrations: {skipped}/{total}")

    if erroneous > 0:
        sys.exit(1)
