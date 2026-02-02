# 기술 문서

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
├── logs/                # 로그 파일 디렉터리
└── docs/                # 기술 문서
```

## 출력 디렉터리 구조

디렉터리 구조는 Confluence 페이지의 실제 계층 구조를 반영합니다.

특수문자와 공백은 언더바(`_`)로 치환됩니다.

```
data/{SPACE_ID}_{SPACE_NAME}/
├── _meta/
│   ├── pages.json          # 원본 API 응답 데이터
│   └── tree.json           # 트리 구조 (선택적)
└── pages/
    ├── {ROOT_PAGE_ID}_{TITLE}/
    │   ├── page.html
    │   ├── page.md
    │   ├── page.pdf
    │   ├── meta.json
    │   ├── attachments/
    │   │   └── image.png
    │   └── {CHILD_PAGE_ID}_{TITLE}/      # 자식 페이지 (중첩)
    │       ├── page.html
    │       ├── page.md
    │       ├── page.pdf
    │       ├── meta.json
    │       ├── attachments/
    │       └── {GRANDCHILD_ID}_{TITLE}/  # 손자 페이지
    │           └── ...
    └── {ANOTHER_ROOT_ID}_{TITLE}/
        └── ...
```

### 파일명 규칙

| 파일 | 설명 |
|------|------|
| `page.html` | HTML 변환 결과 |
| `page.md` | Markdown 변환 결과 |
| `page.pdf` | PDF 변환 결과 |
| `meta.json` | 페이지 메타데이터 (원본 API 응답) |
| `attachments/` | 첨부파일 디렉터리 |

### 첨부파일 경로
- 첨부파일은 페이지와 **동일한 디렉터리**에 `attachments/` 폴더로 저장
- HTML/Markdown: 상대 경로 `./attachments/image.png`
- PDF: 절대 경로 `file://.../attachments/image.png`

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
| `ac:structured-macro[code]` | `<pre><code>...</code></pre>` + Pygments 구문 강조 (마크다운: ` ``` `) |
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

## 코드 구문 강조 (Syntax Highlighting)

Pygments 라이브러리를 사용하여 코드 블록에 언어별 구문 강조를 적용합니다.

### 지원 언어 (일부)
| Confluence 언어 | 변환 |
|----------------|------|
| `python`, `py` | Python |
| `javascript`, `js` | JavaScript |
| `typescript`, `ts` | TypeScript |
| `c#` | C# |
| `c++` | C++ |
| `java` | Java |
| `go` | Go |
| `rust` | Rust |
| `bash`, `sh`, `shell` | Bash |
| `sql`, `html`, `css`, `json`, `yaml` | 각각 지원 |

### 출력 예시 (HTML/PDF)
```html
<pre><code class="language-python">
<span style="color: #008000; font-weight: bold">def</span> hello():
    <span style="color: #008000">print</span>(<span style="color: #BA2121">"Hello"</span>)
</code></pre>
```

> 언어가 지정되지 않은 코드 블록은 일반 텍스트로 처리됩니다.

## 이미지 처리

### 지원 이미지 유형
| 유형 | 설명 | 처리 방식 |
|------|------|----------|
| 첨부 이미지 (`ri:attachment`) | Confluence에 업로드된 파일 | 자동 다운로드 후 상대 경로 참조 |
| 외부 URL 이미지 (`ri:url`) | GitHub, 외부 서버 이미지 | URL 그대로 사용 |

### 포맷별 처리
- **HTML**: 상대 경로 (`./{PAGE_ID}_attachments/image.png`) 또는 외부 URL
- **Markdown**: 마크다운 문법 (`![alt](./{PAGE_ID}_attachments/image.png)`)
- **PDF**: 절대 경로로 이미지 임베드 (`file://.../{PAGE_ID}_attachments/image.png`)

### 첨부파일 자동 다운로드
- 페이지의 모든 첨부파일/이미지가 자동으로 다운로드됩니다
- 지원 형식: PNG, JPG, GIF, PDF 등 모든 첨부파일

## CLI 사용법

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
