"""out/report.json 을 template.html 에 넣어 대시보드형 주간 리포트(docs/reports/<WEEK>.html)를 만든다.
사용: python3 scripts/publish_dashboard.py <WEEK_ID> <FROM> <TO>   (목록 갱신은 build_index.py)"""
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
REPORTS = ROOT / "docs" / "reports"
WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_KEYS = ("summary", "top3", "items", "siren", "timeline", "lawTable",
             "media", "reports", "sourceStatus", "collected")
GRADES = {"긴급", "중요", "중간"}
CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
       "script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
       "base-uri 'none'; form-action 'none'\">")


def fail(msg: str) -> None:
    sys.exit(f"[게시 중단] {msg}")


def inject(html: str, block_id: str, obj) -> str:
    payload = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    pat = re.compile(r'(<script type="application/json" id="%s">)[\s\S]*?(</script>)' % block_id)
    new, n = pat.subn(lambda m: m.group(1) + payload + m.group(2), html, count=1)
    if n != 1:
        fail(f"템플릿에서 {block_id} 블록을 찾지 못했습니다.")
    return new


def main() -> None:
    if len(sys.argv) != 4:
        fail("사용법: publish_dashboard.py <WEEK_ID> <FROM> <TO>")
    week, d_from, d_to = sys.argv[1:]
    if not (WEEK_RE.match(week) and DATE_RE.match(d_from) and DATE_RE.match(d_to)):
        fail("주차·날짜 형식이 올바르지 않습니다.")
    if not SRC.is_file():
        fail("out/report.json 이 없습니다.")
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", SRC.read_text(encoding="utf-8").strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"JSON 형식 오류: {e}")
    if not isinstance(data, dict):
        fail("최상위가 객체가 아닙니다.")
    for k in LIST_KEYS:
        if not isinstance(data.get(k), list):
            data[k] = []
    data["items"] = [i for i in data["items"] if isinstance(i, dict) and i.get("grade") in GRADES and i.get("title")]
    for n, i in enumerate(data["items"], 1):
        i.setdefault("id", f"i{n}")
    if not data["summary"] and not data["items"]:
        fail("요약과 주요 이슈가 모두 비어 있습니다.")
    data["id"], data["period"] = week, {"from": d_from, "to": d_to}
    data["generatedAt"] = datetime.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

    html = inject(TEMPLATE.read_text(encoding="utf-8"), "report-data", data)
    for name, block in (("sources.json", "sources-data"), ("profile.json", "profile-data")):
        html = inject(html, block, json.loads((CONFIG / name).read_text(encoding="utf-8")))
    if "Content-Security-Policy" not in html:
        html = re.sub(r"<head[^>]*>", lambda m: m.group(0) + CSP, html, count=1, flags=re.I)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{week}.html").write_text(html, encoding="utf-8")
    print(f"게시 준비 완료: reports/{week}.html")


if __name__ == "__main__":
    main()
