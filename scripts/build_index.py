"""docs/reports/ 폴더의 리포트 파일을 훑어 목록(reports.json)과 latest.html 을 다시 만든다.
직접 올린 HTML도 파일명 규칙(2026-W46.html 또는 2026-11-16.html)만 맞으면 자동으로 목록에 들어간다."""
import json
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
REPORTS = DOCS / "reports"
WEEK_RE = re.compile(r"^(\d{4}-W\d{2})\.html$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")


def entry(path: Path):
    html = path.read_text(encoding="utf-8", errors="replace")
    m = WEEK_RE.match(path.name)
    if m:
        e = {"id": m.group(1), "file": path.name, "title": "주간 리포트"}
        d = re.search(r'id="report-data">(.*?)</script>', html, re.S)
        if d:
            try:
                data = json.loads(d.group(1))
                p = data.get("period") or {}
                e["from"], e["to"] = str(p.get("from", "")), str(p.get("to", ""))
                g = [i.get("grade") for i in data.get("items", []) if isinstance(i, dict)]
                e["title"] = f"긴급 {g.count('긴급')} · 중요 {g.count('중요')} · 중간 {g.count('중간')}"
            except (json.JSONDecodeError, AttributeError):
                pass
        return e
    m = DATE_RE.match(path.name)
    if m:
        t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        title = re.sub(r"\s+", " ", t.group(1)).strip()[:120] if t else "주간 리포트"
        return {"date": m.group(1), "file": path.name, "title": title}
    return None


def main() -> None:
    items = [e for e in (entry(p) for p in sorted(REPORTS.glob("*.html"))) if e]
    items.sort(key=lambda i: str(i.get("date") or i.get("from") or ""), reverse=True)
    (DOCS / "reports.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    if items:
        (DOCS / "latest.html").write_bytes((REPORTS / items[0]["file"]).read_bytes())
    print(f"목록 갱신: {len(items)}건")


if __name__ == "__main__":
    main()
