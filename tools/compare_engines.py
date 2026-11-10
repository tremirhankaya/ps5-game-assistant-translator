"""Translate the same sentences with every available engine and compare.

Usage:
    python tools/compare_engines.py
    python tools/compare_engines.py my_sentences.txt

Writes a Markdown report to tools/results/ so results can be shared.
"""
from __future__ import annotations

import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ps5_translator.translation import EchoEngine, available_engines  # noqa: E402


def load_sentences(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def run_engine(engine_cls, sentences):
    try:
        engine = engine_cls()
    except Exception as exc:
        return None, f"başlatılamadı: {exc}"

    warm_up = getattr(engine, "warm_up", None)
    if warm_up:
        print(f"  {engine.name}: model yükleniyor...")
        warm_up()

    rows = []
    for text in sentences:
        start = time.perf_counter()
        try:
            out = engine.translate(text)
        except Exception as exc:
            out = f"HATA: {exc}"
        rows.append((text, out, (time.perf_counter() - start) * 1000))
    return rows, None


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "sentences.txt"
    sentences = load_sentences(path)
    engines = [e for e in available_engines() if e is not EchoEngine]

    results = {}
    for engine_cls in engines:
        print(f"{engine_cls.name} deneniyor...")
        rows, error = run_engine(engine_cls, sentences)
        results[engine_cls.name] = (rows, error)
        if error:
            print(f"  atlandı ({error})")

    report = [f"# Motor karşılaştırması ({datetime.now():%Y-%m-%d %H:%M})", ""]
    report.append("| Motor | Ortalama ms | En yavaş ms | Hata |")
    report.append("|---|---|---|---|")
    for name, (rows, error) in results.items():
        if error:
            report.append(f"| {name} | - | - | {error} |")
            continue
        times = [ms for _, _, ms in rows]
        fails = sum(out.startswith("HATA") for _, out, _ in rows)
        report.append(f"| {name} | {statistics.mean(times):.0f} | {max(times):.0f} | {fails} |")

    for i, sentence in enumerate(sentences):
        report += ["", f"**{sentence}**", ""]
        for name, (rows, error) in results.items():
            if not error:
                _, out, ms = rows[i]
                report.append(f"- {name} ({ms:.0f} ms): {out}")

    out_dir = ROOT / "tools" / "results"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"compare-{datetime.now():%Y%m%d-%H%M%S}.md"
    out_file.write_text("\n".join(report) + "\n", encoding="utf-8")

    print()
    print("\n".join(report))
    print(f"\nRapor kaydedildi: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
