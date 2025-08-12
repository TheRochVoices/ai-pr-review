"""PR Review Bot using local Ollama model.

This module provides `PRReviewBot` which inspects the git diff between two
branches and uses a locally running Ollama model to offer code review
suggestions. The model can leverage GPU acceleration as provided by Ollama.
"""
from __future__ import annotations

from dataclasses import dataclass
import subprocess
import textwrap
from typing import List
import requests


@dataclass
class FileReview:
    """Container for a review of a single file."""

    path: str
    comments: str


class PRReviewBot:
    """Generate a review for changes between two branches.

    Parameters
    ----------
    repo_path:
        Path to the git repository. Defaults to the current directory.
    model:
        Name of the Ollama model to use.
    endpoint:
        URL of the Ollama generate endpoint.
    """

    def __init__(self, repo_path: str = ".", model: str = "llama3", endpoint: str = "http://localhost:11434/api/generate") -> None:
        self.repo_path = repo_path
        self.model = model
        self.endpoint = endpoint

    # ------------------------------------------------------------------
    # Git helpers
    def _run_git(self, *args: str) -> str:
        """Run a git command inside ``repo_path`` and return stdout."""
        result = subprocess.run(["git", *args], cwd=self.repo_path, check=True, text=True, capture_output=True)
        return result.stdout

    def _changed_files(self, source: str, target: str) -> List[str]:
        out = self._run_git("diff", "--name-only", f"{target}..{source}")
        return [line.strip() for line in out.splitlines() if line.strip()]

    def _file_diff(self, source: str, target: str, path: str) -> str:
        return self._run_git("diff", f"{target}..{source}", "--", path)

    def _file_content(self, branch: str, path: str) -> str:
        return self._run_git("show", f"{branch}:{path}")

    # ------------------------------------------------------------------
    # Ollama interaction
    def _call_model(self, prompt: str) -> str:
        """Send ``prompt`` to Ollama and return the generated text."""
        response = requests.post(
            self.endpoint,
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def _analyze(self, file_path: str, diff: str, full_content: str, source: str, target: str) -> str:
        prompt = textwrap.dedent(
            f"""
            You are an expert software engineer assisting with pull request reviews.
            Compare two branches: {target} (base) and {source} (feature).
            A developer has changed the file `{file_path}`. You are given the full
            content of the file from the feature branch along with the diff patch
            between the base and feature branch. Consider the entire file but limit
            your comments strictly to lines that are part of the diff. Highlight
            potential bugs, wrong logic, bad coding practices, and opportunities for
            improvement. Be concise and reference line numbers from the patch when
            possible.

            <file_content>
            {full_content}
            </file_content>

            <diff_patch>
            {diff}
            </diff_patch>

            Provide your review now.
            """
        ).strip()

        return self._call_model(prompt)

    # ------------------------------------------------------------------
    def review(self, source: str, target: str) -> List[FileReview]:
        """Return reviews for all files changed from ``target`` to ``source``."""
        files = self._changed_files(source, target)
        reviews: List[FileReview] = []
        for path in files:
            diff = self._file_diff(source, target, path)
            content = self._file_content(source, path)
            comments = self._analyze(path, diff, content, source, target)
            reviews.append(FileReview(path=path, comments=comments))
        return reviews


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run an AI-assisted PR review.")
    parser.add_argument("source", help="Source branch with proposed changes")
    parser.add_argument("target", help="Target branch to compare against")
    parser.add_argument("--repo", default=".", help="Path to the git repository")
    parser.add_argument("--model", default="llama3", help="Ollama model name")
    parser.add_argument("--endpoint", default="http://localhost:11434/api/generate", help="Ollama endpoint URL")
    args = parser.parse_args()

    bot = PRReviewBot(repo_path=args.repo, model=args.model, endpoint=args.endpoint)
    result = bot.review(args.source, args.target)
    output = {r.path: r.comments for r in result}
    print(json.dumps(output, indent=2))
