# main.py

import json
import os
from pathlib import Path

from confluence_client import ConfluenceClient
from parser import parse_pages
from utils import setup_logging

logger = setup_logging("main")


def save_to_json(data: list | dict, output_path: str):
    """
    데이터를 JSON 파일로 저장합니다.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("데이터를 성공적으로 저장했습니다. -> %s", output_path)
    except (IOError, TypeError) as e:
        logger.error("파일 저장 중 오류 발생: %s", e)
        raise


def select_from_list(items: list[dict], prompt: str, key: str = "name") -> dict | None:
    """
    사용자에게 목록을 보여주고 선택을 받습니다.
    """
    logger.info(prompt)
    for i, item in enumerate(items):
        print(f"  [{i + 1}] {item[key]} (ID: {item['id']})")

    while True:
        try:
            selection = input("번호를 입력하세요: ")
            selected_index = int(selection) - 1
            if 0 <= selected_index < len(items):
                return items[selected_index]
            logger.warning("잘못된 번호입니다. 목록에 있는 번호를 입력해주세요.")
        except ValueError:
            logger.warning("숫자만 입력해야 합니다.")
        except (KeyboardInterrupt, EOFError):
            logger.info("\n작업을 중단합니다.")
            return None


def select_output_format() -> str | None:
    """
    출력 포맷을 선택합니다.
    """
    formats = [
        {"id": "html", "name": "HTML (CSS 포함된 문서)"},
        {"id": "markdown", "name": "Markdown (코드 블록 변환 포함)"},
        {"id": "both", "name": "HTML + Markdown (둘 다)"},
    ]

    logger.info("출력 포맷을 선택해주세요:")
    for i, fmt in enumerate(formats):
        print(f"  [{i + 1}] {fmt['name']}")

    while True:
        try:
            selection = input("번호를 입력하세요: ")
            selected_index = int(selection) - 1
            if 0 <= selected_index < len(formats):
                return formats[selected_index]["id"]
            logger.warning("잘못된 번호입니다. 목록에 있는 번호를 입력해주세요.")
        except ValueError:
            logger.warning("숫자만 입력해야 합니다.")
        except (KeyboardInterrupt, EOFError):
            logger.info("\n작업을 중단합니다.")
            return None


def interactive_backup_flow():
    """
    사용자 선택 기반의 대화형 백업 흐름을 관리합니다.
    다운로드 후 자동으로 선택한 포맷으로 변환합니다.
    """
    logger.info("Confluence 백업 작업을 시작합니다.")

    try:
        # 1. Confluence 클라이언트 초기화 및 Space 목록 가져오기
        client = ConfluenceClient()
        spaces = client.get_spaces()

        if not spaces:
            logger.warning("가져올 수 있는 Space가 없습니다. 작업을 종료합니다.")
            return

        # 2. Space 선택
        selected_space = select_from_list(spaces, "백업할 Space를 선택해주세요:")
        if not selected_space:
            return

        target_space_id = selected_space["id"]
        target_space_name = selected_space["name"]
        logger.info("선택된 Space: '%s' (ID: %s)", target_space_name, target_space_id)

        # 3. 출력 포맷 선택
        output_format = select_output_format()
        if not output_format:
            return
        logger.info("선택된 출력 포맷: %s", output_format)

        # 4. 페이지 데이터 가져오기
        pages = client.get_pages_from_space(space_id=target_space_id)

        if not pages:
            logger.warning("Space에 페이지가 없습니다.")
            return

        # 5. 원본 JSON 저장
        json_filename = f"pages_from_space_{target_space_id}.json"
        json_path = f"./data/{json_filename}"
        save_to_json(pages, json_path)

        # 6. 선택한 포맷으로 변환
        logger.info("==========================================================")
        logger.info("페이지 데이터 다운로드 완료. 변환을 시작합니다...")
        logger.info("==========================================================")

        output_root = Path(f"./data/space_{target_space_id}")
        results = parse_pages(pages, output_root, output_format, target_space_name)

        # 7. 결과 출력
        logger.info("==========================================================")
        logger.info("백업 및 변환이 완료되었습니다!")
        logger.info("원본 JSON: %s", json_path)
        logger.info("출력 디렉터리: %s", output_root.resolve())

        if "html" in results:
            logger.info(
                "  HTML: %d개 파일, JSON 메타: %d개",
                results["html"]["html_count"],
                results["html"]["json_count"],
            )

        if "markdown" in results:
            logger.info(
                "  Markdown: %d개 파일 (스킵: %d개)",
                results["markdown"]["md_count"],
                results["markdown"]["skipped_count"],
            )

        logger.info("==========================================================")

    except Exception as e:
        logger.error("작업 중 심각한 오류 발생: %s", e, exc_info=True)

    logger.info("Confluence 백업 작업을 종료합니다.")


if __name__ == "__main__":
    interactive_backup_flow()
