# tree_builder.py

import json
from pathlib import Path

from utils import setup_logging

logger = setup_logging("tree_builder")


def build_tree(pages: list, space_id: str, space_name: str) -> dict:
    """
    플랫한 페이지 리스트를 트리 구조로 변환합니다.

    :param pages: 페이지 데이터 리스트
    :param space_id: Space ID
    :param space_name: Space 이름
    :return: 트리 구조 딕셔너리
    """
    # 페이지 ID -> 페이지 데이터 매핑
    page_map = {}
    for page in pages:
        page_id = page.get("id")
        if page_id:
            page_map[page_id] = {
                "id": page_id,
                "title": page.get("title", ""),
                "parentId": page.get("parentId"),
                "parentType": page.get("parentType", ""),
                "status": page.get("status", ""),
                "createdAt": page.get("createdAt", ""),
                "children": [],
            }

    # 루트 노드들 (parentType이 "space"이거나 parentId가 없는 경우)
    root_nodes = []

    for page_id, node in page_map.items():
        parent_id = node["parentId"]
        parent_type = node["parentType"]

        if parent_type == "space" or parent_id is None:
            # 루트 노드
            root_nodes.append(node)
        elif parent_id in page_map:
            # 부모 노드에 자식으로 추가
            page_map[parent_id]["children"].append(node)
        else:
            # 부모가 없으면 루트로 취급
            root_nodes.append(node)

    # 제목 기준 정렬
    def sort_children(node):
        node["children"].sort(key=lambda x: x["title"])
        for child in node["children"]:
            sort_children(child)

    root_nodes.sort(key=lambda x: x["title"])
    for node in root_nodes:
        sort_children(node)

    return {
        "space_id": space_id,
        "space_name": space_name,
        "total_pages": len(pages),
        "children": root_nodes,
    }


def print_tree(tree: dict, indent: int = 0):
    """
    트리를 CLI에 출력합니다.

    :param tree: 트리 구조 딕셔너리
    :param indent: 들여쓰기 레벨
    """
    if indent == 0:
        # 루트 레벨 출력
        print(f"\n📁 Space: {tree['space_name']} (ID: {tree['space_id']})")
        print(f"   총 {tree['total_pages']}개 페이지")
        print("=" * 60)
        for child in tree["children"]:
            _print_node(child, indent=1)
        print("=" * 60)
    else:
        _print_node(tree, indent)


def _print_node(node: dict, indent: int = 0):
    """
    개별 노드를 출력합니다.
    """
    prefix = "  " * indent
    has_children = len(node["children"]) > 0

    if has_children:
        icon = "📂"
    else:
        icon = "📄"

    print(f"{prefix}{icon} {node['title']} (ID: {node['id']})")

    for child in node["children"]:
        _print_node(child, indent + 1)


def save_tree_json(tree: dict, output_path: Path):
    """
    트리를 JSON 파일로 저장합니다.

    :param tree: 트리 구조 딕셔너리
    :param output_path: 출력 파일 경로
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    logger.info("트리 구조를 저장했습니다. -> %s", output_path)


def get_tree_stats(tree: dict) -> dict:
    """
    트리 통계를 반환합니다.

    :param tree: 트리 구조 딕셔너리
    :return: 통계 딕셔너리
    """
    def count_depth(node: dict, current_depth: int = 0) -> int:
        if not node["children"]:
            return current_depth
        return max(count_depth(child, current_depth + 1) for child in node["children"])

    def count_nodes_by_level(node: dict, level: int, counts: dict):
        counts[level] = counts.get(level, 0) + 1
        for child in node["children"]:
            count_nodes_by_level(child, level + 1, counts)

    max_depth = 0
    level_counts = {}

    for child in tree["children"]:
        depth = count_depth(child, 1)
        if depth > max_depth:
            max_depth = depth
        count_nodes_by_level(child, 1, level_counts)

    root_pages = len(tree["children"])

    return {
        "total_pages": tree["total_pages"],
        "root_pages": root_pages,
        "max_depth": max_depth,
        "pages_by_level": level_counts,
    }
