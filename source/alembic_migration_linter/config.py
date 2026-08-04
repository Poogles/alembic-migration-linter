from __future__ import annotations

import configparser
from pathlib import Path


def parse_alembic_config(config_path: str | Path) -> configparser.ConfigParser:
    """Parse alembic.ini and return the ConfigParser instance."""
    config = configparser.ConfigParser()
    config.read(str(config_path))
    return config


def get_linter_config(config: configparser.ConfigParser) -> dict[str, str]:
    """Extract [linters] section from alembic.ini config."""
    result: dict[str, str] = {}
    if config.has_section("linters"):
        result = dict(config.items("linters"))
    return result
