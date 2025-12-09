# # main.py
# import json

# import requests
# from requests.auth import HTTPBasicAuth
# from dotenv import dotenv_values


# # def hello():
# #     print("hello world")


# # if __name__ == "__main__":
# #     hello()

# config = dotenv_values(".env")
# # print(config)
# ID = 184287513
# TYPE = "pages"
# url = f"https://{config['DOMAIN']}/wiki/api/v2/{TYPE}"

# auth = HTTPBasicAuth(config["EMAIL"], config["API_TOKEN"])

# headers = {"Accept": "application/json"}

# # params = {"include-direct-children": "true"}

# params = {
#     "space-id":"589866",
#     "body-format":"storage"
# }

# response = requests.request(
#     "GET", url, headers=headers, auth=auth, params=params, timeout=1000
# )

# print(
#     json.dumps(
#         json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")
#     )
# )

# main.py
import json
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values


config = dotenv_values(".env")

DOMAIN = config["DOMAIN"]
EMAIL = config["EMAIL"]
API_TOKEN = config["API_TOKEN"]

TYPE = "pages"
BASE_URL = f"https://{DOMAIN}/wiki"
FIRST_URL = f"{BASE_URL}/api/v2/{TYPE}"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

params = {
    "space-id": "589866",
    "body-format": "storage",
}

all_results = []

url = FIRST_URL
first = True

while True:
    # 첫 요청만 params 사용, 이후에는 next URL에 이미 쿼리가 포함됨
    req_params = params if first else None

    resp = requests.get(
        url,
        headers=headers,
        auth=auth,
        params=req_params,
        timeout=1000,
    )
    resp.raise_for_status()

    data = resp.json()

    # 이번 페이지 결과 추가
    all_results.extend(data.get("results", []))

    links = data.get("_links", {})
    next_path = links.get("next")
    base_from_api = links.get("base", BASE_URL)

    if not next_path:
        # 더 이상 next 없으면 종료
        break

    # base + next 를 안전하게 붙이기 (urljoin 사용)
    url = urljoin(base_from_api, next_path)
    first = False

# 최종 결과 출력 (원하면 전체를 아니면 필요한 정보만)
# print(json.dumps(all_results, sort_keys=True, indent=4, separators=(",", ": ")))
# print(f"총 {len(all_results)} 개 페이지 수집 완료")

with open("confluence_pages_backup.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=4, ensure_ascii=False)

print("총", len(all_results), "개의 페이지 백업 완료")