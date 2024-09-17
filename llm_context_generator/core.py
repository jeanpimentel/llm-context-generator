from __future__ import annotations

import json
import logging
import os
import typing as t
from pathlib import Path

import pathspec

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Context:
    def __init__(
        self,
        root_path: Path,
        ignore: t.Optional[str | Path | t.List[str | Path]] = None,
    ):
        self.root_path = root_path.resolve()
        self.ignore = ignore
        self._ignore_patterns = self._load_ignore_patterns(ignore) if ignore else None
        self._included: set[Path] = set()
        logger.debug(f"Initialized Context with root path: {self.root_path}")

    @staticmethod
    def _load_ignore_patterns(
        ignore: str | Path | t.List[str | Path],
    ) -> pathspec.PathSpec:
        """Load ignore patterns."""
        lines = []

        if not isinstance(ignore, list):
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

    def list(self, relative: bool = True) -> str:
        """List all Path objects in the context."""
        return "\n".join(
            [
                str(
                    p.absolute()
                    if not relative
                    else p.absolute().relative_to(self.root_path)
                )
                for p in sorted(self._included)
            ]
        )

    def tree(self) -> str:
        tree: t.Dict[str, t.Any] = {}
        for path in [
            path.absolute().relative_to(self.root_path) for path in self._included
        ]:
            self._add_path_to_tree(tree, path.parts)

        if not tree:
            return ""

        return f".\n{self._build_tree_string(tree)}\n"

    def _add_path_to_tree(
        self,
        tree: t.Dict[str, t.Any],
        parts: t.Tuple[str, ...],
    ) -> None:
        if len(parts) == 1:
            tree[parts[0]] = None
        else:
            if parts[0] not in tree:
                tree[parts[0]] = {}
            self._add_path_to_tree(tree[parts[0]], parts[1:])

    def _build_tree_string(
        self,
        tree: t.Dict[str, t.Any],
        prefix: str = "",
    ) -> str:
        result = []
        keys = sorted(tree.keys())

        for i, key in enumerate(keys):
            subtree = tree[key]
            connector = "└── " if i == len(keys) - 1 else "├── "
            result.append(f"{prefix}{connector}{key}")
            if subtree is not None:
                extension = "    " if i == len(keys) - 1 else "│   "
                result.append(self._build_tree_string(subtree, prefix + extension))

        return "\n".join(result)

    def generate(self) -> str:
        if not self._included:
            logger.debug("No files in the context")
            return ""

        def wrap_code(file: Path) -> str:
            return "\n".join(
                [
                    f"### `{file.absolute().relative_to(self.root_path)}`",
                    f"````{file.suffix[1:] if file.suffix else ''}",
                    f"{file.read_text()}",
                    "````\n",
                ]
            )

        content = [
            "## Context - Relevant files\n",
            f"````\n{self.tree()}````\n" "",
        ]

        for path in sorted(self._included):
            try:
                content.append(wrap_code(path))
            except UnicodeDecodeError as e:
                logger.error(f"Could not read: {path}: {e}")

        return "\n".join(content)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__!s}"
            f"(root_path={self.root_path!r}, ignore={self.ignore!r})"
        )

    def __eq__(self, other: t.Any) -> bool:
        return isinstance(other, Context) and self.to_json() == other.to_json()

    def to_json(self) -> str:
        if not self.ignore:
            ignore = []
        elif isinstance(self.ignore, list):
            ignore = self.ignore
        else:
            ignore = [self.ignore]

        return json.dumps(
            {
                "root": str(self.root_path),
                "ignore": [
                    f"{'str' if isinstance(i, str) else 'path'}::{i}" for i in ignore
                ],
                "files": list(map(str, sorted(self._included))),
            },
            indent=4,
        )

    @classmethod
    def from_json(cls, data: str) -> Context:
        decoded_data: t.Dict[str, t.Any] = json.loads(data)

        ignore: t.List[str | Path] = []
        for i in decoded_data["ignore"]:
            type_, content = i.split("::")
            if type_ == "path":
                ignore.append(Path(content))
            else:
                ignore.append(content)

        ctx = Context(root_path=Path(decoded_data["root"]), ignore=ignore)
        if decoded_data["files"]:
            ctx.add(*map(Path, decoded_data["files"]))

        return ctx
