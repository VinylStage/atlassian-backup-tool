# parsing_tests.py

import json
import re
from pathlib import Path

from utils import setup_logging
from html_to_markdown import convert

logger = setup_logging("utils")

CODE_MACRO_RE = re.compile(
    r'<ac:structured-macro\b[^>]*\bac:name="code"[^>]*>'  # code macro 시작
    r"(?:.*?)"  # 중간 내용(파라미터 포함 가능)
    r'(?:<ac:parameter\b[^>]*\bac:name="language"[^>]*>\s*'  # (옵션) language 파라미터
    r"(?P<lang>[^<]+?)\s*</ac:parameter>)?"
    r"(?:.*?)"
    r"<ac:plain-text-body><!\[CDATA\[(?P<body>.*?)\]\]></ac:plain-text-body>"
    r"(?:.*?)</ac:structured-macro>",
    re.DOTALL,
)


def read_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_filename(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)  # 윈도우 금지문자 대응
    s = re.sub(r"\s+", " ", s)
    return s[:120] or "untitled"


def confluence_code_macro_to_fence(html: str) -> str:
    def _repl(m: re.Match) -> str:
        lang = (m.group("lang") or "").strip()
        body = (m.group("body") or "").replace("\r\n", "\n").rstrip("\n")

        fence = "```"
        if lang:
            return f"\n{fence}{lang}\n{body}\n{fence}\n"
        return f"\n{fence}\n{body}\n{fence}\n"

    md_body = convert(CODE_MACRO_RE.sub(_repl, html))
    return md_body


def iter_transformed(data):
    for page in data:
        page_id = page["id"]
        parent_id = page["parentId"]
        parent_type = page["parentType"]
        space_id = page["spaceId"]
        title = page["title"]
        body = page["body"]["storage"]["value"]

        yield {
            "id": page_id,
            "parent_id": parent_id,
            "parent_type": parent_type,
            "space_id": space_id,
            "title": safe_filename(title),
            "body": confluence_code_macro_to_fence(body),
        }


def write_md_files(data, output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for item in iter_transformed(data):
        page_id = item["id"]
        parent_id = item["parent_id"]
        parent_type = item["parent_type"]
        space_id = item["space_id"]
        title = item["title"]
        body = item["body"]
        logger.info("Writing page: %s (ID: %s)", title, page_id)
        if page_id:
            logger.info("  Parent: %s (ID: %s)", parent_type, parent_id)
            file_name = f"{parent_id}_{parent_type}/{page_id}_{title}.md"
            file_path = output_path / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            logger.info("  No parent information available.")
            file_name = f"{page_id}_{title}.md"
            file_path = output_path / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(
                f"<!-- id: {page_id} | parent_id: {parent_id} | parent_type: {parent_type} | space_id: {space_id} -->\n\n"
            )
            f.write(body)
            logger.info("  Written to: %s", file_path)


if __name__ == "__main__":
    data = read_json("./data/sample.json")
    write_md_files(data, "./data/sample_md")
