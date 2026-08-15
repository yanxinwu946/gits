from __future__ import annotations

import pytest
from gits.fetcher import parse_github_url, FetchError


class TestParseGithubUrl:
    def test_full_repo(self):
        p = parse_github_url("https://github.com/user/repo")
        assert p.owner == "user"
        assert p.repo == "repo"
        assert p.type == "repo"
        assert p.branch is None
        assert p.path is None
        assert p.raw_url is None

    def test_full_repo_with_git(self):
        p = parse_github_url("https://github.com/user/repo.git")
        assert p.owner == "user"
        assert p.repo == "repo"
        assert p.type == "repo"

    def test_tree_url_with_path(self):
        p = parse_github_url("https://github.com/user/repo/tree/main/src/lib")
        assert p.owner == "user"
        assert p.repo == "repo"
        assert p.type == "tree"
        assert p.branch == "main"
        assert p.path == "src/lib"

    def test_tree_url_no_path(self):
        p = parse_github_url("https://github.com/user/repo/tree/main")
        assert p.type == "tree"
        assert p.branch == "main"
        assert p.path is None

    def test_tree_url_encoded(self):
        p = parse_github_url("https://github.com/user/repo/tree/main/my%20dir")
        assert p.path == "my dir"

    def test_blob_url(self):
        p = parse_github_url("https://github.com/user/repo/blob/main/README.md")
        assert p.type == "blob"
        assert p.branch == "main"
        assert p.path == "README.md"
        assert p.raw_url == "https://raw.githubusercontent.com/user/repo/main/README.md"

    def test_blob_url_nested(self):
        p = parse_github_url("https://github.com/user/repo/blob/main/src/lib/foo.py")
        assert p.path == "src/lib/foo.py"
        assert p.raw_url == "https://raw.githubusercontent.com/user/repo/main/src/lib/foo.py"

    def test_www_prefix(self):
        p = parse_github_url("https://www.github.com/user/repo")
        assert p.owner == "user"
        assert p.repo == "repo"

    def test_no_protocol(self):
        p = parse_github_url("github.com/user/repo")
        assert p.owner == "user"

    def test_query_string_stripped(self):
        p = parse_github_url("https://github.com/user/repo?tab=readme-ov-file")
        assert p.type == "repo"

    def test_fragment_stripped(self):
        p = parse_github_url("https://github.com/user/repo#readme")
        assert p.type == "repo"

    def test_invalid_url(self):
        with pytest.raises(FetchError):
            parse_github_url("https://gitlab.com/user/repo")

    def test_invalid_url_garbage(self):
        with pytest.raises(FetchError):
            parse_github_url("not-a-url")

    def test_raw_url(self):
        p = parse_github_url("https://raw.githubusercontent.com/user/repo/main/README.md")
        assert p.type == "raw"
        assert p.owner == "user"
        assert p.repo == "repo"
        assert p.branch == "main"
        assert p.path == "README.md"
        assert p.raw_url == "https://raw.githubusercontent.com/user/repo/main/README.md"

    def test_raw_url_nested(self):
        p = parse_github_url("https://raw.githubusercontent.com/user/repo/main/src/lib/foo.py")
        assert p.path == "src/lib/foo.py"
        assert p.type == "raw"

    def test_archive_url(self):
        p = parse_github_url("https://github.com/user/repo/archive/main.zip")
        assert p.type == "archive"
        assert p.owner == "user"
        assert p.repo == "repo"
        assert p.branch == "main"
        assert p.path is None

    def test_archive_url_tag(self):
        p = parse_github_url("https://github.com/user/repo/archive/v1.0.0.zip")
        assert p.type == "archive"
        assert p.branch == "v1.0.0"

    def test_blob_url_no_path(self):
        p = parse_github_url("https://github.com/user/repo/blob/main")
        assert p.type == "blob"
        assert p.branch == "main"
        assert p.path is None
        assert p.raw_url is None