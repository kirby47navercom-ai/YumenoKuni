"""Decode the existing approved cue bank; never extracts or rewrites audio."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    assert ffmpeg and ffprobe, "Use the installed media tools; do not download replacements."
    cue_file = ROOT / "audio/cues.json"
    bank = json.loads(cue_file.read_text(encoding="utf-8"))
    files = {}
    for group, items in bank.items():
        if not isinstance(items, dict):
            continue
        for cue, row in items.items():
            if not isinstance(row, dict):
                continue
            for role in ("file", "intro"):
                if row.get(role):
                    files.setdefault(row[role], []).append({"cue": cue, "group": group, "role": role, "use": row.get("use", "")})

    def analyze(item):
        relative, uses = item
        source = ROOT / "audio" / relative
        result = {"file": source.relative_to(ROOT).as_posix(), "uses": uses, "decoded": False}
        if not source.is_file():
            return {**result, "error": "Missing approved cue file"}
        result["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        metadata = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels", "-of", "json", str(source)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if metadata.returncode:
            return {**result, "error": metadata.stderr[-1000:]}
        info = json.loads(metadata.stdout)
        result["durationSeconds"] = float(info["format"]["duration"])
        result["streams"] = info["streams"]
        decoded = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-v", "info", "-i", str(source), "-vn", "-af", "astats=metadata=0:reset=0", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        overall = decoded.stderr.rsplit("Overall", 1)[-1]
        for label, key in [("Peak level dB", "peakDB"), ("RMS level dB", "rmsDB"), ("Number of samples", "samples"), ("Number of NaNs", "nanSamples"), ("Number of Infs", "infiniteSamples")]:
            match = re.search(re.escape(label) + r":\s*([-+\w.]+)", overall)
            if match:
                value = float(match[1])
                result[key] = value if math.isfinite(value) else str(value)
        result["decoded"] = decoded.returncode == 0 and result.get("samples", 0) > 0 and result["durationSeconds"] > 0 and result.get("nanSamples", 0) == 0 and result.get("infiniteSamples", 0) == 0
        if not result["decoded"]:
            result["error"] = decoded.stderr[-1600:]
        result["silent"] = result.get("rmsDB") == "-inf"
        return result

    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(analyze, files.items()):
            results.append(result)
            if len(results) % 25 == 0:
                print(json.dumps({"decodedFiles": len(results), "total": len(files), "failures": sum(not x["decoded"] for x in results)}), flush=True)
    report = {"ok": all(r["decoded"] for r in results), "scope": "Full offline decode/sample validity, duration and peak/RMS of the existing approved cue bank. No original archive extraction, audio rewrite, human listening or native mixer equivalence claim.",
              "cueBankSHA256": hashlib.sha256(cue_file.read_bytes()).hexdigest(), "files": results,
              "silentFiles": [r["file"] for r in results if r["silent"]], "decodedSeconds": sum(r.get("durationSeconds", 0) for r in results),
              "failures": [r for r in results if not r["decoded"]]}
    (ROOT / "Game/Saved/audio-full-decode-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "files": len(results), "silentFiles": report["silentFiles"], "failures": len(report["failures"])}))
    return report["ok"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
