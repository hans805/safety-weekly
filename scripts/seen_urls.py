"""최근 주차 리포트(docs/reports/YYYY-Www.html)에 이미 실린 URL을 모아 out/seen.txt 로 만든다.
Claude가 같은 글을 다시 읽지 않도록 해서 중복 수집과 사용량 낭비를 막는다."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "docs" / "reports"
OUT = ROOT / "out" / "seen.txt"
KEEP_WEEKS = 4


def urls(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "url" and isinstance(v, str) and v.startswith("http"):
                yield v
            else:
                yield from urls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from urls(v)


def main() -> None:
    files = sorted(REPORTS.glob("*-W*.html"), reverse=True)[:KEEP_WEEKS]
    seen = set()
    for f in files:
        m = re.search(r'id="report-data">(.*?)</script>', f.read_text(encoding="utf-8", errors="replace"), re.S)
        if not m:
            continue
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        # 다음 주에 반영하기로 한 글은 다시 볼 수 있게 남겨 둔다
        for c in data.get("collected", []):
            if isinstance(c, dict) and "다음 주" in str(c.get("use", "")):
                c["url"] = None
        seen.update(urls(data))
    # 수집 대상 목록 페이지 주소는 매주 다시 봐야 하므로 제외
    try:
        src = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
        seen -= {s.get("url") for s in src if isinstance(s, dict)}
    except (OSError, json.JSONDecodeError):
        pass
    seen = {u for u in seen if not re.search(r"(list\.do|/CSADV|/all-industry)", u)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(sorted(seen)) + "\n", encoding="utf-8")
    print(f"이미 다룬 URL {len(seen)}건 (최근 {len(files)}주)")


if __name__ == "__main__":
    main()
