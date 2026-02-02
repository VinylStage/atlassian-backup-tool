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

### 1. 데이터 다운로드

```bash
python main.py
```

실행하면 백업할 Space를 선택하는 대화형 프롬프트가 표시됩니다. 선택한 Space의 모든 페이지가 `./data/` 디렉터리에 JSON 파일로 저장됩니다.

### 2. HTML 변환

다운로드된 JSON 데이터를 HTML로 변환하려면 `parser.py`의 경로 설정을 수정한 뒤 실행합니다:

```python
# parser.py 상단의 경로 설정 수정
INPUT_PATH = Path("./data/pages_from_space_{SPACE_ID}.json")
OUTPUT_ROOT = Path("./data/space_{SPACE_ID}")
```

```bash
python parser.py
```

각 페이지는 CSS가 포함된 HTML 파일과 메타데이터 JSON 파일로 변환됩니다.

## 프로젝트 구조

```
atlassian-backup-tool/
├── main.py              # 진입점, 대화형 백업 흐름 관리
├── confluence_client.py # Confluence Cloud API 클라이언트
├── parser.py            # JSON → HTML 변환
├── utils.py             # 로깅 유틸리티
├── requirements.txt     # Python 의존성
├── .env                 # 환경 설정 (직접 생성 필요)
├── data/                # 백업 데이터 출력 디렉터리
└── logs/                # 로그 파일 디렉터리
```

## 출력 디렉터리 구조

```
data/
├── pages_from_space_{SPACE_ID}.json  # 다운로드된 원본 데이터
└── space_{SPACE_ID}/
    └── space-{SPACE_ID}/
        ├── folder-root/              # 최상위 페이지
        │   ├── {PAGE_ID}.html
        │   └── {PAGE_ID}.json
        └── folder-{PARENT_ID}/       # 하위 페이지 (부모 ID별 그룹)
            ├── {PAGE_ID}.html
            └── {PAGE_ID}.json
```
