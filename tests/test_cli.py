import json
import os
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Tuple

from click.testing import CliRunner

from llm_context_generator import Context, __version__
from llm_context_generator.cli import (
    add,
    cli,
    destroy,
    generate,
    init,
    list_,
    remove,
    reset,
    tree,
)

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


@contextmanager
def initiated_context() -> Tuple[Context, Path]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        init_result = runner.invoke(init)
        assert init_result.exit_code == 0
        yield runner, Path.cwd()


class TestCli(unittest.TestCase):

    def test_no_args(self):
        runner = CliRunner()
        result = runner.invoke(cli)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            """Usage: cli [OPTIONS] COMMAND [ARGS]...

  LLM Context Generator.

Options:
  -v, --version  Show the version and exit.
  -h, --help     Show this message and exit.

Commands:
  init      Initialize a context.
  destroy   Remove the context.
  add       Add files to the context. Run add --help to see more.
  remove    Remove files from the context. Run remove --help to see more.
  reset     Reset the context removing all files.
  list      List what is included in the context.
  tree      List what is included in the context as a tree.
  generate  Generate the context output.
""",
            result.output,
        )

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            """Usage: cli [OPTIONS] COMMAND [ARGS]...

  LLM Context Generator.

Options:
  -v, --version  Show the version and exit.
  -h, --help     Show this message and exit.

Commands:
  init      Initialize a context.
  destroy   Remove the context.
  add       Add files to the context. Run add --help to see more.
  remove    Remove files from the context. Run remove --help to see more.
  reset     Reset the context removing all files.
  list      List what is included in the context.
  tree      List what is included in the context as a tree.
  generate  Generate the context output.
""",
            result.output,
        )

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["-v"])
        self.assertEqual(0, result.exit_code)
        self.assertEqual(f"{__version__}\n", result.output)

    def test_init(self):
        with initiated_context() as (runner, root):
            expected_ctx_json = {
                "root": str(Path.cwd()),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(Path.cwd() / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

    def test_init_already_done(self):
        with initiated_context() as (runner, root):

            # init again
            result = runner.invoke(init)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                "Directory already exists: .ctx. If needed, run destroy command first.\n",
                result.output,
            )

            (root / "subdir1" / "subdir2").mkdir(parents=True)
            os.chdir(root / "subdir1" / "subdir2")

    def test_destroy(self):
        with initiated_context() as (runner, root):
            expected_ctx_json = {
                "root": str(Path.cwd()),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(Path.cwd() / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

            result = runner.invoke(destroy)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual("", result.output)

            self.assertFalse((root / ".ctx").exists())

    def test_commands_without_initiated_context(self):
        runner = CliRunner()

        commands = [
            (destroy, None),
            (add, ["."]),
            (remove, ["."]),
            (reset, None),
            (list_, None),
            (tree, None),
            (generate, None),
        ]

        for command, args in commands:
            result = runner.invoke(command, args)
            self.assertEqual(-1, result.exit_code)
            self.assertEqual(
                "Context not found. Please initialize with the init command.\n",
                result.output,
            )

    def test_context_metadata_not_found(self):
        with initiated_context() as (runner, root):
            # something happened and the file is not there
            (root / ".ctx" / "ctx.json").unlink()

            result = runner.invoke(list_)

            self.assertEqual(result.exit_code, -1)
            self.assertEqual(
                "Context not found. Please initialize with the init command.\n",
                result.output,
            )

    def test_add_with_no_args(self):
        with initiated_context() as (runner, root):
            result = runner.invoke(add)
            self.assertEqual(result.exit_code, 0)  # no_args_is_help
            self.assertTrue("Usage: add [OPTIONS] [FILES...]" in result.output)

    def test_remove_with_no_args(self):
        with initiated_context() as (runner, root):
            result = runner.invoke(remove)
            self.assertEqual(result.exit_code, 0)  # no_args_is_help
            self.assertTrue("Usage: remove [OPTIONS] [FILES...]" in result.output)

    def test_add(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            result = runner.invoke(
                add,
                [
                    "j",
                    "b",
                    "sql/mysql/hello.sql",
                ],
            )

            self.assertEqual(result.exit_code, 0)
            self.assertEqual("", result.output)

            os.chdir("p")
            runner.invoke(
                add,
                [
                    "hello.php",
                ],
            )

            expected_ctx_json = {
                "root": str(root),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(root / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [
                    str(root / "b" / "hello.bash"),
                    str(root / "b" / "hello.bat"),
                    str(root / "j" / "hello.java"),
                    str(root / "j" / "hello.js"),
                    str(root / "j" / "hello.json"),
                    str(root / "p" / "hello.php"),
                    str(root / "sql" / "mysql" / "hello.sql"),
                ],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

    def test_remove(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            # add
            runner.invoke(
                add,
                [
                    "j",
                    "b",
                    "sql/mysql",
                ],
            )

            expected_ctx_json = {
                "root": str(root),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(root / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [
                    str(root / "b" / "hello.bash"),
                    str(root / "b" / "hello.bat"),
                    str(root / "j" / "hello.java"),
                    str(root / "j" / "hello.js"),
                    str(root / "j" / "hello.json"),
                    str(root / "sql" / "mysql" / "hello.sql"),
                ],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

            # remove
            result = runner.invoke(
                remove,
                [
                    "j",
                    "b/hello.bash",
                    ".hidden_dir/.hidden_file",  # not included
                    "p",  # not included
                ],
            )

            os.chdir("sql/mysql")
            runner.invoke(
                remove,
                [
                    "hello.sql",
                ],
            )

            self.assertEqual(result.exit_code, 0)
            self.assertEqual("", result.output)

            expected_ctx_json = {
                "root": str(root),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(root / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [
                    str(root / "b" / "hello.bat"),
                ],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

    def test_reset(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            # add
            runner.invoke(
                add,
                [
                    "p",
                    "sql",
                ],
            )

            expected_ctx_json = {
                "root": str(root),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(root / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [
                    str(root / "p" / "hello.php"),
                    str(root / "p" / "hello.pl"),
                    str(root / "sql" / "mysql" / "hello.sql"),
                    str(root / "sql" / "postgresql" / "hello.sql"),
                ],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

            # reset
            result = runner.invoke(reset)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual("", result.output)

            expected_ctx_json = {
                "root": str(root),
                "ignore": [
                    f"path::{(Path.home() / '.gitignore')}",
                    f"path::{(root / '.gitignore')}",
                    "str::.git",
                    "str::.ctx",
                ],
                "files": [],
            }

            self.assertEqual(
                expected_ctx_json,
                json.loads(
                    (root / ".ctx" / "ctx.json").read_text(),
                ),
            )

    def test_list(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            # add / remove
            runner.invoke(add, ["."])
            runner.invoke(remove, ["b", "j", "p"])

            os.chdir("b")

            # list
            result = runner.invoke(list_)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                """.hidden_dir/.hidden_file
about.txt
hello.c
hello.cpp
hello.go
hello.html
hello.kt
sql/mysql/hello.sql
sql/postgresql/hello.sql
symlink-to-hello.html
""",
                result.output,
            )

    def test_tree(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            # add / remove
            runner.invoke(add, ["."])
            runner.invoke(remove, ["b", "j", "p"])

            # tree
            result = runner.invoke(tree)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                """.
├── .hidden_dir
│   └── .hidden_file
├── about.txt
├── hello.c
├── hello.cpp
├── hello.go
├── hello.html
├── hello.kt
├── sql
│   ├── mysql
│   │   └── hello.sql
│   └── postgresql
│       └── hello.sql
└── symlink-to-hello.html

""",
                result.output,
            )

    def test_generate(self):
        with initiated_context() as (runner, root):
            shutil.copytree(FIXTURES_DIR, root, dirs_exist_ok=True)

            # add / remove
            runner.invoke(add, ["about.txt", "p"])

            # generate
            result = runner.invoke(generate)

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                """## Context - Relevant files

````
.
├── about.txt
└── p
    ├── hello.php
    └── hello.pl
````

### `about.txt`
````txt
Examples extracted from https://github.com/leachim6/hello-world
````

### `p/hello.php`
````php
<?php

echo 'Hello World';
````

### `p/hello.pl`
````pl
#!/usr/bin/perl
print "Hello World";
````

""",
                result.output,
            )
