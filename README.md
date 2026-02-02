# Atlassian Backup Tool

Confluence Cloud 데이터를 로컬에 백업하는 Python 스크립트입니다.

## 주요 기능

- Confluence Space의 모든 페이지 백업
- 첨부파일 및 이미지 자동 다운로드
- HTML, Markdown, PDF 포맷 변환
- Confluence 매크로 자동 변환 (코드 블록, expand, tip, info 등)
- 페이지 계층 구조 트리 뷰

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

```bash
python main.py
```

실행하면 메인 메뉴가 표시됩니다:

```
============================================================
  Confluence Backup Tool
============================================================
  [1] 백업 및 변환
  [2] 트리 구조 조회
  [3] 종료
============================================================
```

### 1. 백업 및 변환

Space를 선택하고 원하는 출력 포맷으로 변환합니다:

```
백업할 Space를 선택해주세요:
  [1] Engineering Wiki (ID: 1572879)
  [2] Product Documentation (ID: 1843726)
번호를 입력하세요: 1

출력 포맷을 선택해주세요:
  [1] HTML (CSS 포함된 문서)
  [2] Markdown (코드 블록 변환 포함)
  [3] HTML + Markdown
  [4] PDF (인쇄용 문서)
  [5] 전체 (HTML + Markdown + PDF)
번호를 입력하세요: 5
```

**백업 프로세스:**
1. 페이지 데이터 다운로드 (JSON)
2. 첨부파일/이미지 자동 다운로드
3. 선택한 포맷으로 변환

### 2. 트리 구조 조회

Space의 페이지 계층 구조를 트리 형태로 확인합니다:

```
📁 Space: Engineering Wiki (ID: 1572879)
   총 50개 페이지
============================================================
  📂 Getting Started (ID: 12345)
    📄 Installation (ID: 67890)
    📄 Configuration (ID: 67891)
  📂 API Reference (ID: 12346)
    📄 Authentication (ID: 67892)
============================================================

📊 통계:
   총 페이지: 50개
   루트 페이지: 5개
   최대 깊이: 3단계

트리 구조를 JSON으로 저장할까요? (y/n):
```

### 단독 파싱 (CLI)

이미 다운로드된 JSON 파일을 변환할 때 사용합니다:

```bash
python parser.py <input_json> [output_dir] [format] [space_name]
```

**예시:**
```bash
# HTML로 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output html

# PDF로 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output pdf

# 전체 포맷으로 변환
python parser.py ./data/pages_from_space_1572879.json ./data/output all
```

## 프로젝트 구조

```
atlassian-backup-tool/
├── main.py              # 진입점, 메인 메뉴 및 대화형 흐름
├── confluence_client.py # Confluence Cloud API 클라이언트 (첨부파일 다운로드 포함)
├── parser.py            # JSON → HTML/Markdown/PDF 변환, 매크로 처리
├── tree_builder.py      # 트리 구조 생성 및 출력
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
├── tree_{SPACE_ID}.json                          # 트리 구조 (선택적)
└── space_{SPACE_ID}/
    ├── attachments/                              # 다운로드된 첨부파일/이미지
    │   └── {PAGE_ID}/
    │       ├── image1.png
    │       ├── document.pdf
    │       └── ...
    ├── html/                                     # HTML 변환 결과
    │   └── space-{SPACE_ID}_{SPACE_NAME}/
    │       ├── folder-root/
    │       │   ├── {PAGE_ID}_{TITLE}.html
    │       │   └── {PAGE_ID}_{TITLE}.json
    │       └── folder-{PARENT_ID}_{PARENT_TITLE}/
    │           ├── {PAGE_ID}_{TITLE}.html
    │           └── {PAGE_ID}_{TITLE}.json
    ├── markdown/                                 # Markdown 변환 결과
    │   └── space-{SPACE_ID}_{SPACE_NAME}/
    │       ├── folder-root/
    │       │   └── {PAGE_ID}_{TITLE}.md
    │       └── folder-{PARENT_ID}_{PARENT_TITLE}/
    │           └── {PAGE_ID}_{TITLE}.md
    └── pdf/                                      # PDF 변환 결과
        └── space-{SPACE_ID}_{SPACE_NAME}/
            ├── folder-root/
            │   └── {PAGE_ID}_{TITLE}.pdf
            └── folder-{PARENT_ID}_{PARENT_TITLE}/
                └── {PAGE_ID}_{TITLE}.pdf
```

## 출력 포맷

### HTML
- CSS가 포함된 완성된 HTML 문서
- 메타데이터 표시: `ID`, `Space (이름)`, `Parent (이름)`, `Status`, `Created`
- 이미지 및 첨부파일 상대 경로 링크
- 각 페이지별 JSON 메타데이터 파일 함께 생성

### Markdown
- Confluence 코드 매크로를 마크다운 코드 블록으로 변환 (코드 내용 이스케이프 없음)
- HTML을 마크다운으로 자동 변환 (html-to-markdown 라이브러리 사용)
- 이미지를 마크다운 문법으로 변환 (`![alt](url)`)
- 메타데이터는 HTML 주석으로 포함:
  ```
  <!-- id: 12345 | space: 1572879 (Engineering Wiki) | parent: 67890 (Getting Started) | status: current -->
  ```

### PDF
- A4 사이즈 최적화 (margin: 5mm, 최소 여백)
- WeasyPrint 사용
- 테이블 자동 맞춤 (`table-layout: fixed`)
- 이미지 자동 임베드
- 한글 폰트 호환성 (fontTools 패치 적용)

## Confluence 매크로 변환

다음 Confluence 매크로들이 자동으로 HTML 태그로 변환됩니다:

| Confluence 매크로 | 변환 결과 |
|------------------|----------|
| `ac:structured-macro[code]` | `<pre><code>...</code></pre>` (마크다운: ` ``` `) |
| `ac:structured-macro[expand]` | `<details><summary>제목</summary>내용</details>` |
| `ac:structured-macro[tip]` | `<div class="callout callout-tip">...</div>` |
| `ac:structured-macro[info]` | `<div class="callout callout-info">...</div>` |
| `ac:structured-macro[note]` | `<div class="callout callout-note">...</div>` |
| `ac:structured-macro[warning]` | `<div class="callout callout-warning">...</div>` |
| `ac:structured-macro[panel]` | `<div class="callout callout-panel">...</div>` |
| `ac:structured-macro[view-file]` | `<a href="...">📎 파일명</a>` |
| `ac:structured-macro[toc]` | 제거 (로컬에서 불필요) |
| `ac:image` + `ri:attachment` | `<img src="./attachments/...">` (첨부 이미지) |
| `ac:image` + `ri:url` | `<img src="https://...">` (외부 URL 이미지) |

## 이미지 처리

### 지원 이미지 유형
| 유형 | 설명 | 처리 방식 |
|------|------|----------|
| 첨부 이미지 (`ri:attachment`) | Confluence에 업로드된 파일 | 자동 다운로드 후 상대 경로 참조 |
| 외부 URL 이미지 (`ri:url`) | GitHub, 외부 서버 이미지 | URL 그대로 사용 |

### 포맷별 처리
- **HTML**: 상대 경로 (`../../../attachments/{PAGE_ID}/image.png`) 또는 외부 URL
- **Markdown**: 마크다운 문법 (`![alt](url)`)
- **PDF**: 절대 경로로 이미지 임베드 (`file://...`)

### 첨부파일 자동 다운로드
- 페이지의 모든 첨부파일/이미지가 자동으로 다운로드됩니다
- 지원 형식: PNG, JPG, GIF, PDF 등 모든 첨부파일

## 라이선스

MIT License
