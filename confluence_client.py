# confluence_client.py

from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values
from utils import setup_logging

logger = setup_logging("confluence_client")


class ConfluenceClient:
    """
    Confluence Cloud API와 상호작용하기 위한 클라이언트 클래스.
    """

    def __init__(self):
        """
        클라이언트 초기화: .env 파일에서 설정을 로드하고 API 세션을 설정합니다.
        """
        try:
            config = dotenv_values(".env")
            self.domain = config["DOMAIN"]
            self.email = config["EMAIL"]
            self.api_token = config["API_TOKEN"]
        except KeyError as e:
            logger.error(".env 파일에 필요한 설정값이 없습니다: %s", e)
            raise

        self.base_url = f"https://{self.domain}/wiki"
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        인증 정보와 공통 헤더를 포함한 requests.Session 객체를 생성합니다.
        """
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.email, self.api_token)
        session.headers.update({"Accept": "application/json"})
        return session

    def _fetch_all_resources(self, resource_type: str, params: dict | None = None) -> list:
        """
        Confluence API v2에서 특정 리소스를 페이지네이션을 통해 모두 가져옵니다.

        :param resource_type: "spaces", "pages" 등 리소스 종류
        :param params: 첫 API 요청에 사용할 쿼리 파라미터
        :return: 모든 결과가 담긴 리스트
        """
        all_results = []
        url = f"{self.base_url}/api/v2/{resource_type}"
        first_request = True

        while url:
            try:
                # 첫 요청에만 파라미터 사용, 이후에는 next URL에 포함된 쿼리 사용
                current_params = params if first_request else None
                resp = self._session.get(url, params=current_params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                all_results.extend(data.get("results", []))

                links = data.get("_links", {})
                next_path = links.get("next")

                if not next_path:
                    break

                # next_path가 전체 URL이 아닌 path만 오는 경우를 대비해 urljoin 사용
                base_from_api = links.get("base", self.base_url)
                url = urljoin(base_from_api, next_path)
                first_request = False

            except requests.RequestException as e:
                logger.error("API 요청 중 에러 발생: %s", e)
                raise

        return all_results

    def get_spaces(self, space_ids: list[int] | None = None) -> list:
        """
        Confluence의 모든 또는 특정 Space 정보를 가져옵니다.

        :param space_ids: 정보를 가져올 space의 id 리스트
        :return: Space 정보가 담긴 리스트
        """
        params = {"id": space_ids} if space_ids else None
        logger.info(f"Fetching spaces... IDs: {space_ids or 'All'}")
        spaces = self._fetch_all_resources("spaces", params=params)
        logger.info(f"Found {len(spaces)} spaces.")
        return spaces

    def get_space_ids(self) -> list[int]:
        """
        모든 Space의 ID만 가져옵니다.
        """
        spaces = self.get_spaces()
        space_ids = [space['id'] for space in spaces]
        logger.info(f"Extracted {len(space_ids)} space IDs.")
        return space_ids

    def get_pages_from_space(self, space_id: int, body_format: str = "storage") -> list:
        """
        특정 Space에 속한 모든 페이지를 가져옵니다.

        :param space_id: 페이지를 가져올 Space의 ID
        :param body_format: 페이지 본문의 포맷 (e.g., "storage", "view")
        :return: 페이지 정보가 담긴 리스트
        """
        params = {"space-id": space_id, "body-format": body_format}
        logger.info(f"Fetching pages from space {space_id}...")
        pages = self._fetch_all_resources("pages", params=params)
        logger.info(f"Found {len(pages)} pages in space {space_id}.")
        return pages
