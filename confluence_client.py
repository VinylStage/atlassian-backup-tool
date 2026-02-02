# confluence_client.py

import requests
from atlassian import Confluence
from dotenv import dotenv_values

from utils import setup_logging

logger = setup_logging("confluence_client")


class ConfluenceClient:
    """
    Confluence Cloud API와 상호작용하기 위한 클라이언트 클래스.
    atlassian-python-api 라이브러리를 사용합니다.
    """

    def __init__(self):
        """
        클라이언트 초기화: .env 파일에서 설정을 로드하고 Confluence 세션을 설정합니다.
        """
        try:
            config = dotenv_values(".env")
            self.domain = config["DOMAIN"]
            self.email = config["EMAIL"]
            self.api_token = config["API_TOKEN"]
        except KeyError as e:
            logger.error(".env 파일에 필요한 설정값이 없습니다: %s", e)
            raise

        self._confluence = self._create_client()

    def _create_client(self) -> Confluence:
        """
        atlassian-python-api Confluence 클라이언트를 생성합니다.
        """
        session = requests.Session()
        return Confluence(
            url=f"https://{self.domain}",
            username=self.email,
            password=self.api_token,
            session=session,
        )

    def get_spaces(self) -> list[dict]:
        """
        Confluence의 모든 Space 정보를 가져옵니다.

        :return: Space 정보가 담긴 리스트 [{"id": ..., "name": ...}, ...]
        """
        logger.info("Fetching all spaces...")
        result = self._confluence.get_all_spaces()
        spaces = [
            {"id": item["id"], "name": item["name"]}
            for item in result.get("results", [])
        ]
        logger.info("Found %d spaces.", len(spaces))
        return spaces

    def get_pages_from_space(self, space_id: int, body_format: str = "storage") -> list:
        """
        특정 Space에 속한 모든 페이지를 가져옵니다.

        :param space_id: 페이지를 가져올 Space의 ID
        :param body_format: 페이지 본문의 포맷 (e.g., "storage", "view")
        :return: 페이지 정보가 담긴 리스트
        """
        logger.info("Fetching pages from space %s...", space_id)
        pages = self._confluence.get_all_pages_by_space_ids_confluence_cloud(
            space_ids=[str(space_id)],
            body_format=body_format,
        )
        logger.info("Found %d pages in space %s.", len(pages), space_id)
        return pages

    def get_attachments(self, page_id: str) -> list:
        """
        페이지의 첨부파일 목록을 가져옵니다.

        :param page_id: 페이지 ID
        :return: 첨부파일 정보 리스트
        """
        result = self._confluence.get_attachments_from_content(page_id)
        return result.get("results", [])

    def download_attachments(self, page_id: str, output_dir: str) -> dict:
        """
        페이지의 모든 첨부파일을 다운로드합니다.

        :param page_id: 페이지 ID
        :param output_dir: 저장할 디렉터리 경로
        :return: {"downloaded": int, "failed": int, "files": list}
        """
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        attachments = self.get_attachments(page_id)
        downloaded = 0
        failed = 0
        files = []

        for att in attachments:
            filename = att.get("title", "")
            download_link = att.get("_links", {}).get("download", "")

            if not filename or not download_link:
                failed += 1
                continue

            try:
                # 다운로드 URL 구성
                download_url = f"https://{self.domain}/wiki{download_link}"

                # 인증 헤더와 함께 다운로드
                response = requests.get(
                    download_url,
                    auth=(self.email, self.api_token),
                    timeout=30,
                )
                response.raise_for_status()

                # 파일 저장
                file_path = output_path / filename
                file_path.write_bytes(response.content)
                files.append(filename)
                downloaded += 1
                logger.info("Downloaded: %s", filename)

            except Exception as e:
                logger.warning("Failed to download %s: %s", filename, e)
                failed += 1

        return {"downloaded": downloaded, "failed": failed, "files": files}
