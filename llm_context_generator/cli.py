import pathlib
import shutil
import sys
import typing as t
from functools import lru_cache
from pathlib import Path

import click

from llm_context_generator import Context, __version__

_CTX_DIR_NAME = ".ctx"
_CTX_METADATA = "ctx.json"
_CTX_OUTPUT = "ctx.md"


def get_ctx_dir() -> Path:
    root = _find_root(start_path=Path.cwd())
    if not root:
        click.secho(
            "Context not found. Please initialize with the init command.",
            fg="red",
            bold=True,
        )
        sys.exit(-1)

    return root / _CTX_DIR_NAME


@lru_cache
def _find_root(start_path: Path) -> t.Optional[Path]:
    current_path = Path(start_path).resolve()
    while current_path:
        target_folder = current_path / _CTX_DIR_NAME
        if target_folder.exists() and target_folder.is_dir():
            return target_folder.parent.absolute()

        if current_path == current_path.parent or current_path.parent == Path.home():
            break

        current_path = current_path.parent

    return None


def get_ctx() -> Context:
    ctx_data = get_ctx_dir() / _CTX_METADATA
    if not ctx_data.exists():
        click.secho(
            "Context not found. Please initialize with the init command.",
            fg="red",
            bold=True,
        )
        sys.exit(-1)

    return Context.from_json(ctx_data.read_text())


def save_ctx(context: Context) -> None:
    ctx_json = get_ctx_dir() / _CTX_METADATA
    ctx_json.write_text(context.to_json())

    ctx_md = get_ctx_dir() / _CTX_OUTPUT
    ctx_md.write_text(context.generate())


def init_ctx(root: Path) -> None:
    ctx_dir = root / _CTX_DIR_NAME
    if ctx_dir.exists():
        click.secho(
            f"Directory already exists: {_CTX_DIR_NAME}. If needed, run destroy command first.",
            fg="yellow",
        )
        return
    else:
        ctx_dir.mkdir(parents=True)

    ctx = Context(
        root_path=root,
        ignore=[
            Path.home() / ".gitignore",  # Try global gitignore
            root / ".gitignore",  # Try local gitignore
            ".git",
            ".ctx",
        ],
    )
    save_ctx(ctx)

    click.secho("Context initialized.", fg="green", bold=True)


def destroy_ctx() -> None:
    shutil.rmtree(get_ctx_dir())


class OrderCommands(click.Group):
    def list_commands(self, ctx: click.Context) -> t.List[str]:
        return list(self.commands)


@click.group(
    cls=OrderCommands,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def cli() -> None:
    """LLM Context Generator."""
    pass


@cli.command()
def init() -> None:
    """Initialize a context."""
    init_ctx(root=Path.cwd())


@cli.command()
def destroy() -> None:
    """Remove the context."""
    destroy_ctx()


@cli.command(
    short_help="Add files to the context. Run add --help to see more.",
    no_args_is_help=True,
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        path_type=pathlib.Path,
    ),
    is_eager=True,
    metavar="[FILES...]",
    required=True,
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
def add(
    src: t.Tuple[Path, ...],
    verbose: bool = False,
) -> None:
    """Add files to the context.

    \b
    <FILES>...
        Files that should be added to the context for the LLM. Fileglobs (e.g. *.c) can be given to add all matching files. Also a leading directory name (e.g. dir to add dir/file1 and dir/file2).
    """
    ctx = get_ctx()
    ctx.add(*src)
    save_ctx(ctx)


@cli.command(
    short_help="Remove files from the context. Run remove --help to see more.",
    no_args_is_help=True,
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        path_type=pathlib.Path,
    ),
    is_eager=True,
    metavar="[FILES...]",
    required=False,
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
def remove(
    src: t.Tuple[Path, ...],
    verbose: bool = False,
) -> None:
    """Remove files from the context.

    \b
    <FILES>...
        Files that should be removed from the context for the LLM. Fileglobs (e.g. *.c) can be given to remove all matching files. Also a leading directory name (e.g. dir to add dir/file1 and dir/file2).
    """
    ctx = get_ctx()
    ctx.remove(*src)
    save_ctx(ctx)


@cli.command()
def reset() -> None:
    """Reset the context removing all files."""
    ctx = get_ctx()
    ctx.drop()
    save_ctx(ctx)


@cli.command(name="list")
def list_() -> None:
    """List what is included in the context."""
    click.echo(get_ctx().list())


@cli.command()
def tree() -> None:
    """List what is included in the context as a tree."""
    click.echo(get_ctx().tree())


@cli.command()
def generate() -> None:
    """Generate the context output."""
    ctx = get_ctx()
    save_ctx(ctx)
    click.echo(ctx.generate())


if __name__ == "__main__":
    cli()
