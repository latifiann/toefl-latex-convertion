#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=ROOT)


def compile_mode(practice_id: str, mode: str) -> None:
    run(["python3", "scripts/render_tex.py", "--practice-id", practice_id, "--mode", mode])

    tex_path = ROOT / "build" / "generated-tex" / f"{practice_id}-{mode}.tex"
    authoritative_pdf = ROOT / "build" / "pdf" / f"{practice_id}-{mode}.pdf"
    stray_pdf = tex_path.with_suffix(".pdf")

    if authoritative_pdf.exists():
        authoritative_pdf.unlink()
    if stray_pdf.exists():
        stray_pdf.unlink()

    run(
        [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            "build/pdf",
            str(tex_path.relative_to(ROOT)),
        ]
    )

    if stray_pdf.exists():
        stray_pdf.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice-id", default="P01")
    parser.add_argument("--mode", choices=["tryout", "review", "both"], default="both")
    args = parser.parse_args()

    modes = ["tryout", "review"] if args.mode == "both" else [args.mode]
    for mode in modes:
        compile_mode(args.practice_id, mode)


if __name__ == "__main__":
    main()
