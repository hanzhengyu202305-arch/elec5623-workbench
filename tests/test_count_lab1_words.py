from pathlib import Path

from scripts.count_lab1_words import count_words, main


def test_count_words_splits_on_whitespace() -> None:
    assert count_words("one two\nthree") == 3


def test_main_fails_when_lab1_limit_exceeded(tmp_path: Path) -> None:
    path = tmp_path / "run2.txt"
    path.write_text("word " * 121, encoding="utf-8")
    assert main([str(path)]) == 1


def test_main_passes_at_limit(tmp_path: Path, capsys) -> None:
    path = tmp_path / "run2.txt"
    path.write_text("word " * 120, encoding="utf-8")
    assert main([str(path)]) == 0
    assert capsys.readouterr().out.strip() == "120"
