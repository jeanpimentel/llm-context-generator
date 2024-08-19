import pathlib
from pathlib import Path
from typing import List, Tuple

import click

from llm_context_generator import __version__


class OrderCommands(click.Group):
    def list_commands(self, ctx: click.Context) -> List[str]:
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
    click.echo("init!")


@cli.command()
def destroy() -> None:
    """Remove the context."""
    click.echo("destroy!")


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
    src: Tuple[Path, ...],
    verbose: bool = False,
) -> None:
    """Add files to the context.

    \b
    <FILES>...
        Files that should be added to the context for the LLM. Fileglobs (e.g. *.c) can be given to add all matching files. Also a leading directory name (e.g. dir to add dir/file1 and dir/file2).
    """
    click.echo("Add:")
    click.echo(src)


@cli.command(short_help="Remove files from the context. Run remove --help to see more.")
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
    src: Tuple[Path, ...],
    verbose: bool = False,
) -> None:
    """Remove files from the context.

    \b
    <FILES>...
        Files that should be removed from the context for the LLM. Fileglobs (e.g. *.c) can be given to remove all matching files. Also a leading directory name (e.g. dir to add dir/file1 and dir/file2).
    """
    click.echo("Remove:")
    click.echo(src)


@cli.command()
def reset() -> None:
    """Reset the context removing all files."""
    click.echo("reset.")


@cli.command(name="list")
def list_() -> None:
    """List what is included in the context."""
    click.echo("list!")


@cli.command()
def tree() -> None:
    """List what is included in the context as a tree."""
    click.echo("treeeeee")


@cli.command()
def generate() -> None:
    """Generate the context output."""
    click.echo("generate...")


if __name__ == "__main__":
    cli()
