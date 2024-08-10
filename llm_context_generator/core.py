from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pathspec

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Context:
    def __init__(
        self,
        root_path: Path,
        ignore: Optional[Union[str, Path, List[Union[str, Path]]]] = None,
    ):
        self.root_path = root_path.resolve()
        self.ignore = ignore
        self._ignore_patterns = self._load_ignore_patterns(ignore) if ignore else None
        self._included: set[Path] = set()
        logger.debug(f"Initialized Context with root path: {self.root_path}")

    @staticmethod
    def _load_ignore_patterns(
        ignore: Union[str, Path, List[Union[str, Path]]]
    ) -> pathspec.PathSpec:
        """Load ignore patterns."""
        lines = []

        if not isinstance(ignore, List):
            ignore = [ignore]

        for i in ignore:
            if isinstance(i, str):
                lines.extend(i.splitlines())
            elif isinstance(i, Path):
                if i.exists() and i.is_file():
                    lines.extend(i.read_text().splitlines())

        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    def _is_ignored(self, path: Path) -> bool:
        """Check if a path matches any ignore patterns."""
        if self._ignore_patterns:
            relative_path = path.relative_to(self.root_path)
            return self._ignore_patterns.match_file(str(relative_path))
        return False

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

            if self._is_ignored(resolved_value):
                logger.debug(f"Ignored path: {resolved_value}")
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

                        if self._is_ignored(resolved_value):
                            logger.debug(f"Ignored path: {resolved_value}")
                            continue

                        if resolved_value not in self._included:
                            self._included.add(resolved_value)
                            logger.debug(f"File added: {resolved_value}")

    def remove(self, *values: Path) -> None:
        """Remove a Path object from the context.

        Args:
            values (Path, ...): Paths to remove from the context.
        """
        for value in values:
            resolved_value = value.resolve()

            if resolved_value.is_file():
                if resolved_value in self._included:
                    self._included.remove(resolved_value)
                    logger.debug(f"File removed: {resolved_value}")
            elif resolved_value.is_dir():
                self._included = {
                    file
                    for file in self._included
                    if not file.is_relative_to(resolved_value)
                }
                logger.debug(f"Directory removed and its files: {resolved_value}")

    def drop(self) -> None:
        self._included = set()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__!s}"
            f"(root_path={self.root_path!r}, ignore={self.ignore!r})"
        )
