"""Regenerate Figs. 3–7 without error."""

from __future__ import annotations

from pathlib import Path

from figures.make_figures import main as make_main
import figures.make_figures as fm


def test_make_figures(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["make_figures.py", "--source", str(Path("results/paper/figures.json")), "--out", str(tmp_path)],
    )
    make_main()
    for name in ["fig3.png", "fig4.png", "fig5.png", "fig6.png", "fig7.png"]:
        assert (tmp_path / name).exists()
        assert (tmp_path / name).stat().st_size > 1000
