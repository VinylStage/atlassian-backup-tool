# main.py

import json
import os
from pathlib import Path

from confluence_client import ConfluenceClient
from parser import parse_pages, build_output_path_tree, build_page_map, safe_filename
from tree_builder import build_tree, print_tree, save_tree_json, get_tree_stats
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
        {"id": "both", "name": "HTML + Markdown"},
        {"id": "pdf", "name": "PDF (인쇄용 문서)"},
        {"id": "all", "name": "전체 (HTML + Markdown + PDF)"},
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


def select_main_menu() -> int | None:
    """
    메인 메뉴를 선택합니다.
    """
    print("\n" + "=" * 60)
    print("  Confluence Backup Tool")
    print("=" * 60)
    print("  [1] 백업 및 변환")
    print("  [2] 트리 구조 조회")
    print("  [3] 종료")
    print("=" * 60)

    while True:
        try:
            selection = input("메뉴를 선택하세요: ")
            menu = int(selection)
            if 1 <= menu <= 3:
                return menu
            logger.warning("잘못된 번호입니다. 1-3 사이의 번호를 입력해주세요.")
        except ValueError:
            logger.warning("숫자만 입력해야 합니다.")
        except (KeyboardInterrupt, EOFError):
            return 3  # 종료


def backup_flow(client: ConfluenceClient):
    """
    백업 및 변환 흐름을 실행합니다.
    """
    spaces = client.get_spaces()

    if not spaces:
        logger.warning("가져올 수 있는 Space가 없습니다.")
        return

    # Space 선택
    selected_space = select_from_list(spaces, "백업할 Space를 선택해주세요:")
    if not selected_space:
        return

    target_space_id = selected_space["id"]
    target_space_name = selected_space["name"]
    logger.info("선택된 Space: '%s' (ID: %s)", target_space_name, target_space_id)

    # 출력 포맷 선택
    output_format = select_output_format()
    if not output_format:
        return
    logger.info("선택된 출력 포맷: %s", output_format)

    # 페이지 데이터 가져오기
    pages = client.get_pages_from_space(space_id=target_space_id)

    if not pages:
        logger.warning("Space에 페이지가 없습니다.")
        return

    # 출력 디렉터리 설정: data/{SPACE_ID}_{SPACE_NAME}/
    space_safe = safe_filename(target_space_name)
    output_root = Path(f"./data/{target_space_id}_{space_safe}")

    # 메타 데이터 디렉터리 생성
    meta_dir = output_root / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    # 원본 JSON 저장 (메타 디렉터리에)
    json_path = meta_dir / "pages.json"
    save_to_json(pages, str(json_path))

    # 페이지 맵 생성 (트리 구조 경로 계산용)
    page_map = build_page_map(pages)

    # 첨부파일 다운로드 (각 페이지의 출력 디렉터리에 저장)
    logger.info("==========================================================")
    logger.info("첨부파일 다운로드를 시작합니다...")
    logger.info("==========================================================")

    total_downloaded = 0
    total_failed = 0
    for page in pages:
        page_id = page.get("id")
        if not page_id:
            continue
        try:
            # 트리 구조에 따른 페이지 출력 디렉터리 결정
            page_out_dir = build_output_path_tree(page, output_root, page_map)
            # 첨부파일은 attachments/ 폴더에 저장
            attachments_dir = page_out_dir / "attachments"
            result = client.download_attachments(page_id, str(attachments_dir))
            total_downloaded += result["downloaded"]
            total_failed += result["failed"]
        except Exception as e:
            logger.warning("첨부파일 다운로드 실패 (page_id=%s): %s", page_id, e)

    logger.info("첨부파일 다운로드 완료: %d개 성공, %d개 실패", total_downloaded, total_failed)

    # 선택한 포맷으로 변환
    logger.info("==========================================================")
    logger.info("페이지 데이터 변환을 시작합니다...")
    logger.info("==========================================================")

    results = parse_pages(pages, output_root, output_format, target_space_name)

    # 결과 출력
    logger.info("==========================================================")
    logger.info("백업 및 변환이 완료되었습니다!")
    logger.info("메타 데이터: %s", json_path)
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

    if "pdf" in results:
        logger.info(
            "  PDF: %d개 파일 (스킵: %d개)",
            results["pdf"]["pdf_count"],
            results["pdf"]["skipped_count"],
        )

    logger.info("==========================================================")


def tree_view_flow(client: ConfluenceClient):
    """
    트리 구조 조회 흐름을 실행합니다.
    """
    spaces = client.get_spaces()

    if not spaces:
        logger.warning("가져올 수 있는 Space가 없습니다.")
        return

    # Space 선택
    selected_space = select_from_list(spaces, "조회할 Space를 선택해주세요:")
    if not selected_space:
        return

    target_space_id = selected_space["id"]
    target_space_name = selected_space["name"]
    logger.info("선택된 Space: '%s' (ID: %s)", target_space_name, target_space_id)

    # 페이지 데이터 가져오기
    pages = client.get_pages_from_space(space_id=target_space_id)

    if not pages:
        logger.warning("Space에 페이지가 없습니다.")
        return

    # 트리 구조 생성
    tree = build_tree(pages, str(target_space_id), target_space_name)

    # 트리 출력
    print_tree(tree)

    # 통계 출력
    stats = get_tree_stats(tree)
    print(f"\n통계:")
    print(f"   총 페이지: {stats['total_pages']}개")
    print(f"   루트 페이지: {stats['root_pages']}개")
    print(f"   최대 깊이: {stats['max_depth']}단계")

    # JSON 저장 여부 확인
    try:
        save_choice = input("\n트리 구조를 JSON으로 저장할까요? (y/n): ").strip().lower()
        if save_choice == "y":
            # 메타 디렉터리에 저장
            space_safe = safe_filename(target_space_name)
            meta_dir = Path(f"./data/{target_space_id}_{space_safe}/_meta")
            meta_dir.mkdir(parents=True, exist_ok=True)
            output_path = meta_dir / "tree.json"
            save_tree_json(tree, output_path)
    except (KeyboardInterrupt, EOFError):
        pass


def main():
    """
    메인 진입점
    """
    logger.info("Confluence Backup Tool을 시작합니다.")

    try:
        client = ConfluenceClient()
    except Exception as e:
        logger.error("Confluence 클라이언트 초기화 실패: %s", e)
        return

    while True:
        try:
            menu = select_main_menu()

            if menu == 1:
                backup_flow(client)
            elif menu == 2:
                tree_view_flow(client)
            elif menu == 3:
                logger.info("프로그램을 종료합니다.")
                break

        except Exception as e:
            logger.error("작업 중 오류 발생: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
