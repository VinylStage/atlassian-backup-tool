# Atlassian Backup Tool

Confluence Cloud 데이터를 로컬에 백업하는 Python 스크립트입니다.

## 주요 기능

- Confluence Space의 모든 페이지 백업
- 첨부파일 및 이미지 자동 다운로드
- HTML, Markdown, PDF 포맷 변환
- 코드 블록 구문 강조 (Pygments)
- Confluence 매크로 자동 변환
- 페이지 계층 구조 트리 뷰

## 요구 사항

- Python 3.13 이상
- Atlassian Cloud 계정 및 API 토큰

## 설치

```bash
git clone https://github.com/your-username/atlassian-backup-tool.git
cd atlassian-backup-tool
poetry install
```

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```
DOMAIN=yourcompany.atlassian.net
EMAIL=your-email@example.com
API_TOKEN=your-api-token
```

API 토큰은 [Atlassian API 토큰 관리](https://id.atlassian.com/manage-profile/security/api-tokens)에서 생성할 수 있습니다.

## 빠른 시작

```bash
poetry shell
python main.py
```

### 메인 메뉴

```
============================================================
  Confluence Backup Tool
============================================================
  [1] 백업 및 변환
  [2] 트리 구조 조회
  [3] 종료
============================================================
```

### 백업 및 변환

1. Space 선택
2. 출력 포맷 선택:
   - `[1]` HTML
   - `[2]` Markdown
   - `[3]` HTML + Markdown
   - `[4]` PDF
   - `[5]` 전체

백업 결과는 `data/{SPACE_ID}_{SPACE_NAME}/` 디렉터리에 저장됩니다.

### 트리 구조 조회

Space의 페이지 계층 구조를 트리 형태로 확인합니다.

## 문서

상세 기술 문서는 [docs/technical.md](docs/technical.md)를 참조하세요.

## 라이선스

MIT License
