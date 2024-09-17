# LLM Context Generator

## Overview

LLM Context Generator is a command-line tool designed to help manage context files for large language models (LLMs). 

It provides functionalities to add, remove, list, and generate context files, making it easier to maintain the context required for various LLM operations.

## Features

- **Add Files**: Add files to the context.
- **Remove Files**: Remove files from the context.
- **List Files**: List all files included in the context.
- **Tree View**: View the context files in a tree structure.
- **Generate Context**: Generate the final context output file.

## Installation

To install the LLM Context Generator, clone the repository and install the dependencies:

```sh
pip install llm-context-generator
```

## Usage

The tool provides several commands to manage your context files:

### Initialize Context

Initialize a new context in the current directory.

```sh
ctx init
```

### Destroy Context

Remove the context directory. It does not touch any of your files.

```sh
ctx destroy
```

### Add Files

Add specified files or directories to the context.

```sh
ctx add [FILES...]
```

### Remove Files

Remove specified files or directories from the context.

```sh
ctx remove [FILES...]
```

### Reset Context

Remove all files from the context without deleting the context directory.

```sh
ctx reset
```

### List Files

List all files currently included in the context.

```sh
ctx list
```

### Tree View

View the context files in a tree structure.

```sh
ctx tree
```

### Generate Context

Generate the final context output file.

```sh
ctx generate
```

## Example

Here is a typical workflow for using the LLM Context Generator:

1. **Initialize the Context**:
    ```sh
    ctx init
    ```

2. **Add Files to the Context**:
    ```sh
    ctx add src/main.py src/utils.py
    ```

3. **List Files in the Context**:
    ```sh
    ctx list
    ```

4. **Generate the Context Output**:
    ```sh
    ctx generate
    ```
   or 
    ```sh
    ctx generate | pbcopy 
