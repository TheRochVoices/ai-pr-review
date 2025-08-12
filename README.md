# AI PR Review Bot

This repository contains a simple Python utility that performs an AI-assisted
code review for changes between two branches in a git repository.  The tool
uses a locally running [Ollama](https://github.com/jmorganca/ollama) service to
generate feedback about the diff.

## Usage

```bash
python pr_review_bot.py <source_branch> <target_branch> [--repo /path/to/repo]
```

The script contacts an Ollama server running on `http://localhost:11434` by
default.  A different model or endpoint can be supplied via command line
arguments.

The output is a JSON document with each changed file mapped to the model's
review comments.

## Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```
