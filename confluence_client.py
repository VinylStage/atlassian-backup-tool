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
