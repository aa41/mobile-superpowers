#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable


Comparer = Callable[..., dict[str, Any]]


def pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def pillow_compare(*, reference: Path, candidate: Path, out_dir: Path, prefix: str, clips: list[str]) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageEnhance, ImageStat
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Pillow is required for image comparison. "
            "Run `python3 mobile-superpowers/scripts/mobile_visual_deps.py --install` "
            "or run with a custom comparer."
        ) from exc

    def load_rgb(path: Path):
        return Image.open(path).convert("RGB")

    def fit_to_reference(candidate_img, reference_img):
        if candidate_img.size == reference_img.size:
            return candidate_img
        return candidate_img.resize(reference_img.size, Image.Resampling.LANCZOS)

    def rms(diff_img) -> float:
        stat = ImageStat.Stat(diff_img)
        return math.sqrt(sum(value * value for value in stat.rms) / len(stat.rms))

    def mean_abs(diff_img) -> float:
        stat = ImageStat.Stat(diff_img)
        return sum(stat.mean) / len(stat.mean)

    def make_heatmap(diff_img):
        gray = diff_img.convert("L")
        boosted = ImageEnhance.Contrast(gray).enhance(2.2)
        boosted = ImageEnhance.Brightness(boosted).enhance(1.5)
        heat = Image.new("RGB", diff_img.size, (255, 255, 255))
        red = Image.new("RGB", diff_img.size, (255, 55, 55))
        heat.paste(red, mask=boosted)
        return heat

    reference_img = load_rgb(reference)
    candidate_original = load_rgb(candidate)
    candidate_img = fit_to_reference(candidate_original, reference_img)

    def compare_region(name: str, ref_img, cand_img) -> dict[str, Any]:
        diff = ImageChops.difference(ref_img, cand_img)
        normalized_candidate = out_dir / f"{prefix}-{name}-candidate.png"
        diff_path = out_dir / f"{prefix}-{name}-diff.png"
        heatmap_path = out_dir / f"{prefix}-{name}-heatmap.png"
        cand_img.save(normalized_candidate)
        diff.save(diff_path)
        make_heatmap(diff).save(heatmap_path)
        return {
            "name": name,
            "size": list(ref_img.size),
            "rms_diff": round(rms(diff), 3),
            "mean_abs_diff": round(mean_abs(diff), 3),
            "candidate": str(normalized_candidate),
            "diff": str(diff_path),
            "heatmap": str(heatmap_path),
        }

    regions = [compare_region("full", reference_img, candidate_img)]
    for raw_clip in clips:
        name, box = parse_clip(raw_clip)
        regions.append(compare_region(name, reference_img.crop(box), candidate_img.crop(box)))

    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "reference_size": list(reference_img.size),
        "candidate_size_original": list(candidate_original.size),
        "candidate_size_compared": list(candidate_img.size),
        "regions": regions,
        "clips": clips,
    }


def parse_clip(raw_clip: str) -> tuple[str, tuple[int, int, int, int]]:
    try:
        name, raw_box = raw_clip.split(":", 1)
        x, y, width, height = [int(part) for part in raw_box.split(",")]
    except Exception as exc:
        raise ValueError(f"invalid clip {raw_clip!r}; expected name:x,y,w,h") from exc
    return name, (x, y, x + width, y + height)


def replace_section(text: str, section: str, replacement_lines: list[str]) -> str:
    marker = f"## {section}"
    start = text.find(marker)
    if start == -1:
        return text.rstrip() + "\n\n" + marker + "\n\n" + "\n".join(replacement_lines) + "\n"
    next_start = text.find("\n## ", start + len(marker))
    replacement = marker + "\n\n" + "\n".join(replacement_lines) + "\n"
    if next_start == -1:
        return text[:start] + replacement
    return text[:start] + replacement + text[next_start:]


def update_visual_contract(*, contract_path: Path, metrics: dict[str, Any], metrics_path: Path) -> None:
    if not contract_path.exists():
        return
    regions = metrics.get("regions", [])
    primary = regions[0] if regions else {}
    lines = [
        f"- Baseline metrics: `{metrics_path}`",
        f"- Reference: `{metrics.get('reference', '')}`",
        f"- Candidate: `{metrics.get('candidate', '')}`",
    ]
    if primary:
        lines.extend(
            [
                f"- Full RMS diff: `{primary.get('rms_diff')}`",
                f"- Full mean absolute diff: `{primary.get('mean_abs_diff')}`",
                f"- Full diff: `{primary.get('diff')}`",
                f"- Full heatmap: `{primary.get('heatmap')}`",
            ]
        )
    lines.append("- Completion assessment: not reviewed by human yet.")
    text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(replace_section(text, "Similarity Results", lines), encoding="utf-8")


def compare_visuals(
    *,
    reference: Path | str,
    candidate: Path | str,
    out_dir: Path | str | None = None,
    prefix: str = "baseline",
    clips: list[str] | None = None,
    comparer: Comparer | None = None,
) -> dict[str, Any]:
    reference = Path(reference).expanduser().resolve()
    candidate = Path(candidate).expanduser().resolve()
    out_dir = Path(out_dir).expanduser().resolve() if out_dir else candidate.parent
    clips = clips or []
    metrics_path = out_dir / "baseline-metrics.json"
    contract_path = candidate.parent / "visual-contract.md"

    errors: list[str] = []
    if not reference.exists():
        errors.append(f"reference image not found: {reference}")
    if not candidate.exists():
        errors.append(f"candidate image not found: {candidate}")
    for raw_clip in clips:
        try:
            parse_clip(raw_clip)
        except ValueError as exc:
            errors.append(str(exc))

    result = {
        "metrics": str(metrics_path),
        "out_dir": str(out_dir),
        "visual_contract": str(contract_path),
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result

    out_dir.mkdir(parents=True, exist_ok=True)
    selected_comparer = comparer or pillow_compare
    try:
        metrics = selected_comparer(
            reference=reference,
            candidate=candidate,
            out_dir=out_dir,
            prefix=prefix,
            clips=clips,
        )
    except RuntimeError as exc:
        result["validation"]["errors"].append(str(exc))
        return result

    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    update_visual_contract(contract_path=contract_path, metrics=metrics, metrics_path=metrics_path)
    return {**result, "regions": metrics.get("regions", [])}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare a reference image against a baseline screenshot.")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--prefix", default="baseline")
    parser.add_argument("--clip", action="append", default=[])
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = compare_visuals(
        reference=args.reference,
        candidate=args.candidate,
        out_dir=args.out_dir,
        prefix=args.prefix,
        clips=args.clip,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["metrics"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
