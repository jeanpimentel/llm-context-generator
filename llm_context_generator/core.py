from __future__ import annotations

import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Context:
    def __init__(
        self,
        root_path: Path,
    ):
        self.root_path = root_path.resolve()
        self._included: set[Path] = set()
        logger.debug(f"Initialized Context with root path: {self.root_path}")

    def add(self, *values: Path) -> None:
        """Add multiple Path objects to the context.

        Args:
            values (Path, ...): Paths to add to the context.
        """
        for value in values:
            resolved_value = value.resolve()
            if not resolved_value.is_relative_to(self.root_path):
                error_msg = (
                    f"Path {resolved_value} is not under the root path {self.root_path}"
                )
                logger.error(error_msg)
                continue

            if resolved_value.is_file():
                if resolved_value not in self._included:
                    self._included.add(resolved_value)
                    logger.debug(f"File added: {resolved_value}")

            elif resolved_value.is_dir():
                for root, _, files in os.walk(resolved_value):
                    for file in files:
                        resolved_value = (Path(root) / file).resolve()

                        if not resolved_value.is_relative_to(self.root_path):
                            error_msg = f"Path {resolved_value} is not under the root path {self.root_path}"
                            logger.error(error_msg)
                            continue

                        if resolved_value not in self._included:
                            self._included.add(resolved_value)
                            logger.debug(f"File added: {resolved_value}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__!s}(root_path={self.root_path!r})"
