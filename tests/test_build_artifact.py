"""tools/build_artifact.py 的把關測試。

Artifact 版本靠 index.html 裡的 ARTIFACT:HEAD / ARTIFACT:BODY 註解標記切片。
標記被誤刪或改名時，若沒有這層把關，只會在發佈當下才發現頁面壞掉。
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "static" / "index.html"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_artifact", ROOT / "tools" / "build_artifact.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_page_is_a_complete_document():
    """repo 內的 index.html 由 FastAPI 直接提供，必須是完整的 HTML 文件。"""
    html = SOURCE.read_text(encoding="utf-8")
    assert html.lstrip().startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in html
    assert "viewport-fit=cover" in html


def test_artifact_build_strips_the_document_skeleton():
    """Artifact 發佈時會自行包上外層骨架，切出來的片段不能自帶。"""
    built = load_builder().build(SOURCE.read_text(encoding="utf-8"))
    for tag in ("<!doctype", "<html", "<head>", "</head>", "<body>", "</body>", "</html>"):
        assert tag not in built.lower(), tag


def test_artifact_build_keeps_the_parts_the_page_needs():
    built = load_builder().build(SOURCE.read_text(encoding="utf-8"))
    assert "<title>血鈉鑑別決策台</title>" in built
    assert '<script src="sodium-engine.js"></script>' in built
    assert "<style>" in built
    assert 'id="results"' in built
    # 標記之間不該漏掉頁尾說明
    assert "臨床決策輔助與教學用途" in built


@pytest.mark.parametrize("marker", ["HEAD", "BODY"])
def test_missing_marker_fails_loudly(marker):
    builder = load_builder()
    broken = SOURCE.read_text(encoding="utf-8").replace(f"<!-- ARTIFACT:{marker} -->", "")
    with pytest.raises(SystemExit):
        builder.build(broken)
