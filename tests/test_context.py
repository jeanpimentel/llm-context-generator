import json
import logging
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from llm_context_generator import Context

# Disable logging for the tests
logging.disable(logging.CRITICAL)

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


class TestContext(unittest.TestCase):
    def test_add_file(self):
        c = FIXTURES_DIR / "hello.c"

        context = Context(root_path=TESTS_DIR)
        context.add(c)

        self.assertIn(c, context._included)

    def test_add_files_simultaneously(self):
        c = FIXTURES_DIR / "hello.c"
        bash = FIXTURES_DIR / "b" / "hello.bash"

        context = Context(root_path=TESTS_DIR)
        context.add(c, bash)

        self.assertIn(c, context._included)
        self.assertIn(bash, context._included)

    def test_add_files_sequentially(self):
        c = FIXTURES_DIR / "hello.c"
        bash = FIXTURES_DIR / "b" / "hello.bash"

        context = Context(root_path=TESTS_DIR)
        context.add(c)
        context.add(bash)

        self.assertIn(c, context._included)
        self.assertIn(bash, context._included)

    def test_add_directory(self):
        j_dir = FIXTURES_DIR / "j"

        context = Context(root_path=TESTS_DIR)
        context.add(j_dir)

        self.assertIn(j_dir / "hello.java", context._included)
        self.assertIn(j_dir / "hello.js", context._included)
        self.assertIn(j_dir / "hello.json", context._included)

    def test_add_directory_recursively(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR)

        self.assertIn(FIXTURES_DIR / "j" / "hello.java", context._included)
        self.assertIn(FIXTURES_DIR / "p" / "hello.php", context._included)
        self.assertIn(FIXTURES_DIR / "sql" / "mysql" / "hello.sql", context._included)
        self.assertIn(
            FIXTURES_DIR / "sql" / "postgresql" / "hello.sql", context._included
        )

    def test_add_files_and_directory(self):
        php = FIXTURES_DIR / "p" / "hello.php"
        b_dir = FIXTURES_DIR / "b"
        sql_dir = FIXTURES_DIR / "sql"

        context = Context(root_path=TESTS_DIR)
        context.add(php, b_dir, sql_dir)

        self.assertIn(php, context._included)
        self.assertIn(b_dir / "hello.bash", context._included)
        self.assertIn(b_dir / "hello.bat", context._included)
        self.assertIn(sql_dir / "mysql" / "hello.sql", context._included)
        self.assertIn(sql_dir / "postgresql" / "hello.sql", context._included)

    def test_add_files_not_under_root_path(self):
        context = Context(root_path=TESTS_DIR)
        context.add(TESTS_DIR.parent)
        self.assertEqual(0, len(context._included))

        with TemporaryDirectory() as temp_dir:
            context.add(Path(temp_dir))
        self.assertEqual(0, len(context._included))

    def test_add_duplicated_files(self):
        php = FIXTURES_DIR / "p" / "hello.php"

        context = Context(root_path=TESTS_DIR)
        context.add(php, php, php)
        context.add(php)

        self.assertIn(php, context._included)
        self.assertEqual(1, len(context._included))

    def test_add_hidden_files_and_directories(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR)

        self.assertIn(FIXTURES_DIR / ".hidden_dir" / ".hidden_file", context._included)

    def test_add_handles_symlink(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR / "symlink-to-hello.html")

        self.assertIn(FIXTURES_DIR / "hello.html", context._included)
        self.assertNotIn(FIXTURES_DIR / "symlink-to-hello.html", context._included)
        self.assertEqual(1, len(context._included))

    def test_empty_ignore_string(self):
        j_dir = FIXTURES_DIR / "j"

        context = Context(root_path=TESTS_DIR, ignore="")
        context.add(j_dir)

        self.assertIn(j_dir / "hello.java", context._included)
        self.assertIn(j_dir / "hello.js", context._included)
        self.assertIn(j_dir / "hello.json", context._included)

    def test_simple_ignore_string(self):
        j_dir = FIXTURES_DIR / "j"

        context = Context(root_path=TESTS_DIR, ignore="*.java")
        context.add(j_dir)

        self.assertNotIn(j_dir / "hello.java", context._included)
        self.assertIn(j_dir / "hello.js", context._included)
        self.assertIn(j_dir / "hello.json", context._included)

    def test_complex_ignore_string(self):
        context = Context(
            root_path=TESTS_DIR,
            ignore="""
*.java
*.bash
p
sql/mysql
""",
        )
        context.add(FIXTURES_DIR)

        self.assertNotIn(FIXTURES_DIR / "b" / "hello.bash", context._included)
        self.assertNotIn(FIXTURES_DIR / "j" / "hello.java", context._included)
        self.assertNotIn(FIXTURES_DIR / "p" / "hello.php", context._included)
        self.assertNotIn(
            FIXTURES_DIR / "sql" / "mysql " / "hello.sql", context._included
        )
        self.assertIn(
            FIXTURES_DIR / "sql" / "postgresql" / "hello.sql", context._included
        )

    def test_empty_ignore_file(self):
        j_dir = FIXTURES_DIR / "j"

        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(b"")
            temp_file.seek(0)

            context = Context(
                root_path=TESTS_DIR,
                ignore=Path(temp_file.name),
            )
            context.add(j_dir)

            self.assertIn(j_dir / "hello.java", context._included)
            self.assertIn(j_dir / "hello.js", context._included)
            self.assertIn(j_dir / "hello.json", context._included)

    def test_simple_ignore_file(self):
        j_dir = FIXTURES_DIR / "j"

        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(b"*.java")
            temp_file.seek(0)

            context = Context(
                root_path=TESTS_DIR,
                ignore=Path(temp_file.name),
            )
            context.add(j_dir)

            self.assertNotIn(j_dir / "hello.java", context._included)
            self.assertIn(j_dir / "hello.js", context._included)
            self.assertIn(j_dir / "hello.json", context._included)

    def test_complex_ignore_file(self):
        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(
                b"""
*.java
*.bash
p
sql/mysql
"""
            )
            temp_file.seek(0)

            context = Context(
                root_path=TESTS_DIR,
                ignore=Path(temp_file.name),
            )
            context.add(FIXTURES_DIR)

            self.assertNotIn(FIXTURES_DIR / "b" / "hello.bash", context._included)
            self.assertNotIn(FIXTURES_DIR / "j" / "hello.java", context._included)
            self.assertNotIn(FIXTURES_DIR / "p" / "hello.php", context._included)
            self.assertNotIn(
                FIXTURES_DIR / "sql" / "mysql " / "hello.sql", context._included
            )
            self.assertIn(
                FIXTURES_DIR / "sql" / "postgresql" / "hello.sql", context._included
            )

    def test_simple_ignore_list(self):
        j_dir = FIXTURES_DIR / "j"

        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(b"*.java")
            temp_file.seek(0)

            context = Context(
                root_path=TESTS_DIR,
                ignore=[
                    Path(temp_file.name),
                    "*.json",
                ],
            )
            context.add(j_dir / "hello.java")
            context.add(j_dir / "hello.js")
            context.add(j_dir / "hello.json")

            self.assertNotIn(j_dir / "hello.java", context._included)
            self.assertIn(j_dir / "hello.js", context._included)
            self.assertNotIn(j_dir / "hello.json", context._included)

    def test_nonexistent_ignore_file(self):
        j_dir = FIXTURES_DIR / "j"

        context = Context(
            root_path=TESTS_DIR,
            ignore=Path("invalid"),
        )
        context.add(j_dir)

        self.assertIn(j_dir / "hello.java", context._included)
        self.assertIn(j_dir / "hello.js", context._included)
        self.assertIn(j_dir / "hello.json", context._included)

    def test_remove_file(self):
        c = FIXTURES_DIR / "hello.c"
        bash = FIXTURES_DIR / "b" / "hello.bash"

        context = Context(root_path=TESTS_DIR)
        context.add(c, bash)

        self.assertIn(c, context._included)
        self.assertIn(bash, context._included)

        context.remove(c)
        self.assertNotIn(c, context._included)

    def test_remove_directory(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR)

        self.assertIn(FIXTURES_DIR / "j" / "hello.java", context._included)
        self.assertIn(FIXTURES_DIR / "j" / "hello.js", context._included)
        self.assertIn(FIXTURES_DIR / "j" / "hello.json", context._included)

        context.remove(FIXTURES_DIR / "j")

        self.assertNotIn(FIXTURES_DIR / "j" / "hello.java", context._included)
        self.assertNotIn(FIXTURES_DIR / "j" / "hello.js", context._included)
        self.assertNotIn(FIXTURES_DIR / "j" / "hello.json", context._included)

    def test_drop(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR)

        self.assertNotEqual(0, len(context._included))

        context.drop()

        self.assertEqual(0, len(context._included))

    def test_tree(self):
        context = Context(root_path=FIXTURES_DIR)
        context.add(FIXTURES_DIR)

        expected = """.
├── .hidden_dir
│   └── .hidden_file
├── about.txt
├── b
│   ├── hello.bash
│   └── hello.bat
├── hello.c
├── hello.cpp
├── hello.go
├── hello.html
├── hello.kt
├── j
│   ├── hello.java
│   ├── hello.js
│   └── hello.json
├── p
│   ├── hello.php
│   └── hello.pl
└── sql
    ├── mysql
    │   └── hello.sql
    └── postgresql
        └── hello.sql
"""

        self.assertEqual(expected, context.tree())

        context.remove(FIXTURES_DIR / "j")
        context.remove(FIXTURES_DIR / "p")
        context.remove(FIXTURES_DIR / "sql" / "mysql")

        expected2 = """.
├── .hidden_dir
│   └── .hidden_file
├── about.txt
├── b
│   ├── hello.bash
│   └── hello.bat
├── hello.c
├── hello.cpp
├── hello.go
├── hello.html
├── hello.kt
└── sql
    └── postgresql
        └── hello.sql
"""

        self.assertEqual(expected2, context.tree())

    def test_tree_without_files(self):
        context = Context(root_path=FIXTURES_DIR)
        self.assertEqual("", context.tree())

    def test_list(self):
        php = FIXTURES_DIR / "p" / "hello.php"
        java = FIXTURES_DIR / "j" / "hello.java"

        context = Context(root_path=TESTS_DIR)
        context.add(php, java)

        self.assertEqual("fixtures/j/hello.java\nfixtures/p/hello.php", context.list())

        self.assertEqual(
            f"{java.absolute()}\n{php.absolute()}", context.list(relative=False)
        )

    def test_generate(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR / "j")
        context.add(FIXTURES_DIR / "p")

        expected = """## Context - Relevant files

````
.
└── fixtures
    ├── j
    │   ├── hello.java
    │   ├── hello.js
    │   └── hello.json
    └── p
        ├── hello.php
        └── hello.pl
````

### `fixtures/j/hello.java`
````java
public class Java {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
````

### `fixtures/j/hello.js`
````js
console.log("Hello World");
````

### `fixtures/j/hello.json`
````json
{ "hello": "world" }
````

### `fixtures/p/hello.php`
````php
<?php

echo 'Hello World';
````

### `fixtures/p/hello.pl`
````pl
#!/usr/bin/perl
print "Hello World";
````
"""
        self.assertEqual(expected, context.generate())

    def test_generate_without_files(self):
        context = Context(root_path=TESTS_DIR)
        self.assertEqual("", context.generate())

    def test_equals(self):
        c1 = Context(root_path=TESTS_DIR, ignore=["*.json"])
        c1.add(FIXTURES_DIR)

        c2 = Context(root_path=FIXTURES_DIR.parent, ignore="*.json")
        c2.add(FIXTURES_DIR)

        self.assertEqual(c1, c2)


class ToJsonFromJson(unittest.TestCase):
    def test_empty(self):
        context = Context(root_path=TESTS_DIR)

        expected = {
            "root": str(TESTS_DIR),
            "ignore": [],
            "files": [],
        }

        ctx_as_json = context.to_json()
        self.assertEqual(expected, json.loads(ctx_as_json))

        context_2 = Context.from_json(ctx_as_json)
        self.assertEqual(context, context_2)

    def test_with_files(self):
        context = Context(root_path=TESTS_DIR)
        context.add(FIXTURES_DIR / "p")
        context.add(FIXTURES_DIR / "j")

        expected = {
            "root": str(TESTS_DIR),
            "ignore": [],
            "files": [
                str(FIXTURES_DIR / "j" / "hello.java"),
                str(FIXTURES_DIR / "j" / "hello.js"),
                str(FIXTURES_DIR / "j" / "hello.json"),
                str(FIXTURES_DIR / "p" / "hello.php"),
                str(FIXTURES_DIR / "p" / "hello.pl"),
            ],
        }

        ctx_as_json = context.to_json()
        self.assertEqual(expected, json.loads(ctx_as_json))

        context_2 = Context.from_json(ctx_as_json)
        self.assertEqual(context, context_2)

    def test_with_ignore(self):
        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(b"*.java")
            temp_file.seek(0)

            context = Context(root_path=TESTS_DIR, ignore=Path(temp_file.name))
            context.add(FIXTURES_DIR / "p")
            context.add(FIXTURES_DIR / "j")

            expected = {
                "root": str(TESTS_DIR),
                "ignore": [
                    f"path::{temp_file.name}",
                ],
                "files": [
                    str(FIXTURES_DIR / "j" / "hello.js"),
                    str(FIXTURES_DIR / "j" / "hello.json"),
                    str(FIXTURES_DIR / "p" / "hello.php"),
                    str(FIXTURES_DIR / "p" / "hello.pl"),
                ],
            }

            ctx_as_json = context.to_json()
            self.assertEqual(expected, json.loads(ctx_as_json))

            context_2 = Context.from_json(ctx_as_json)
            self.assertEqual(context, context_2)

    def test_with_ignore_list(self):
        with NamedTemporaryFile(delete=True, suffix=".gitignore") as temp_file:
            temp_file.write(b"*.java")
            temp_file.seek(0)

            context = Context(
                root_path=TESTS_DIR,
                ignore=[
                    Path(temp_file.name),
                    "*.json",
                ],
            )
            context.add(FIXTURES_DIR / "p")
            context.add(FIXTURES_DIR / "j")

            expected = {
                "root": str(TESTS_DIR),
                "ignore": [
                    f"path::{temp_file.name}",
                    "str::*.json",
                ],
                "files": [
                    str(FIXTURES_DIR / "j" / "hello.js"),
                    str(FIXTURES_DIR / "p" / "hello.php"),
                    str(FIXTURES_DIR / "p" / "hello.pl"),
                ],
            }

            ctx_as_json = context.to_json()
            self.assertEqual(expected, json.loads(ctx_as_json))

            context_2 = Context.from_json(ctx_as_json)
            self.assertEqual(context, context_2)
