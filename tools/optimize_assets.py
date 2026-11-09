# 패키지 줄이기 : create-project.mjs 가 마지막에 부른다. 원본(repo 의 ui/·fonts/ 등)은 건드리지 않고 Game/Assets 만 바꾼다.
#  1) Game/Assets/Art 아래 PNG → WebP(q88, 알파 유지) 후 PNG 삭제, 위젯·장면·데이터 JSON·SVG 안의 경로도 .webp 로
#  2) 글꼴 : 게임에 나오는 글자(data/·Game/Source·Game/tools·생성된 Assets JSON)만 남긴 서브셋(fontTools)
# python tools/optimize_assets.py
import os, pathlib, re, sys, tempfile
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = ROOT / "Game" / "Assets"
EXACT_FONTS = {"gpu_trial", "gpu_panic", "gpu_anagram", "gpu_stage_clock", "gpu_showdown"}


def pngs(convert=True):
    n = before = after = 0
    for p in GAME.joinpath("Art").rglob("*.png") if convert else ():
        # Trial font bitmaps are exact raster output; preserve their alpha edges.
        if EXACT_FONTS.intersection(p.parts):
            continue
        w = p.with_suffix(".webp")
        before += p.stat().st_size
        im = Image.open(p)
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") or "transparency" in im.info else im.convert("RGB")
        im.save(w, "WEBP", quality=88, method=4, alpha_quality=100)
        after += w.stat().st_size
        p.unlink()
        n += 1
    pat = re.compile(r"(Assets/Art/[^\"'\s<>]+)\.(png|webp)(?![\w.-])")
    def reference(match):
        stem = match[1]
        if EXACT_FONTS.intersection(pathlib.PurePosixPath(stem).parts):
            # Repair older metadata that renamed a preserved glyph without
            # converting its pixels. Never point an exact glyph at lossy art.
            return stem + ".png" if (ROOT / "Game" / (stem + ".png")).is_file() else match[0]
        webp = ROOT / "Game" / (stem + ".webp")
        png = ROOT / "Game" / (stem + ".png")
        return stem + ".webp" if webp.is_file() and (convert or not png.is_file()) else match[0]
    for f in list(GAME.rglob("*.json")) + list(GAME.rglob("*.svg")):
        s = f.read_text(encoding="utf-8")
        t = pat.sub(reference, s)
        if t != s:
            # OneDrive can reject truncating an existing generated asset. Publish
            # the complete replacement in the same directory instead.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=f.parent, prefix=f.name + ".", suffix=".tmp", delete=False) as stream:
                    temporary = pathlib.Path(stream.name)
                    stream.write(t)
                os.replace(temporary, f)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    return n, before, after


def corpus():
    chars = set(chr(c) for c in range(0x20, 0x7F))
    chars |= set("…·「」『』《》〈〉※○●◎△▲▽▼□■◇◆☆★♪♡♥→←↑↓×÷～—–‘’“”、。！？")
    for base, pats in ((ROOT / "data", ("*.json", "*.txt")), (ROOT / "Game" / "Source", ("*.hpp", "*.cpp", "*.h")),
                       (ROOT / "Game" / "tools", ("*.mjs",)), (GAME, ("*.json",)),
                       (ROOT / "docs" / "design" / "rewrite_v5", ("*.md",)),
                       (ROOT / "tools", ("build_revised*.py", "revised_*.py"))):
        for pat in pats:
            for f in base.rglob(pat):
                try:
                    chars |= set(f.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
    return "".join(sorted(c for c in chars if c >= " "))


def fonts():
    from fontTools import subset
    text = corpus()
    before = after = 0
    for f in list(GAME.joinpath("Fonts").rglob("*.ttf")) + list(GAME.joinpath("Fonts").rglob("*.otf")):
        before += f.stat().st_size
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        relative = f.relative_to(GAME / "Fonts")
        aliases = {"BlackHanSans-Regular.ttf": "blackhansans/BlackHanSans-Regular.ttf",
                   "Pretendard-Medium.otf": "pretendard/Pretendard-Medium.otf"}
        source = ROOT / "fonts" / aliases.get(relative.as_posix(), relative.as_posix().replace("-VF", "[wght]"))
        # Always start with the authoring font: an earlier subset cannot supply newly added dialogue glyphs.
        font = subset.load_font(str(source), opts)
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=f.parent, prefix=f.name + ".", suffix=".tmp", delete=False) as stream:
                temporary = pathlib.Path(stream.name)
            subset.save_font(font, str(temporary), opts)
            font.close()
            os.replace(temporary, f)
        finally:
            font.close()
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        after += f.stat().st_size
    return len(text), before, after


if __name__ == "__main__":
    if "--fonts-only" in sys.argv:
        c, b, a = fonts()
        print(f"글꼴 서브셋 ({c}자) {b / 1e6:.0f}MB → {a / 1e6:.0f}MB")
        sys.exit(0)
    if "--paths-only" in sys.argv:
        pngs(convert=False)
        print("PNG/WebP references reconciled")
        sys.exit(0)
    from optimize_native_glb import optimize_generated_glbs
    optimize_generated_glbs()
    n, b, a = pngs()
    print(f"png→webp {n}개 {b / 1e6:.0f}MB → {a / 1e6:.0f}MB")
    c, b, a = fonts()
    print(f"글꼴 서브셋 ({c}자) {b / 1e6:.0f}MB → {a / 1e6:.0f}MB")
    sys.exit(0)
