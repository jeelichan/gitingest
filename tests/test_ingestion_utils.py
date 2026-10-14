"""Unit tests for ``_should_exclude`` and ``_should_include`` in ingestion_utils."""

from pathlib import Path

import pytest

from gitingest.utils.ingestion_utils import _should_exclude, _should_include

BASE = Path("/repo")


# ---------- _should_exclude : kondisi NORMAL ----------
@pytest.mark.parametrize(
    ("relative", "patterns", "expected"),
    [
        ("main.py", {"*.pyc"}, False),                  # tidak cocok -> tidak di-exclude
        ("cache/mod.pyc", {"*.pyc"}, True),             # cocok ekstensi
        ("node_modules/a/b.js", {"node_modules/"}, True),  # file di dalam folder ter-ignore
        ("src/app.py", {"*.pyc", "*.log"}, False),      # banyak pola, tak ada yang cocok
        ("logs/today.log", {"*.pyc", "*.log"}, True),   # banyak pola, satu cocok
    ],
)
def test_should_exclude_normal(relative, patterns, expected):
    assert _should_exclude(BASE / relative, BASE, patterns) is expected


# ---------- _should_exclude : kondisi BATAS (edge) ----------
def test_should_exclude_empty_patterns_excludes_nothing():
    assert _should_exclude(BASE / "anything.txt", BASE, set()) is False


def test_should_exclude_path_outside_base_is_always_excluded():
    # File di luar repo harus dianggap "excluded" demi keamanan.
    assert _should_exclude(Path("/etc/passwd"), BASE, set()) is True


def test_should_exclude_negation_depends_on_pattern_order():
    """Aturan gitignore: pola TERAKHIR yang cocok menang, jadi urutan penting.

    Kita pakai list (berurutan) agar hasilnya pasti. Ini membuktikan akar masalah
    bug di bawah.
    """
    path = BASE / "keep.log"
    assert _should_exclude(path, BASE, ["*.log", "!keep.log"]) is False  # dikecualikan dari ignore
    assert _should_exclude(path, BASE, ["!keep.log", "*.log"]) is True   # urutan terbalik -> ter-ignore


@pytest.mark.xfail(
    reason="BUG: ignore_patterns bertipe set (tanpa urutan), sehingga pola negasi '!' "
    "memberi hasil berbeda-beda tergantung PYTHONHASHSEED.",
    strict=False,
)
def test_should_exclude_negation_with_set_is_deterministic():
    path = BASE / "keep.log"
    assert _should_exclude(path, BASE, {"*.log", "!keep.log"}) is False


def test_should_exclude_path_equal_to_base():
    # Path == base -> relative path-nya "." ; tidak boleh crash.
    assert _should_exclude(BASE, BASE, {"*.pyc"}) is False


# ---------- _should_exclude : ERROR / perilaku tak terduga ----------
def test_should_exclude_directory_pattern_does_not_match_bare_dir_name():
    """Dokumentasi perilaku: pola 'build/' TIDAK cocok dengan path 'build' itu sendiri.

    Penyebab: fungsi tidak menambahkan '/' di akhir path folder sebelum dicocokkan.
    Dampak kecil (isi folder tetap ter-exclude), tapi folder kosong tidak.
    """
    assert _should_exclude(BASE / "build", BASE, {"build/"}) is False
    assert _should_exclude(BASE / "build" / "out.o", BASE, {"build/"}) is True


# ---------- _should_include ----------
def test_should_include_matching_file(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x")
    assert _should_include(f, tmp_path, {"*.py"}) is True


def test_should_include_non_matching_file(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    assert _should_include(f, tmp_path, {"*.py"}) is False


def test_should_include_directory_always_true_so_children_are_visited(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    assert _should_include(d, tmp_path, {"*.py"}) is True


def test_should_include_outside_base_is_false(tmp_path):
    other = tmp_path.parent / "elsewhere.py"
    assert _should_include(other, tmp_path, {"*.py"}) is False


def test_should_include_empty_patterns_matches_nothing(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x")
    assert _should_include(f, tmp_path, set()) is False
