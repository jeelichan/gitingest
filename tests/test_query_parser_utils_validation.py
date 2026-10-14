"""Unit tests for host/scheme/path validators in query_parser_utils."""

import pytest

from gitingest.utils.query_parser_utils import (
    _get_user_and_repo_from_path,
    _looks_like_git_host,
    _validate_host,
    _validate_url_scheme,
)


# ---------- _validate_host ----------
@pytest.mark.parametrize("host", ["github.com", "gitlab.com", "bitbucket.org"])
def test_validate_host_accepts_known_hosts(host):
    _validate_host(host)  # tidak boleh raise


@pytest.mark.parametrize("host", ["GitHub.com", "GITLAB.COM"])
def test_validate_host_is_case_insensitive(host):
    _validate_host(host)


@pytest.mark.parametrize("host", ["git.example.com", "gitlab.mycompany.io", "github.corp.net"])
def test_validate_host_accepts_self_hosted_by_prefix(host):
    _validate_host(host)


@pytest.mark.parametrize("host", ["example.com", "evil.org", "", "localhost"])
def test_validate_host_rejects_unknown(host):
    with pytest.raises(ValueError, match="Unknown domain"):
        _validate_host(host)


def test_validate_host_port_is_part_of_host_string():
    """Port ikut terbaca sebagai bagian host.

    - 'example.com:8080' ditolak (tidak dikenal).
    - 'github.com:8080' justru DITERIMA, karena lolos heuristik awalan 'github.'
      (bukan karena dikenali sebagai github.com). Perilaku tak terduga yang kami temukan.
    """
    with pytest.raises(ValueError):
        _validate_host("example.com:8080")
    _validate_host("github.com:8080")  # tidak raise


def test_validate_host_accepts_lookalike_prefix_domain():
    """Perilaku tak terduga: heuristik hanya melihat AWAL nama host.

    'github.attacker.example' lolos walau bukan GitHub. Ini by-design untuk
    mendukung self-hosted, tetapi layak dicatat sebagai risiko.
    """
    _validate_host("github.attacker.example")  # tidak raise


# ---------- _looks_like_git_host ----------
@pytest.mark.parametrize(
    ("host", "expected"),
    [("git.foo.com", True), ("gitlab.foo.com", True), ("github.foo.com", True),
     ("GIT.FOO.COM", True), ("mygit.foo.com", False), ("foo.com", False), ("", False)],
)
def test_looks_like_git_host(host, expected):
    assert _looks_like_git_host(host) is expected


# ---------- _validate_url_scheme ----------
@pytest.mark.parametrize("scheme", ["http", "https", "HTTPS", "Http"])
def test_validate_url_scheme_accepts_http_family(scheme):
    _validate_url_scheme(scheme)


@pytest.mark.parametrize("scheme", ["ftp", "ssh", "file", "javascript", ""])
def test_validate_url_scheme_rejects_others(scheme):
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        _validate_url_scheme(scheme)


# ---------- _get_user_and_repo_from_path ----------
def test_get_user_and_repo_normal():
    assert _get_user_and_repo_from_path("/octocat/Hello-World") == ("octocat", "hello-world")


def test_get_user_and_repo_ignores_extra_segments_and_slashes():
    assert _get_user_and_repo_from_path("/a/b/tree/main/") == ("a", "b")


def test_get_user_and_repo_lowercases():
    assert _get_user_and_repo_from_path("/OctoCat/MyRepo") == ("octocat", "myrepo")


@pytest.mark.parametrize("path", ["", "/", "/onlyuser", "onlyuser/"])
def test_get_user_and_repo_too_short_raises(path):
    with pytest.raises(ValueError, match="Invalid repository URL"):
        _get_user_and_repo_from_path(path)
