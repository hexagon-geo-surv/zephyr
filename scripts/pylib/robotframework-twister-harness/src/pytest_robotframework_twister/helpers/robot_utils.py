"""Utility functions for Robot Framework integration."""
import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def create_robot_variable_file(variables: dict[str, Any]) -> str:
    """Create a temporary Robot Framework variable file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as var_file:
        var_file.write("def get_variables():\n")
        var_file.write("    return {\n")
        for key, value in variables.items():
            var_file.write(f'        "{key}": "{value}",\n')
        var_file.write("    }\n")
        return var_file.name


def validate_robot_test_file(test_file: Path) -> bool:
    """Validate that a Robot Framework test file exists and is accessible."""
    if not test_file.exists():
        logger.error(f"Robot Framework test file not found: {test_file}")
        return False

    if not test_file.is_file():
        logger.error(f"Robot Framework test path is not a file: {test_file}")
        return False

    return True
