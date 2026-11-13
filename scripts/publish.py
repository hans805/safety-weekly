"""Claude가 만든 out/report.html 을 docs/ 에 게시하고 목록(reports.json)을 갱신한다."""
import datetime
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "out" / "report.html"
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports"
INDEX = DOCS / "reports.json"

# 리포트 안에서 스크립트 실행을 원천 차단 (외부 수집 내용이 섞이므로 보안상 필수)
CSP = (
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
    "style-src 'unsafe-inline' https://cdn.jsdelivr.net; "
    "font-src https://cdn.jsdelivr.net; img-src data:; "
    "base-uri 'none'; form-action 'none'\">"
)


def main() -> None:
    if not SRC.is_file():
        sys.exit("out/report.html 이 없습니다.")
    html = SRC.read_text(encoding="utf-8")
    if len(html) < 2000 or "<html" not in html.lower():
        sys.exit("리포트 내용이 비정상입니다(너무 짧거나 HTML 아님).")

    html, n = re.subn(r"<head[^>]*>", lambda m: m.group(0) + CSP, html, count=1, flags=re.I)
    if n == 0:
        sys.exit("<head> 태그가 없어 보안 정책을 넣을 수 없습니다.")

    today = datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I)
    title = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else f"주간 안전보건 동향 ({today})"

    REPORTS.mkdir(parents=True, exist_ok=True)
    name = f"{today}.html"
    (REPORTS / name).write_text(html, encoding="utf-8")
    (DOCS / "latest.html").write_text(html, encoding="utf-8")

    items = []
    if INDEX.is_file():
        try:
            items = json.loads(INDEX.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    items = [i for i in items if isinstance(i, dict) and i.get("file") != name]
    items.append({"date": today, "file": name, "title": title})
    items.sort(key=lambda i: i.get("date", ""), reverse=True)
    INDEX.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"게시 완료: reports/{name} (누적 {len(items)}건)")


if __name__ == "__main__":
    main()
