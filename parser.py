# parser.py

import json
import html
from pathlib import Path

INPUT_PATH = Path("./data/pages_from_space_1572879.json")
OUTPUT_ROOT = Path("./data/space_1572879")


def build_output_dir(page: dict) -> Path:
    """
    space-id / folder-id 기준으로 디렉터리 생성 경로 결정
    예) ./data/exported_pages/space-589866/folder-184287517/
    parentId가 없으면 folder-root 로 처리
    """
    space_id = page.get("spaceId", "unknown-space")
    parent_id = page.get("parentId")

    space_dir = OUTPUT_ROOT / f"space-{space_id}"

    if parent_id:
        folder_dir = space_dir / f"folder-{parent_id}"
    else:
        folder_dir = space_dir / "folder-root"

    folder_dir.mkdir(parents=True, exist_ok=True)
    return folder_dir


def build_html_doc(page_id: str, title: str, body_html: str, page: dict) -> str:
    """
    CSS 포함된 HTML 문서 생성
    """
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


def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"총 {len(data)} 개의 페이지를 처리합니다.")

    html_count = 0
    json_count = 0

    for page in data:
        page_id = page.get("id")
        title = page.get("title", "")
        body_html = (
            page.get("body", {})
            .get("storage", {})
            .get("value", "")
        )

        if not page_id:
            print("[SKIP] id 없음 → 이 항목은 건너뜀")
            continue

        # 출력 디렉터리 결정 (space-id / folder-id 기준)
        out_dir = build_output_dir(page)

        # 1) 메타 JSON 저장: {id}.json
        meta_path = out_dir / f"{page_id}.json"
        meta_path.write_text(
            json.dumps(page, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        json_count += 1

        # body 없으면 HTML은 스킵 (메타만 저장)
        if not body_html:
            print(f"[WARN] body.storage.value 없음 → HTML 스킵, meta만 저장 (id={page_id})")
            continue

        # 2) HTML 저장: {id}.html
        html_doc = build_html_doc(page_id, title, body_html, page)
        html_path = out_dir / f"{page_id}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        html_count += 1

    print()
    print(f"HTML 파일   : {html_count} 개 생성")
    print(f"JSON 메타   : {json_count} 개 생성")
    print(f"출력 루트   : {OUTPUT_ROOT.resolve()}")


if __name__ == "__main__":
    main()