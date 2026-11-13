"""out/report.json 을 template.html 에 넣어 주간 리포트 페이지를 만들고 docs/ 에 게시한다.

사용: python3 scripts/publish.py <WEEK_ID> <FROM> <TO>
"""
import datetime
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "out" / "report.json"
TEMPLATE = ROOT / "template.html"
CONFIG = ROOT / "config"
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports"
INDEX = DOCS / "reports.json"

WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_KEYS = ("summary", "top3", "items", "siren", "timeline", "lawTable",
             "media", "reports", "sourceStatus", "collected")
GRADES = {"긴급", "중요", "중간"}

# 템플릿 자체 스크립트만 허용, 외부 통신·외부 리소스 전면 차단
CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
       "script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
       "base-uri 'none'; form-action 'none'\">")


def fail(msg: str) -> None:
    sys.exit(f"[게시 중단] {msg}")


def load_report(week: str, d_from: str, d_to: str) -> dict:
    if not SRC.is_file():
        fail("out/report.json 이 없습니다.")
    raw = SRC.read_text(encoding="utf-8").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)  # 코드블록 표시가 섞인 경우 제거
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"JSON 형식 오류: {e}")
    if not isinstance(data, dict):
        fail("최상위가 객체가 아닙니다.")
    for k in LIST_KEYS:
        v = data.get(k)
        data[k] = v if isinstance(v, list) else []
    items = [i for i in data["items"] if isinstance(i, dict) and i.get("grade") in GRADES and i.get("title")]
    for n, i in enumerate(items, 1):
        i.setdefault("id", f"i{n}")
    data["items"] = items
    if not data["summary"] and not items:
        fail("요약과 주요 이슈가 모두 비어 있습니다.")
    # 주차·기간·생성시각은 실행 환경 값으로 고정
    data["id"], data["period"] = week, {"from": d_from, "to": d_to}
    data["generatedAt"] = datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    return data


def inject(html: str, block_id: str, obj) -> str:
    payload = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    pat = re.compile(r'(<script type="application/json" id="%s">)[\s\S]*?(</script>)' % block_id)
    new, n = pat.subn(lambda m: m.group(1) + payload + m.group(2), html, count=1)
    if n != 1:
        fail(f"템플릿에서 {block_id} 블록을 찾지 못했습니다.")
    return new


def main() -> None:
    if len(sys.argv) != 4:
        fail("사용법: publish.py <WEEK_ID> <FROM> <TO>")
    week, d_from, d_to = sys.argv[1:]
    if not WEEK_RE.match(week) or not DATE_RE.match(d_from) or not DATE_RE.match(d_to):
        fail("주차·날짜 형식이 올바르지 않습니다.")

    data = load_report(week, d_from, d_to)
    html = TEMPLATE.read_text(encoding="utf-8")
    html = inject(html, "report-data", data)
    for name, block in (("sources.json", "sources-data"), ("profile.json", "profile-data")):
        html = inject(html, block, json.loads((CONFIG / name).read_text(encoding="utf-8")))
    if "Content-Security-Policy" not in html:
        html, n = re.subn(r"<head[^>]*>", lambda m: m.group(0) + CSP, html, count=1, flags=re.I)
        if n == 0:
            fail("<head> 태그가 없습니다.")

    REPORTS.mkdir(parents=True, exist_ok=True)
    name = f"{week}.html"
    (REPORTS / name).write_text(html, encoding="utf-8")

    items = []
    if INDEX.is_file():
        try:
            items = json.loads(INDEX.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    items = [i for i in items if isinstance(i, dict) and i.get("file") != name and WEEK_RE.match(str(i.get("id", "")))]
    counts = {g: sum(1 for i in data["items"] if i["grade"] == g) for g in ("긴급", "중요", "중간")}
    items.append({"id": week, "file": name, "from": d_from, "to": d_to,
                  "title": f"긴급 {counts['긴급']} · 중요 {counts['중요']} · 중간 {counts['중간']}"})
    items.sort(key=lambda i: i["id"], reverse=True)
    INDEX.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOCS / "latest.html").write_text((REPORTS / items[0]["file"]).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"게시 완료: reports/{name} (누적 {len(items)}주)")


if __name__ == "__main__":
    main()
