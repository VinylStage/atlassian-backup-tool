# main.py
import json
import os

from confluence_client import ConfluenceClient
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
        logger.info(f"데이터를 성공적으로 저장했습니다. -> {output_path}")
    except (IOError, TypeError) as e:
        logger.error(f"파일 저장 중 오류 발생: {e}")
        raise


def interactive_backup_flow():
    """
    사용자 선택 기반의 대화형 백업 흐름을 관리합니다.
    """
    logger.info("Confluence 백업 작업을 시작합니다.")
    
    try:
        # 1. Confluence 클라이언트 초기화 및 Space 목록 가져오기
        client = ConfluenceClient()
        spaces = client.get_spaces()
        space_details = [{'id': space['id'], 'name': space['name']} for space in spaces]

        if not space_details:
            logger.warning("가져올 수 있는 Space가 없습니다. 작업을 종료합니다.")
            return

        # 2. 사용자에게 Space 목록을 보여주고 선택 받기
        logger.info("백업할 Space를 선택해주세요:")
        for i, space in enumerate(space_details):
            print(f"  [{i + 1}] {space['name']} (ID: {space['id']})")
        
        selected_space = None
        while not selected_space:
            try:
                selection = input("번호를 입력하세요: ")
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(space_details):
                    selected_space = space_details[selected_index]
                else:
                    logger.warning("잘못된 번호입니다. 목록에 있는 번호를 입력해주세요.")
            except ValueError:
                logger.warning("숫자만 입력해야 합니다.")
            except (KeyboardInterrupt, EOFError):
                logger.info("\n작업을 중단합니다.")
                return

        # 3. 선택된 Space의 페이지들 가져오기
        target_space_id = selected_space['id']
        target_space_name = selected_space['name']
        logger.info(f"선택된 Space: '{target_space_name}' (ID: {target_space_id})")
        
        pages = client.get_pages_from_space(space_id=target_space_id)
        
        # 4. 페이지들을 JSON 파일로 저장
        output_filename = f"pages_from_space_{target_space_id}.json"
        output_path = f"./data/{output_filename}"
        save_to_json(pages, output_path)

        # ======================================================================
        # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 가이드 시작 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
        # ======================================================================

        logger.info("==========================================================")
        logger.info("페이지 데이터 다운로드가 완료되었습니다.")
        logger.info(f"이제부터 '{output_path}' 파일을 사용하여 다음 작업을 코딩하시면 됩니다.")
        logger.info("예시: 다운로드된 JSON 파일을 HTML로 변환하기")
        logger.info("1. parser.py가 이 파일을 읽도록 INPUT_PATH를 수정하거나,")
        logger.info(f"2. 아래처럼 커맨드 라인 인자로 파일 경로를 넘겨주도록 parser.py를 수정할 수 있습니다.")
        logger.info(f'   (예: python parser.py {output_path})')
        logger.info("==========================================================")

        # --- 여기에 다음 단계를 구현하세요 ---
        # 예시: subprocess 모듈을 사용하여 parser.py 실행하기
        # import subprocess
        # try:
        #     # parser.py가 커맨드 라인 인자를 받도록 수정했다고 가정
        #     logger.info("parser.py를 실행하여 HTML 변환을 시작합니다...")
        #     # subprocess.run(["python", "parser.py", output_path], check=True)
        # except FileNotFoundError:
        #     logger.error("parser.py를 찾을 수 없습니다.")
        # except Exception as e:
        #     logger.error(f"parser.py 실행 중 오류 발생: {e}")

    except Exception as e:
        logger.error(f"작업 중 심각한 오류 발생: {e}", exc_info=True)
        
    logger.info("Confluence 백업 작업을 종료합니다.")


if __name__ == "__main__":
    interactive_backup_flow()