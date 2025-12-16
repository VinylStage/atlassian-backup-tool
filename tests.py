# tests.py

import json

from atlassian import Confluence
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")


def init_session():
    domain = config["DOMAIN"]
    session = requests.Session()
    cfl = Confluence(
        url=f"https://{domain}",
        username=config["EMAIL"],
        password=config["API_TOKEN"],
        session=session,
    )
    return cfl


def get_space_info(cfl):
    result = {}
    status = cfl.get_all_spaces()
    for item in status["results"]:
        result[item["id"]] = item["name"]
    return result


def get_id_by_name(name, mapping):
    # name -> id 검색 (전체를 다 돈다)
    for _id, _name in mapping.items():
        if _name == name:
            return _id
    # 못 찾으면 None
    return None


def get_all_pages_by_space_id(space_info, cfl, space_name):
    space_id = get_id_by_name(space_name, space_info)

    if space_id is None:
        raise ValueError(f"'{space_name}' 에 해당하는 space가 없습니다.")

    space_ids = [str(space_id)]

    res = cfl.get_all_pages_by_space_ids_confluence_cloud(
        space_ids=space_ids,
        body_format="storage",
    )
    return res


if __name__ == "__main__":
    cfl = init_session()
    space_info = get_space_info(cfl)
    print(space_info)
    print("=" * 50)

    print("받고싶은 이름 입력")
    space_name = input().strip()

    res_data = get_all_pages_by_space_id(space_info, cfl, space_name)

    with open(f"./data/{space_name}.json", "w", encoding="utf-8") as f:
        json.dump(res_data, f, ensure_ascii=False, indent=4)

    print(f"{space_name}.json 으로 저장 완료")
