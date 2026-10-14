"""Unit tests for ``resolve_token`` in gitingest.utils.auth."""

import pytest

from gitingest.utils.auth import resolve_token
from gitingest.utils.exceptions import InvalidGitHubTokenError

# Token palsu tapi formatnya valid (regex mewajibkan: prefix + 36 karakter alfanumerik).
VALID_CLASSIC = "ghp_" + "a" * 36
VALID_ENV = "ghp_" + "b" * 36
VALID_FINE_GRAINED = "github_pat_" + "A" * 22 + "_" + "B" * 59


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Pastikan GITHUB_TOKEN dari komputer kita tidak mengganggu tes."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


# ---------- NORMAL ----------
def test_explicit_valid_token_is_returned():
    assert resolve_token(VALID_CLASSIC) == VALID_CLASSIC


def test_fine_grained_token_is_accepted():
    assert resolve_token(VALID_FINE_GRAINED) == VALID_FINE_GRAINED


def test_falls_back_to_env_var(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", VALID_ENV)
    assert resolve_token(None) == VALID_ENV


def test_explicit_token_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", VALID_ENV)
    assert resolve_token(VALID_CLASSIC) == VALID_CLASSIC


# ---------- EDGE ----------
def test_no_token_anywhere_returns_none():
    assert resolve_token(None) is None


def test_empty_string_is_treated_as_missing(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", VALID_ENV)
    assert resolve_token("") == VALID_ENV  # "" falsy -> pakai env


def test_empty_string_and_no_env_returns_falsy_not_error():
    assert not resolve_token("")


@pytest.mark.parametrize("length", [35, 37])
def test_token_length_boundary(length):
    with pytest.raises(InvalidGitHubTokenError):
        resolve_token("ghp_" + "a" * length)  # harus tepat 36


# ---------- ERROR ----------
@pytest.mark.parametrize(
    "bad",
    ["not-a-token", "ghp_short", "xyz_" + "a" * 36, "ghp_" + "!" * 36, "   ", VALID_CLASSIC + "\n"],
)
def test_invalid_explicit_token_raises(bad):
    with pytest.raises(InvalidGitHubTokenError, match="Invalid GitHub token format"):
        resolve_token(bad)


def test_invalid_env_token_also_raises(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "garbage")
    with pytest.raises(InvalidGitHubTokenError):
        resolve_token(None)


def test_error_is_a_valueerror_subclass():
    with pytest.raises(ValueError):
        resolve_token("garbage")
