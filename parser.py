# parser.py

import html
import json
import re
import uuid
from pathlib import Path

from html_to_markdown import convert

from utils import setup_logging

# fontTools 패치: OS/2 테이블의 Unicode Range bit 123+ 처리 에러 수정
# WeasyPrint PDF 변환 시 한글 폰트 서브셋팅 오류 방지
import fontTools.ttLib.tables.O_S_2f_2 as _os2

_original_setUnicodeRanges = _os2.table_O_S_2f_2.setUnicodeRanges


def _patched_setUnicodeRanges(self, bits):
    """bit 123 이상의 비표준 Unicode Range bit를 무시"""
    filtered_bits = {b for b in bits if b <= 122}
    return _original_setUnicodeRanges(self, filtered_bits)


_os2.table_O_S_2f_2.setUnicodeRanges = _patched_setUnicodeRanges

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

# Confluence 이미지 매크로 정규식 - 첨부파일 이미지
AC_IMAGE_RE = re.compile(
    r'<ac:image[^>]*>'
    r'(?:.*?)'
    r'<ri:attachment\s+ri:filename="(?P<filename>[^"]+)"[^/]*/>'
    r'(?:.*?)'
    r'</ac:image>',
    re.DOTALL,
)

# Confluence 이미지 매크로 정규식 - 외부 URL 이미지
AC_IMAGE_URL_RE = re.compile(
    r'<ac:image\b'
    r'(?:[^>]*?\bac:alt="(?P<alt>[^"]*)")?'
    r'(?:[^>]*?\bac:src="(?P<acsrc>[^"]*)")?'
    r'[^>]*>'
    r'(?:.*?)'
    r'<ri:url\s+ri:value="(?P<url>[^"]+)"[^/]*/>'
    r'(?:.*?)'
    r'</ac:image>',
    re.DOTALL,
)

# Confluence expand 매크로 정규식
EXPAND_MACRO_RE = re.compile(
    r'<ac:structured-macro[^>]*ac:name="expand"[^>]*>'
    r'(?:.*?<ac:parameter[^>]*ac:name="title"[^>]*>(?P<title>[^<]*)</ac:parameter>)?'
    r'(?:.*?)<ac:rich-text-body>(?P<body>.*?)</ac:rich-text-body>'
    r'(?:.*?)</ac:structured-macro>',
    re.DOTALL,
)

# Confluence 알림 매크로 (tip, info, note, warning, panel) 정규식
CALLOUT_MACRO_RE = re.compile(
    r'<ac:structured-macro[^>]*ac:name="(?P<type>tip|info|note|warning|panel)"[^>]*>'
    r'(?:.*?)<ac:rich-text-body>(?P<body>.*?)</ac:rich-text-body>'
    r'(?:.*?)</ac:structured-macro>',
    re.DOTALL,
)

# Confluence TOC 매크로 정규식
TOC_MACRO_RE = re.compile(
    r'<ac:structured-macro[^>]*ac:name="toc"[^>]*>.*?</ac:structured-macro>',
    re.DOTALL,
)

# Confluence view-file 매크로 정규식
VIEW_FILE_MACRO_RE = re.compile(
    r'<ac:structured-macro[^>]*ac:name="view-file"[^>]*>'
    r'(?:.*?)<ac:parameter[^>]*ac:name="name"[^>]*>'
    r'<ri:attachment\s+ri:filename="(?P<filename>[^"]+)"[^/]*/>'
    r'</ac:parameter>'
    r'(?:.*?)</ac:structured-macro>',
    re.DOTALL,
)


def safe_filename(s: str) -> str:
    """파일명으로 사용할 수 있도록 문자열 정리 (특수문자/공백 -> 언더바)"""
    s = (s or "").strip()
    s = re.sub(r"[\\/:*?\"<>|\s]+", "_", s)  # 특수문자 + 공백 -> _
    s = re.sub(r"_+", "_", s)  # 연속 언더바 정리
    s = s.strip("_")
    return s[:120] or "untitled"


def convert_ac_image_to_img(html_content: str, attachments_path: str = "") -> str:
    """
    Confluence ac:image 태그를 표준 img 태그로 변환합니다.

    :param html_content: 변환할 HTML 콘텐츠
    :param attachments_path: 첨부파일이 저장된 상대 경로
    :return: 변환된 HTML
    """
    # 외부 URL 이미지 처리 (ri:url)
    def _repl_url(m: re.Match) -> str:
        url = m.group("url")
        alt = m.group("alt") or ""
        # ac:src를 fallback으로 사용
        if not url:
            url = m.group("acsrc") or ""
        alt_safe = html.escape(alt) if alt else "image"
        return f'<img src="{url}" alt="{alt_safe}" style="max-width: 100%;" />'

    content = AC_IMAGE_URL_RE.sub(_repl_url, html_content)

    # 첨부파일 이미지 처리 (ri:attachment)
    def _repl_attachment(m: re.Match) -> str:
        filename = m.group("filename")
        # 상대 경로로 이미지 참조
        src = f"{attachments_path}/{filename}" if attachments_path else filename
        alt = html.escape(filename)
        return f'<img src="{src}" alt="{alt}" style="max-width: 100%;" />'

    return AC_IMAGE_RE.sub(_repl_attachment, content)


def convert_expand_macro(html_content: str) -> str:
    """
    Confluence expand 매크로를 HTML details 태그로 변환합니다.
    """
    def _repl(m: re.Match) -> str:
        title = m.group("title") or "펼치기"
        body = m.group("body") or ""
        title_safe = html.escape(title)
        return f'<details><summary>{title_safe}</summary>{body}</details>'

    return EXPAND_MACRO_RE.sub(_repl, html_content)


def convert_callout_macros(html_content: str) -> str:
    """
    Confluence 알림 매크로(tip, info, note, warning, panel)를 스타일된 div로 변환합니다.
    """
    callout_styles = {
        "tip": "background: #e6f7e6; border-left: 4px solid #36b37e; padding: 1rem;",
        "info": "background: #e6f3ff; border-left: 4px solid #0065ff; padding: 1rem;",
        "note": "background: #fff8e6; border-left: 4px solid #ffab00; padding: 1rem;",
        "warning": "background: #ffebe6; border-left: 4px solid #de350b; padding: 1rem;",
        "panel": "background: #f4f5f7; border: 1px solid #dfe1e6; padding: 1rem; border-radius: 4px;",
    }

    def _repl(m: re.Match) -> str:
        callout_type = m.group("type")
        body = m.group("body") or ""
        style = callout_styles.get(callout_type, callout_styles["info"])
        return f'<div class="callout callout-{callout_type}" style="{style}">{body}</div>'

    return CALLOUT_MACRO_RE.sub(_repl, html_content)


def convert_toc_macro(html_content: str) -> str:
    """
    Confluence TOC 매크로를 제거합니다 (로컬 HTML에서는 불필요).
    """
    return TOC_MACRO_RE.sub("<!-- TOC removed -->", html_content)


def convert_view_file_macro(html_content: str, attachments_path: str = "") -> str:
    """
    Confluence view-file 매크로를 파일 링크로 변환합니다.
    """
    def _repl(m: re.Match) -> str:
        filename = m.group("filename")
        href = f"{attachments_path}/{filename}" if attachments_path else filename
        filename_safe = html.escape(filename)
        return f'<a href="{href}" class="attachment-link">📎 {filename_safe}</a>'

    return VIEW_FILE_MACRO_RE.sub(_repl, html_content)


def convert_all_macros(html_content: str, attachments_path: str = "", for_html: bool = True) -> str:
    """
    모든 Confluence 매크로를 HTML로 변환합니다.

    :param html_content: 변환할 HTML 콘텐츠
    :param attachments_path: 첨부파일 경로
    :param for_html: True면 HTML 출력용 (코드를 <pre><code>로 변환), False면 Markdown용 (코드 변환 제외)
    """
    content = convert_ac_image_to_img(html_content, attachments_path)
    if for_html:
        content = confluence_code_macro_to_html(content)
    content = convert_expand_macro(content)
    content = convert_callout_macros(content)
    content = convert_toc_macro(content)
    content = convert_view_file_macro(content, attachments_path)
    return content


def build_page_lookup(pages: list) -> dict:
    """페이지 ID -> 제목 매핑 생성"""
    return {page.get("id"): page.get("title", "") for page in pages}


def confluence_code_macro_to_html(html_content: str) -> str:
    """Confluence 코드 매크로를 HTML pre/code 태그로 변환 (HTML/PDF 출력용)"""

    def _repl(m: re.Match) -> str:
        lang = (m.group("lang") or "").strip()
        body = html.escape(m.group("body") or "").replace("\r\n", "\n")
        lang_attr = f' class="language-{lang}"' if lang else ""
        return f'<pre><code{lang_attr}>{body}</code></pre>'

    return CODE_MACRO_RE.sub(_repl, html_content)


def confluence_code_macro_to_fence(html_content: str) -> str:
    """Confluence 코드 매크로를 마크다운 코드 펜스로 변환 (placeholder 방식으로 보호)"""

    # 코드 블록을 placeholder로 저장
    code_blocks = {}

    def _extract_code(m: re.Match) -> str:
        lang = (m.group("lang") or "").strip()
        body = (m.group("body") or "").replace("\r\n", "\n").rstrip("\n")
        fence = "```"
        if lang:
            code_block = f"\n{fence}{lang}\n{body}\n{fence}\n"
        else:
            code_block = f"\n{fence}\n{body}\n{fence}\n"
        # 고유 placeholder 생성
        placeholder = f"__CODE_BLOCK_{uuid.uuid4().hex}__"
        code_blocks[placeholder] = code_block
        return placeholder

    # 코드 매크로를 placeholder로 대체
    content_with_placeholders = CODE_MACRO_RE.sub(_extract_code, html_content)

    # HTML을 마크다운으로 변환 (코드 블록은 placeholder로 보호됨)
    converted = convert(content_with_placeholders)

    # placeholder를 코드 블록으로 복원
    for placeholder, code_block in code_blocks.items():
        converted = converted.replace(placeholder, code_block)

    return converted


def build_output_dir(
    page: dict,
    output_root: Path,
    space_name: str = "",
    page_lookup: dict | None = None,
) -> Path:
    """
    space-id_name / folder-id_name 기준으로 디렉터리 생성 경로 결정
    """
    space_id = page.get("spaceId", "unknown-space")
    parent_id = page.get("parentId")

    # Space 디렉터리: space-{ID}_{NAME}
    space_safe = safe_filename(space_name)
    space_dir_name = f"space-{space_id}_{space_safe}" if space_safe else f"space-{space_id}"
    space_dir = output_root / space_dir_name

    if parent_id:
        # 부모 페이지 제목 조회
        parent_title = ""
        if page_lookup:
            parent_title = safe_filename(page_lookup.get(parent_id, ""))
        folder_name = f"folder-{parent_id}_{parent_title}" if parent_title else f"folder-{parent_id}"
        folder_dir = space_dir / folder_name
    else:
        folder_dir = space_dir / "folder-root"

    folder_dir.mkdir(parents=True, exist_ok=True)
    return folder_dir


def build_html_doc(
    page_id: str,
    title: str,
    body_html: str,
    page: dict,
    space_name: str = "",
    parent_name: str = "",
) -> str:
    """CSS 포함된 HTML 문서 생성 (A4 PDF 최적화)"""
    title_safe = html.escape(title or "")
    space_id = page.get("spaceId", "")
    parent_id = page.get("parentId", "")
    created_at = page.get("createdAt", "")
    status = page.get("status", "")

    # 메타정보: ID (이름) 형식
    space_display = f"{space_id} ({space_name})" if space_name else f"{space_id} (none)"
    parent_display = f"{parent_id} ({parent_name})" if parent_id else "none"
    if parent_id and not parent_name:
        parent_display = f"{parent_id} (none)"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8" />
    <title>{title_safe}</title>
    <style>
        /* PDF A4 페이지 설정 - 최소 여백 */
        @page {{
            size: A4;
            margin: 5mm;
        }}
        :root {{
            color-scheme: light dark;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                         "Noto Sans KR", "Malgun Gothic", sans-serif;
            margin: 0;
            padding: 3mm;
            background: #ffffff;
            color: #111111;
            font-size: 9pt;
            line-height: 1.4;
            max-width: 100%;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
        }}
        .page-wrapper {{
            max-width: 100%;
            margin: 0 auto;
            overflow: hidden;
        }}
        .page-header {{
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.3rem;
        }}
        h1 {{
            font-size: 14pt;
            margin: 0 0 0.3rem 0;
        }}
        h2 {{
            font-size: 12pt;
            margin: 0.5rem 0 0.3rem 0;
        }}
        h3 {{
            font-size: 10pt;
            margin: 0.4rem 0 0.2rem 0;
        }}
        h4, h5, h6 {{
            font-size: 9pt;
            margin: 0.3rem 0 0.2rem 0;
        }}
        .meta {{
            font-size: 7pt;
            color: #666;
            line-height: 1.4;
        }}
        .meta-row {{
            margin-bottom: 1px;
        }}
        .card {{
            background: #ffffff;
            color: #111111;
            padding: 0.3rem 0;
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
            margin: 0.5rem 0;
        }}
        code {{
            background: #f2f2f5;
            padding: 0.05rem 0.15rem;
            border-radius: 2px;
            font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
            font-size: 7pt;
            word-break: break-all;
        }}
        pre {{
            margin: 0.3rem 0;
            max-width: 100%;
            overflow-x: hidden;
        }}
        pre code {{
            display: block;
            padding: 0.3rem;
            background: #1e1e1e;
            color: #eaeaea;
            font-size: 6.5pt;
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-all;
            overflow-wrap: break-word;
        }}
        a {{
            color: #0070f3;
            text-decoration: none;
            word-break: break-all;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 0.8rem;
            font-size: 6pt;
            color: #888;
            text-align: center;
            border-top: 1px solid #e0e0e0;
            padding-top: 0.3rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #111111;
        }}
        /* 테이블 A4 너비 내 강제 맞춤 */
        table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 100%;
            table-layout: fixed;
            font-size: 7pt;
            margin: 0.3rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 2px 4px;
            text-align: left;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
            overflow: hidden;
        }}
        th {{
            background: #f5f5f5;
            font-size: 7pt;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}
        /* 콜아웃 스타일 조정 */
        .callout {{
            font-size: 8pt;
            margin: 0.3rem 0;
            padding: 0.3rem;
            max-width: 100%;
            overflow: hidden;
        }}
        details {{
            margin: 0.3rem 0;
            font-size: 8pt;
        }}
        summary {{
            cursor: pointer;
            font-weight: bold;
        }}
        /* 긴 텍스트/URL 강제 줄바꿈 */
        p, li, span, div {{
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
            max-width: 100%;
        }}
        ul, ol {{
            padding-left: 1.2em;
            margin: 0.2rem 0;
        }}
        li {{
            margin: 0.1rem 0;
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <header class="page-header">
            <h1>{title_safe}</h1>
            <div class="meta">
                <div class="meta-row"><strong>ID:</strong> {page_id}</div>
                <div class="meta-row"><strong>Space:</strong> {space_display}</div>
                <div class="meta-row"><strong>Parent:</strong> {parent_display}</div>
                <div class="meta-row"><strong>Status:</strong> {status} | <strong>Created:</strong> {created_at}</div>
            </div>
        </header>

        <main class="card">
{body_html}
        </main>

        <footer>
            Exported from Confluence · {space_display}
        </footer>
    </div>
</body>
</html>
"""


def convert_to_html(
    pages: list,
    output_root: Path,
    space_name: str = "",
    attachments_base: Path | None = None,
) -> dict:
    """
    페이지 데이터를 HTML 파일로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :param space_name: Space 이름
    :param attachments_base: 첨부파일이 저장된 기본 디렉터리
    :return: {"html_count": int, "json_count": int}
    """
    output_root.mkdir(parents=True, exist_ok=True)

    # 부모 페이지 제목 조회용 lookup 생성
    page_lookup = build_page_lookup(pages)

    html_count = 0
    json_count = 0

    for page in pages:
        page_id = page.get("id")
        title = page.get("title", "")
        body_html = page.get("body", {}).get("storage", {}).get("value", "")

        if not page_id:
            logger.warning("[SKIP] id 없음 → 이 항목은 건너뜀")
            continue

        safe_title = safe_filename(title)
        out_dir = build_output_dir(page, output_root, space_name, page_lookup)

        # 메타 JSON 저장: {id}_{title}.json
        meta_path = out_dir / f"{page_id}_{safe_title}.json"
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

        # Confluence 매크로를 HTML로 변환
        # HTML 위치: output_root/html/space-X/folder-Y/file.html
        # 첨부파일 위치: output_root/attachments/{page_id}/
        # 상대 경로: ../../../attachments/{page_id}/
        if attachments_base:
            attachments_path = f"../../../attachments/{page_id}"
        else:
            attachments_path = ""
        body_html = convert_all_macros(body_html, attachments_path, for_html=True)

        # 부모 페이지 이름 조회
        parent_id = page.get("parentId")
        parent_name = page_lookup.get(parent_id, "") if parent_id else ""

        # HTML 저장: {id}_{title}.html
        html_doc = build_html_doc(page_id, title, body_html, page, space_name, parent_name)
        html_path = out_dir / f"{page_id}_{safe_title}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        html_count += 1

    return {"html_count": html_count, "json_count": json_count}


def convert_to_markdown(
    pages: list,
    output_root: Path,
    space_name: str = "",
    attachments_base: Path | None = None,
) -> dict:
    """
    페이지 데이터를 Markdown 파일로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :param space_name: Space 이름
    :param attachments_base: 첨부파일이 저장된 기본 디렉터리
    :return: {"md_count": int, "skipped_count": int}
    """
    output_root.mkdir(parents=True, exist_ok=True)

    # 부모 페이지 제목 조회용 lookup 생성
    page_lookup = build_page_lookup(pages)

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

        # 첨부파일 경로 설정 (markdown에서 상대 경로로 참조)
        # Markdown 위치: output_root/markdown/space-X/folder-Y/file.md
        # 첨부파일 위치: output_root/attachments/{page_id}/
        # 상대 경로: ../../../attachments/{page_id}/
        if attachments_base:
            attachments_path = f"../../../attachments/{page_id}"
        else:
            attachments_path = ""

        # Confluence 매크로 변환 (코드 제외) - 이미지 등 처리
        body_converted = convert_all_macros(body_storage, attachments_path, for_html=False)
        # 코드 블록을 마크다운 펜스로 변환 (placeholder 보호 방식)
        md_body = confluence_code_macro_to_fence(body_converted)

        # Space 디렉터리
        space_safe = safe_filename(space_name)
        space_dir_name = f"space-{space_id}_{space_safe}" if space_safe else f"space-{space_id}"

        # 디렉터리 구조: space-{id}_{name}/folder-{parent_id}_{parent_title}/
        parent_name = page_lookup.get(parent_id, "") if parent_id else ""
        if parent_id:
            parent_title = safe_filename(parent_name)
            folder_name = f"folder-{parent_id}_{parent_title}" if parent_title else f"folder-{parent_id}"
            file_dir = output_root / space_dir_name / folder_name
        else:
            file_dir = output_root / space_dir_name / "folder-root"

        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / f"{page_id}_{safe_title}.md"

        # 메타정보: ID (이름) 형식
        space_display = f"{space_id} ({space_name})" if space_name else f"{space_id} (none)"
        parent_display = f"{parent_id} ({parent_name})" if parent_id else "none"
        if parent_id and not parent_name:
            parent_display = f"{parent_id} (none)"

        content = f"# {title}\n\n"
        content += f"<!-- id: {page_id} | space: {space_display} | parent: {parent_display} | status: {page.get('status', '')} -->\n\n"
        content += md_body

        file_path.write_text(content, encoding="utf-8")
        md_count += 1
        logger.info("Written: %s", file_path.name)

    return {"md_count": md_count, "skipped_count": skipped_count}


def convert_to_pdf(
    pages: list,
    output_root: Path,
    space_name: str = "",
    attachments_base: Path | None = None,
) -> dict:
    """
    페이지 데이터를 PDF 파일로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :param space_name: Space 이름
    :param attachments_base: 첨부파일이 저장된 기본 디렉터리
    :return: {"pdf_count": int, "skipped_count": int}
    """
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    output_root.mkdir(parents=True, exist_ok=True)
    font_config = FontConfiguration()

    page_lookup = build_page_lookup(pages)

    pdf_count = 0
    skipped_count = 0

    for page in pages:
        page_id = page.get("id")
        title = page.get("title", "")
        body_html = page.get("body", {}).get("storage", {}).get("value", "")

        if not page_id:
            logger.warning("[SKIP] id 없음 → 이 항목은 건너뜀")
            skipped_count += 1
            continue

        if not body_html:
            logger.warning("[SKIP] body 없음 (id=%s)", page_id)
            skipped_count += 1
            continue

        safe_title = safe_filename(title)
        out_dir = build_output_dir(page, output_root, space_name, page_lookup)

        # Confluence 매크로를 HTML로 변환 (file:// 절대 경로 사용)
        if attachments_base:
            attachments_path = f"file://{(attachments_base / page_id).resolve()}"
        else:
            attachments_path = ""
        body_html = convert_all_macros(body_html, attachments_path, for_html=True)

        # 부모 페이지 이름 조회
        parent_id = page.get("parentId")
        parent_name = page_lookup.get(parent_id, "") if parent_id else ""

        # HTML 문서 생성
        html_doc = build_html_doc(page_id, title, body_html, page, space_name, parent_name)

        # PDF 저장: {id}_{title}.pdf
        pdf_path = out_dir / f"{page_id}_{safe_title}.pdf"
        try:
            # optimize_size=() 로 폰트 서브셋팅 비활성화
            HTML(string=html_doc).write_pdf(
                pdf_path,
                font_config=font_config,
                optimize_size=(),
            )
            pdf_count += 1
            logger.info("Written: %s", pdf_path.name)
        except Exception as e:
            logger.warning("[WARN] PDF 변환 실패 (id=%s): %s", page_id, e)
            skipped_count += 1

    return {"pdf_count": pdf_count, "skipped_count": skipped_count}


def parse_pages(
    pages: list,
    output_root: Path,
    output_format: str = "html",
    space_name: str = "",
    attachments_base: Path | None = None,
) -> dict:
    """
    페이지 데이터를 지정된 포맷으로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param output_root: 출력 루트 디렉터리
    :param output_format: "html", "markdown", "pdf", "both", 또는 "all"
    :param space_name: Space 이름
    :param attachments_base: 첨부파일이 저장된 기본 디렉터리
    :return: 변환 결과 통계
    """
    results = {}

    if output_format in ("html", "both", "all"):
        html_output = output_root / "html"
        html_result = convert_to_html(pages, html_output, space_name, attachments_base)
        results["html"] = html_result
        logger.info(
            "HTML 변환 완료: %d개 HTML, %d개 JSON",
            html_result["html_count"],
            html_result["json_count"],
        )

    if output_format in ("markdown", "both", "all"):
        md_output = output_root / "markdown"
        md_result = convert_to_markdown(pages, md_output, space_name, attachments_base)
        results["markdown"] = md_result
        logger.info(
            "Markdown 변환 완료: %d개 MD, %d개 스킵",
            md_result["md_count"],
            md_result["skipped_count"],
        )

    if output_format in ("pdf", "all"):
        pdf_output = output_root / "pdf"
        pdf_result = convert_to_pdf(pages, pdf_output, space_name, attachments_base)
        results["pdf"] = pdf_result
        logger.info(
            "PDF 변환 완료: %d개 PDF, %d개 스킵",
            pdf_result["pdf_count"],
            pdf_result["skipped_count"],
        )

    return results


# CLI 지원 (단독 실행 시)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python parser.py <input_json> [output_dir] [format] [space_name]")
        print("  format: html, markdown, both (기본값: html)")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/output")
    fmt = sys.argv[3] if len(sys.argv) > 3 else "html"
    space_name_arg = sys.argv[4] if len(sys.argv) > 4 else ""

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"총 {len(data)} 개의 페이지를 처리합니다.")
    result = parse_pages(data, output_dir, fmt, space_name_arg)
    print(f"변환 완료: {result}")
    print(f"출력 디렉터리: {output_dir.resolve()}")
