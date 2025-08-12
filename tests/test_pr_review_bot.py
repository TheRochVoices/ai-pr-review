import json
import subprocess
from pathlib import Path

from pr_review_bot import PRReviewBot


def init_repo(repo: Path):
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    (repo / "hello.py").write_text("print('hello')\n")
    subprocess.run(["git", "add", "hello.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True, capture_output=True)
    (repo / "hello.py").write_text("print('hello world')\n")
    subprocess.run(["git", "commit", "-am", "update"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "main"], cwd=repo, check=True, capture_output=True)


def test_review_collects_changes(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)

    bot = PRReviewBot(repo_path=str(repo))

    # Avoid calling the real model by stubbing _call_model
    monkeypatch.setattr(bot, "_call_model", lambda prompt: "stub response")

    reviews = bot.review("feature", "main")
    assert len(reviews) == 1
    assert reviews[0].path == "hello.py"
    assert "stub response" in reviews[0].comments
