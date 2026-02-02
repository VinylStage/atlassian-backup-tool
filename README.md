# Atlassian Backup Tool

Confluence Cloud 데이터를 로컬에 백업하는 Python 스크립트입니다.

## 요구 사항

- Python 3.13 이상
- Atlassian Cloud 계정 및 API 토큰

## 설치

1. 저장소 클론:
```bash
git clone https://github.com/your-username/atlassian-backup-tool.git
cd atlassian-backup-tool
```

2. 의존성 설치:

**Poetry 사용 (권장):**
```bash
poetry install
poetry shell
```

**pip 사용:**
```bash
pip install -r requirements.txt
```

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 값을 설정합니다:

```
DOMAIN=yourcompany.atlassian.net
EMAIL=your-email@example.com
API_TOKEN=your-api-token
```

| 변수 | 설명 |
|------|------|
| `DOMAIN` | Confluence Cloud 도메인 (예: `yourcompany.atlassian.net`) |
| `EMAIL` | Atlassian 계정 이메일 |
| `API_TOKEN` | [Atlassian API 토큰](https://id.atlassian.com/manage-profile/security/api-tokens) |

## 사용 방법

### 통합 백업 (권장)

```bash
python main.py
```

실행하면 대화형 프롬프트가 표시됩니다:

```
2025-01-15 10:30:00 - main - INFO - Confluence 백업 작업을 시작합니다.
2025-01-15 10:30:01 - main - INFO - 백업할 Space를 선택해주세요:
  [1] Engineering Wiki (ID: 1572879)
  [2] Product Documentation (ID: 1843726)
  [3] Team Handbook (ID: 2019384)
번호를 입력하세요: 1
2025-01-15 10:30:05 - main - INFO - 선택된 Space: 'Engineering Wiki' (ID: 1572879)
2025-01-15 10:30:05 - main - INFO - 출력 포맷을 선택해주세요:
  [1] HTML (CSS 포함된 문서)
  [2] Markdown (코드 블록 변환 포함)
  [3] HTML + Markdown (둘 다)
번호를 입력하세요: 3
2025-01-15 10:30:08 - main - INFO - 선택된 출력 포맷: both
2025-01-15 10:30:15 - main - INFO - 데이터를 성공적으로 저장했습니다. -> ./data/pages_from_space_1572879.json
2025-01-15 10:30:15 - main - INFO - ==========================================================
2025-01-15 10:30:15 - main - INFO - 페이지 데이터 다운로드 완료. 변환을 시작합니다...
2025-01-15 10:30:20 - main - INFO - ==========================================================
2025-01-15 10:30:20 - main - INFO - 백업 및 변환이 완료되었습니다!
2025-01-15 10:30:20 - main - INFO - 원본 JSON: ./data/pages_from_space_1572879.json
2025-01-15 10:30:20 - main - INFO - 출력 디렉터리: /path/to/data/space_1572879
2025-01-15 10:30:20 - main - INFO -   HTML: 45개 파일, JSON 메타: 50개
2025-01-15 10:30:20 - main - INFO -   Markdown: 45개 파일 (스킵: 5개)
```

### 단독 파싱 (기존 JSON 파일 변환)

이미 다운로드된 JSON 파일을 변환할 때 사용합니다:

```bash
python parser.py <input_json> [output_dir] [format]
```

**예시:**
```bash
# HTML로 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output html

# Markdown으로 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output markdown

# 둘 다 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output both
```

## 프로젝트 구조

```
atlassian-backup-tool/
├── main.py              # 진입점, 대화형 백업 흐름 (다운로드 + 변환 통합)
├── confluence_client.py # Confluence Cloud API 클라이언트 (atlassian-python-api 사용)
├── parser.py            # JSON → HTML/Markdown 변환
├── utils.py             # 로깅 유틸리티
├── pyproject.toml       # Poetry 프로젝트 설정
├── requirements.txt     # Python 의존성 (pip용)
├── .env                 # 환경 설정 (직접 생성 필요)
├── data/                # 백업 데이터 출력 디렉터리
└── logs/                # 로그 파일 디렉터리
```

## 출력 디렉터리 구조

파일명과 폴더명에 ID와 이름이 함께 표시됩니다. 특수문자와 공백은 언더바(`_`)로 치환됩니다.

```
data/
├── pages_from_space_{SPACE_ID}.json              # 원본 API 응답 데이터
└── space_{SPACE_ID}/
    ├── html/                                     # HTML 변환 결과
    │   └── space-{SPACE_ID}_{SPACE_NAME}/
    │       ├── folder-root/                      # 최상위 페이지
    │       │   ├── {PAGE_ID}_{TITLE}.html
    │       │   └── {PAGE_ID}_{TITLE}.json        # 메타데이터
    │       └── folder-{PARENT_ID}_{PARENT_TITLE}/ # 하위 페이지
    │           ├── {PAGE_ID}_{TITLE}.html
    │           └── {PAGE_ID}_{TITLE}.json
    └── markdown/                                 # Markdown 변환 결과
        └── space-{SPACE_ID}_{SPACE_NAME}/
            ├── folder-root/                      # 최상위 페이지
            │   └── {PAGE_ID}_{TITLE}.md
            └── folder-{PARENT_ID}_{PARENT_TITLE}/ # 하위 페이지
                └── {PAGE_ID}_{TITLE}.md
```

**예시:**
```
data/space_1572879/
├── html/
│   └── space-1572879_Engineering_Wiki/
│       ├── folder-root/
│       │   └── 12345_Getting_Started.html
│       └── folder-67890_Setup_Guide/
│           └── 11111_Installation.html
└── markdown/
    └── space-1572879_Engineering_Wiki/
        ├── folder-root/
        │   └── 12345_Getting_Started.md
        └── folder-67890_Setup_Guide/
            └── 11111_Installation.md
```

## 출력 포맷

### HTML
- CSS가 포함된 완성된 HTML 문서
- 메타데이터 (ID, Space, Folder, Status, Created) 표시
- 각 페이지별 JSON 메타데이터 파일 함께 생성

### Markdown
- Confluence 코드 매크로를 마크다운 코드 블록으로 변환
- HTML을 마크다운으로 자동 변환 (html-to-markdown 라이브러리 사용)
- 메타데이터는 HTML 주석으로 포함
