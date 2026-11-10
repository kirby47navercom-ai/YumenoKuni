"""Read-only glyph audit of generated native UI, with no acceptance shortcuts."""
from pathlib import Path
import json
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def audit():
    fonts, missing, checked = {}, [], 0
    for file in sorted((ROOT / "Game/Assets/UI").glob("*.hbwidget.json")):
        widget = json.loads(file.read_text(encoding="utf-8"))
        for node in widget["nodes"]:
            props = node.get("properties", {})
            text, relative = props.get("text", ""), props.get("font", "")
            if node.get("type") != "Text" or not text or not relative:
                continue
            path = ROOT / "Game" / relative
            if not path.is_file():
                missing.append({"widget": file.name, "node": node["id"], "font": relative, "reason": "missing-font-file"})
                continue
            if relative not in fonts:
                fonts[relative] = set(TTFont(path).getBestCmap())
            checked += 1
            glyphs = sorted({c for c in text if not c.isspace() and ord(c) not in fonts[relative]})
            if glyphs:
                missing.append({"widget": file.name, "node": node["id"], "font": relative,
                                "missing": glyphs, "codepoints": [f"U+{ord(c):04X}" for c in glyphs]})
    return {"scope": "Static authored native Text nodes only; dynamic text needs its own runtime inspection",
            "checkedTextNodes": checked, "fonts": len(fonts), "missing": missing,
            "allUIAcceptance": False}


if __name__ == "__main__":
    result = audit()
    output = ROOT / "docs/analysis/v3_rebuild/ui_font_coverage_20261103.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"checked": result["checkedTextNodes"], "missingNodes": len(result["missing"]), "report": str(output)}, ensure_ascii=False))
