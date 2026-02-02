# parser.py

import html
import json
import re
from pathlib import Path

from html_to_markdown import convert

from utils import setup_logging

logger = setup_logging("parser")

# Confluence 코드 매크로 정규식
CODE_MACRO_RE = re.compile(
    r'<ac:structured-macro\b[^>]*\bac:name="code"[^>]*>'
    r"(?:.*?)"
    r'(?:<ac:parameter\b[^>]*\bac:name="language"[^>]*>\s*'
    r"(?P<lang>[^<]+?)\s*</ac:parameter>)?"
    r"(?:.*?)"
    r"<ac:plain-text-body><!\[CDATA\[(?P<body>.*?)\]\]></ac:plain-text-body>"
    r"(?:.*?)</ac:structured-macro>",
    re.DOTALL,
)


def safe_filename(s: str) -> str:
    """파일명으로 사용할 수 있도록 문자열 정리"""
    s = (s or "").strip()
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", " ", s)
    return s[:120] or "untitled"


def confluence_code_macro_to_fence(html_content: str) -> str:
    """Confluence 코드 매크로를 마크다운 코드 펜스로 변환"""

    def _repl(m: re.Match) -> str:
        lang = (m.group("lang") or "").strip()
        body = (m.group("body") or "").replace("\r\n", "\n").rstrip("\n")
        fence = "```"
        if lang:
            return f"\n{fence}{lang}\n{body}\n{fence}\n"
        return f"\n{fence}\n{body}\n{fence}\n"

    return convert(CODE_MACRO_RE.sub(_repl, html_content))


def build_output_dir(page: dict, output_root: Path) -> Path:
    """
    space-id / folder-id 기준으로 디렉터리 생성 경로 결정
    """
    space_id = page.get("spaceId", "unknown-space")
    parent_id = page.get("parentId")

    space_dir = output_root / f"space-{space_id}"

    if parent_id:
        folder_dir = space_dir / f"folder-{parent_id}"
    else:
        folder_dir = space_dir / "folder-root"

    folder_dir.mkdir(parents=True, exist_ok=True)
    return folder_dir


def build_html_doc(page_id: str, title: str, body_html: str, page: dict) -> str:
    """CSS 포함된 HTML 문서 생성"""
    title_safe = html.escape(title or "")
    space_id = page.get("spaceId", "")
    parent_id = page.get("parentId", "")
    created_at = page.get("createdAt", "")
    status = page.get("status", "")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8" />
    <title>{title_safe}</title>
    <style>
        :root {{
            color-scheme: light dark;
        }}
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                         Roboto, "Noto Sans KR", sans-serif;
            margin: 0;
            padding: 2rem 1rem;
            background: #f5f5f7;
            color: #111111;
        }}
        .page-wrapper {{
            max-width: 960px;
            margin: 0 auto;
        }}
        .page-header {{
            margin-bottom: 1.5rem;
        }}
        h1 {{
            font-size: 1.9rem;
            margin: 0 0 0.5rem 0;
        }}
        .meta {{
            font-size: 0.85rem;
            color: #666;
        }}
        .meta span {{
            display: inline-block;
            margin-right: 1rem;
        }}
        .card {{
            background: #fafafa;
            color: #111111;
            border-radius: 10px;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04);
        }}
        .card :first-child {{
            margin-top: 0;
        }}
        .card :last-child {{
            margin-bottom: 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 1.5rem 0;
        }}
        code {{
            background: #f2f2f5;
            padding: 0.1rem 0.25rem;
            border-radius: 4px;
            font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
            font-size: 0.9em;
        }}
        pre code {{
            display: block;
            padding: 0.75rem 1rem;
            overflow-x: auto;
            background: #1e1e1e;
            color: #eaeaea;
        }}
        a {{
            color: #0070f3;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 2rem;
            font-size: 0.8rem;
            color: #888;
            text-align: center;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #111111
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <header class="page-header">
            <h1>{title_safe}</h1>
            <div class="meta">
                <span><strong>ID</strong> {page_id}</span>
                <span><strong>Space</strong> {space_id}</span>
                <span><strong>Folder</strong> {parent_id or "-"}</span>
                <span><strong>Status</strong> {status}</span>
                <span><strong>Created</strong> {created_at}</span>
            </div>
        </header>

        <main class="card">
{body_html}
        </main>

        <footer>
            <hr />
            <div>Exported from Confluence space {space_id} · Local backup view</div>
        </footer>
    </div>
</body>
</html>
"""


def convert_to_html(pages: list, output_root: Path) -> dict:
    """
    페이지 데이터를 HTML 파일로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :return: {"html_count": int, "json_count": int}
    """
    output_root.mkdir(parents=True, exist_ok=True)

    html_count = 0
    json_count = 0

    for page in pages:
        page_id = page.get("id")
        title = page.get("title", "")
        body_html = page.get("body", {}).get("storage", {}).get("value", "")

        if not page_id:
            logger.warning("[SKIP] id 없음 → 이 항목은 건너뜀")
            continue

        out_dir = build_output_dir(page, output_root)

        # 메타 JSON 저장
        meta_path = out_dir / f"{page_id}.json"
        meta_path.write_text(
            json.dumps(page, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        json_count += 1

        if not body_html:
            logger.warning(
                "[WARN] body.storage.value 없음 → HTML 스킵, meta만 저장 (id=%s)", page_id
            )
            continue

        # HTML 저장
        html_doc = build_html_doc(page_id, title, body_html, page)
        html_path = out_dir / f"{page_id}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        html_count += 1

    return {"html_count": html_count, "json_count": json_count}


def convert_to_markdown(pages: list, output_root: Path) -> dict:
    """
    페이지 데이터를 Markdown 파일로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :return: {"md_count": int, "skipped_count": int}
    """
    output_root.mkdir(parents=True, exist_ok=True)

    md_count = 0
    skipped_count = 0

    for page in pages:
        page_id = page.get("id")
        parent_id = page.get("parentId")
        parent_type = page.get("parentType", "page")
        space_id = page.get("spaceId")
        title = page.get("title", "")
        body_storage = page.get("body", {}).get("storage", {}).get("value", "")

        if not page_id:
            logger.warning("[SKIP] id 없음 → 이 항목은 건너뜀")
            skipped_count += 1
            continue

        if not body_storage:
            logger.warning("[SKIP] body 없음 (id=%s)", page_id)
            skipped_count += 1
            continue

        safe_title = safe_filename(title)
        md_body = confluence_code_macro_to_fence(body_storage)

        # 디렉터리 구조: parent_id_parent_type/page_id_title.md
        if parent_id:
            file_dir = output_root / f"{parent_id}_{parent_type}"
        else:
            file_dir = output_root / "root"

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / f"{page_id}_{safe_title}.md"

        content = f"# {title}\n\n"
        content += f"<!-- id: {page_id} | parent_id: {parent_id} | parent_type: {parent_type} | space_id: {space_id} -->\n\n"
        content += md_body

        file_path.write_text(content, encoding="utf-8")
        md_count += 1
        logger.info("Written: %s", file_path.name)

    return {"md_count": md_count, "skipped_count": skipped_count}


def parse_pages(
    pages: list,
    output_root: Path,
    output_format: str = "html",
) -> dict:
    """
    페이지 데이터를 지정된 포맷으로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :param output_format: "html", "markdown", 또는 "both"
    :return: 변환 결과 통계
    """
    results = {}

    if output_format in ("html", "both"):
        html_output = output_root / "html"
        html_result = convert_to_html(pages, html_output)
        results["html"] = html_result
        logger.info(
            "HTML 변환 완료: %d개 HTML, %d개 JSON",
            html_result["html_count"],
            html_result["json_count"],
        )

    if output_format in ("markdown", "both"):
        md_output = output_root / "markdown"
        md_result = convert_to_markdown(pages, md_output)
        results["markdown"] = md_result
        logger.info(
            "Markdown 변환 완료: %d개 MD, %d개 스킵",
            md_result["md_count"],
            md_result["skipped_count"],
        )

    return results


# CLI 지원 (단독 실행 시)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python parser.py <input_json> [output_dir] [format]")
        print("  format: html, markdown, both (기본값: html)")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/output")
    fmt = sys.argv[3] if len(sys.argv) > 3 else "html"

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"총 {len(data)} 개의 페이지를 처리합니다.")
    result = parse_pages(data, output_dir, fmt)
    print(f"변환 완료: {result}")
    print(f"출력 디렉터리: {output_dir.resolve()}")
