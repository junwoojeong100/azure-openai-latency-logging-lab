# Azure OpenAI 응답 지연 — 모니터링 실습 (두 가지 방법)

> **EN** — Two hands-on labs (Korean) for monitoring Azure OpenAI response latency at request level. (1) Keep the app on a VM and add logging around Azure OpenAI. (2) Move the model call into a Microsoft Foundry prompt agent or a Microsoft Agent Framework (MAF) hosted agent, where traces arrive without telemetry code. Both build a fresh lab in your own subscription and were run end to end.

## 가이드 두 개

| | 가이드 | 요약 | 웹 |
| --- | --- | --- | --- |
| 1 | **AOAI + VM 앱 — 로그 수집 (R1~R8)** | 이미 있는 앱을 그대로 두고 진단 설정 · 에이전트 · 앱 코드 · probe · 알림으로 요청 단위 로그를 모읍니다 | [열기](https://junwoojeong100.github.io/azure-openai-latency-logging-lab/) |
| 2 | **Foundry 에이전트 — 같은 모니터링, 훨씬 짧게** | 프롬프트 에이전트 · MAF 호스티드 에이전트로 옮기면 서버 쪽 모니터링 설정 코드가 **234줄 → 35줄**, 에이전트 코드 안의 텔레메트리 코드는 **0줄**, 환경은 `azd up` 한 번. 단 **앱 ↔ 에이전트 구간은 앱이 따로 기록**해야 합니다 | [열기](https://junwoojeong100.github.io/azure-openai-latency-logging-lab/foundry-agents-monitoring-lab.html) |

두 가이드는 서로 링크되어 있습니다. `main` 에 push 하면 GitHub Actions(`.github/workflows/pages.yml`)가 두 HTML 을 GitHub Pages 에 자동 배포합니다.

### 처음 보는 분을 위한 구성

두 가이드는 Azure 모니터링을 처음 접하는 개발 담당자가 **이 문서만 보고 끝까지 따라갈 수 있도록** 쓰였습니다.

- **먼저 읽는 부분** — 이 가이드가 하는 일(문제 · 전체 그림), 용어 사전, 읽는 법, 준비물 · 안전 수칙, 전체 단계 표
- **단계마다 같은 모양** — ‘한눈에’(무엇을 · 왜 · 끝나면 · 내 환경에서는) → 코드 → 예상 결과와 **읽는 법**
- **모든 스크립트 · 소스코드를 구간(번호)으로 나눠, 구간 바로 아래에 무슨 일을 하는지 · 왜 하는지 · 옵션의 뜻**을 설명합니다. 코드 위의 ‘전체 복사’ 버튼은 구간을 이어 붙인 **스크립트 전체**를 복사합니다.
- 단계 이름표로 **‘실습 환경 준비’**(실습에만 필요)와 **‘내 환경에도 그대로 적용’**(운영 환경에 쓰는 설정)을 구분합니다.
- 왼쪽 목차에 진행 체크(브라우저에만 저장)와 ‘코드 해설 숨기기’ · ‘접이식 모두 펼치기’ 도구가 있습니다.

## 구성

| 경로 | 내용 |
| --- | --- |
| `aoai-logging-hands-on-lab.html` · `foundry-agents-monitoring-lab.html` | 생성된 한 페이지 가이드 (복사 버튼 · 다크/라이트 · 외부 의존 없음) |
| `snippets/` | 가이드 1 의 코드 R1~R8 (진단 설정 · 메트릭 · 호출 로그 · Application Insights · AMA/DCR · 네트워크 로그 · probe · 알림)과 분석 쿼리 `queries.kql` 28개 |
| `foundry/` | 가이드 2 의 azd 프로젝트: `azure.yaml`(Foundry 프로젝트 · 모델 · 프롬프트 에이전트 · 호스티드 에이전트 정의), `src/report-maf-agent/`(MAF 에이전트 코드), `scripts/`(Application Insights 연결 · 알림), `invoke_agents.py`(클라이언트), `queries.kql`(분석 쿼리 11개) |
| `generator/` | 두 HTML 을 만드는 생성기(`build.py` · `build_foundry.py`), 공용 부품(`lib.py` 간단 마크다운 · 코드 해설 · 단계 상자, `common.py` 목차 · 읽는 법 · 용어 사전, `template.py` CSS · JS), 단계별 내용(가이드 1: `part_a.py` · `part_b.py` · `part_b2.py` · `part_c.py`, 가이드 2: `foundry_a.py` · `foundry_b.py` · `foundry_c.py` · `foundry_app.py`), 가이드 1 의 데모 앱 파일(`vmfiles/`), 실측 출력(`foundry_expected/`), 정적 점검(`check_html.py`), 문서 검증 러너(`run_html.py` · `run_foundry_html.py`) |

스니펫 안의 `# >>> slide:이름` / `# <<< slide:이름` 주석은 생성기가 가이드에 발췌할 구간을 표시한 것입니다. 가이드 2 의 줄 수 · 비교표는 빌드할 때 `snippets/` 와 `foundry/` 파일에서 직접 셉니다.

## 사용법

### 가이드 1 — AOAI + VM 앱

```bash
# 가이드 다시 만들기 (Python 3 표준 라이브러리만 사용) — 생성된 HTML 을 커밋·push 하면 웹에도 반영됩니다
python3 generator/build.py

# 생성된 HTML 정적 점검 (Azure 불필요): 앵커 링크 · id 중복 · 코드 해설 구간/해설 수 · 실행 블록 이음 · 테마 변수 · 본문 찌꺼기
python3 generator/check_html.py

# 문서 검증 — 실제 Azure 리소스(VM 포함)가 새로 만들어지고 비용이 듭니다 (로그 대기 포함 약 40분 · 선택 Firewall·정리 블록 제외 · $2 안팎 예상 · 요금제에 따라 다름)
SUB=<구독 ID> MAIL=<알림 받을 이메일> python3 generator/run_html.py aoai-logging-hands-on-lab.html
```

실습이 끝나면 가이드의 **D · 정리** 단계로 삭제하세요. Connection Monitor · flow log 는 리소스 그룹 밖(NetworkWatcherRG)에 만들어져서 그룹 삭제만으로는 지워지지 않습니다.

### 가이드 2 — Foundry 에이전트

```bash
# 환경 만들기: Foundry 프로젝트 + 모델 + Application Insights 연결 + 에이전트 2개 (azd 1.37.1+ · microsoft.foundry 확장 필요)
cd foundry
azd env new <환경 이름> --subscription <구독 ID> --location koreacentral
azd up

# 가이드 다시 만들기
python3 generator/build_foundry.py

# 문서 검증 — 실제 Azure 리소스가 새로 만들어지고 비용이 듭니다 (약 20분 · $1 안팎 예상 · 요금제에 따라 다름)
SUB=<구독 ID> MAIL=<알림 받을 이메일> python3 generator/run_foundry_html.py foundry-agents-monitoring-lab.html
```

실습이 끝나면 `azd down --force --purge` 로 전부 삭제하세요.

## 검증 상태

### 가이드 1

- 2026-10-23, Korea Central · RHEL 9.8 · gpt-4.1-mini(Global Standard)에서 **2회** 검증했습니다 (단계별 적용 → HTML의 실행 코드 블록 26개를 새 리소스 그룹에서 그대로 재실행). 선택 단계인 Azure Firewall 블록은 따로 실행했고, 분석 쿼리 28개도 실제 워크스페이스에서 오류 없이 실행했습니다.
- **검증하지 못한 것**: Azure Firewall을 거치는 트래픽 경로, 알림 메일의 실제 수신, Private Endpoint 등 환경별 구성, Python 이외의 앱 언어.
- 검증은 리소스 이름 접두사가 다른 사본으로 했습니다. 공개용으로 이름만 중립 값(`lablog`)으로 바꿨고 명령·로직은 같습니다.

### 가이드 2

- 2026-10-24, Korea Central · gpt-5.4-mini · azd 1.37.1 · azure.ai.agents 1.0.0-beta.22 · Azure CLI 2.86 에서 검증했습니다. 단계별로 한 번 실행한 뒤, **HTML 의 실행 코드 블록 23개(15 단계)를 새 환경에서 그대로 재실행**해 전부 오류 없이 통과했습니다(자동 실행 약 17분). 분석 쿼리 11개도 실제 Application Insights 에서 실행했습니다.
- **확인한 것**: `azd up` 한 번(약 3분 40초)으로 환경 완성 · 연결만으로 두 에이전트의 서버 쪽 트레이스 자동 수집 · 클라이언트 `traceparent` 가 서버 기록의 `operation_Id` 로 이어짐 · 호스티드 에이전트의 cold start 4단계 분해 · 실패한 실행의 가시성(`requests` 는 success 로 남음) · 지연/실패 알림 2개 발화 · 입출력 본문이 트레이스에 기록됨 (가이드 부록 A).
- **검증하지 못한 것**: Foundry 포털 화면(Traces · Monitor · Operate), 알림 메일의 실제 수신, 로컬 실행(`azd ai agent run`), 네트워크 격리(private endpoint) 프로젝트, 호스티드 에이전트 컴퓨트 과금의 실제 금액, 장기 운영(샘플링 · 보존).
- azd 의 Foundry 확장은 **베타**(1.0.0-beta.x)라 명령 · 스키마가 바뀔 수 있습니다. 새 환경 3번 중 1번은 첫 `azd up` 이 일시적 오류로 실패했고 재실행으로 성공했습니다.

### 이번 개정(2026-10-25)에서 다시 확인한 것 · 하지 않은 것

- **실행 코드는 사실상 그대로입니다.** 두 가이드의 실행 코드 블록(가이드 1 · 29개, 가이드 2 · 24개)을 개정 전과 단계별로 비교했습니다(코드를 해설용 구간으로 나눠서 러너가 구간을 이어 붙입니다 — `data-part`). 주석 줄을 뺀 코드가 달라진 것은 **가이드 1 의 정리(D) 블록 하나**뿐이고, 가이드 2 는 달라진 것이 없습니다(`foundry/azure.yaml` 의 주석 한 줄만 고쳤습니다).
  - **주석만 고친 곳**(가이드 1 의 A1 · B3 · B4, `snippets/R7_aoai-probe.env.sample`): 이 문서 밖의 슬라이드 번호를 가리키던 주석(‘22장’, ‘R4 ①’ 등)을 중립적인 문장으로 바꿨습니다.
  - **정리(D) 블록**(자동 재실행에서 건너뛰는 블록): (A) 중지와 (B) 삭제를 두 블록으로 나누고, (B) 에는 리소스 그룹의 `purpose=aoai-logging-lab` 태그 확인과, **리소스 그룹 밖의 Connection Monitor · flow log 는 이 실습의 VM · VNet 을 가리킬 때만** 지우는 확인을 넣었습니다. 이 분기는 `az` 를 흉내 낸 래퍼로 4가지 경우(실습 그룹 · 남의 Network Watcher 리소스 · 없음 · 태그 불일치)를 모의 실행했고, `show | grep` 로 소유를 판별하는 방식은 임시로 만든 실제 Connection Monitor · flow log 로 확인한 뒤 지웠습니다. 새 코드로 실제 삭제를 실행하지는 않았습니다.
- **분석 쿼리 2개를 고쳤습니다**(`snippets/queries.kql`): `app_after_idle` 은 직전 호출이 없는 첫 행이 ‘5분 초과 유휴’로 잘못 분류되던 것을 제외하고, `app_dependencies_aoai` 는 샘플링을 되돌려도 건수가 맞도록 `sum(ItemCount)` 로 바꿨습니다. 둘 다 실습 워크스페이스에서 실행해 확인했습니다.
- **개정한 것은 대부분 설명입니다.**
  - 두 가이드 공통: 구간별 코드 해설, 용어 사전, 단계별 ‘한눈에’ 상자, 예상 결과 읽는 법, 코드 구간 이름표(‘실습 전용’ · ‘내 환경에도’), 터미널 사용 규칙.
  - 가이드 1: R3 · R4 비교표와 ID 5종 표(B3), 부록 B ‘내 환경에 적용하기’(변수표 · 단계별 표 · `lablog.env` 예시 · R3 필드 표), 부록 E 의 쿼리 전문, B2 사전 확인 표, B7 시작 전 확인, C2 의 ‘평소 gap’ 기준선 쿼리, C3 의 ‘시각의 분’ 쿼리 2개, C4 의 Connection Monitor 쿼리. 이 **쿼리들의 예시 출력은 실습 워크스페이스에서 실제로 실행한 결과**입니다.
  - 가이드 2: 시작 부분의 ‘핵심 결과’ · ‘가이드 1 을 읽지 않은 분께’, C1 의 ‘어떤 기록이 어디에 남는지’ 표, B3 의 변경점 5가지 · 작업 순서 · 전환 후보 체크리스트, C7 의 ‘앱 최소 기록’ 스케치(**가짜 클라이언트로 구문과 흐름만 점검했고 실제 Foundry 호출로는 실행하지 않았습니다**)와 읽는 법, E1 의 판단 기준 4가지, C1 의 수집 지연 직접 재 보기 쿼리(실행해 확인). B3 · C7 의 표는 2026-10-24 추가 시험(`generator/foundry_expected/` 의 `E1` · `P1` · `E2*` · `E3`)에서 읽어 옵니다.
- **화면 출력 점검(같은 날 추가)**: 옵션 목록(`<dl>`)이 긴 코드 항목 때문에 설명 열이 260px 미만으로 좁아진 곳이 두 가이드에 모두 46곳(가이드 1 · 30곳, 가이드 2 · 16곳)이었고, 그중 일부는 너비 0 이 되어 글자가 한 줄에 한 자씩 세로로 깨졌습니다(예: 가이드 2 B2 의 5번 ‘에이전트를 대상으로 하는 클라이언트 만들기’). 항목 이름 열의 폭을 제한하고, 아주 긴 항목은 설명 위에 한 줄로 쌓도록 고쳤습니다. 함께 고친 것: 긴 코드 줄이 말없이 잘려 보이던 것(가로 스크롤 막대 · 오른쪽 그림자 표시 추가), 좁은 화면(720px 이하)에서 표가 답답하던 것(항목별 카드로 표시), 한글이 섞여 열이 어긋나던 예상 출력 한 곳(가이드 1 의 C3 — 값은 그대로 두고 빈 칸 표시를 `(없음)` → `-` 로, 열 간격만 영문 기준으로 맞춤), 코드 글꼴 목록(Courier New 우선 → 시스템 고정폭 글꼴 우선). 확인은 Playwright 로 폭 1280 · 820 · 390px 에서 두 페이지를 점검했고(페이지 가로 넘침 · 찌그러진 열 · 글자가 세로로 깨진 곳 모두 0), 어두운 테마는 일부 화면만 눈으로 확인했습니다. 실제 모바일 기기와 Safari · Firefox 는 확인하지 않았습니다.
- **검토에서 실제로 재현해 고친 사실 오류**: `az account show --query "{구독:name,…}"` 처럼 한글 키를 따옴표 없이 쓰면 JMESPath 오류가 난다 · 가이드 2 의 `kq` 가 기본으로 **최근 1시간만** 조회한다(`az monitor app-insights query` 의 기본값 — 오래된 호출은 `--offset` 필요) · Connection Monitor · flow log 이름이 고정이라 남의 리소스를 지울 수 있었다 · `azure-monitor-opentelemetry` 의 Python 요구 버전 표기 등.
- **개정 후 전체 실습(새 리소스 그룹에서 처음부터)은 다시 돌리지 않았습니다.** 실행 코드가 같으므로 이전 검증(위 두 절)이 그대로 유효하지만, 해설 문장은 사람의 검토 대상입니다. 해설은 AI 검토 에이전트(정확성 2 · 초보자 가독성 2)가 **두 번에 걸쳐** 교차 검토해 지적을 반영했으며, 사람의 검토를 대신하지는 않습니다. 새로 넣은 일부 확인용 명령(`timedatectl` 확인, 스냅샷 열어 보기, 관리 ID 로 인증하는 코드 예시)과 포털 메뉴 경로는 이번에 다시 실행해 보지 않았거나 문서 기준입니다.

## 알아두기

- `contoso-…` 로 시작하는 이름은 예시 자리 표시자입니다. 본인 환경의 이름으로 바꿔 쓰세요.
- 문서 속 **R1~R8** 은 로그 수집 항목의 번호(R1 AOAI 진단 설정 · R2 메트릭 · R3 앱 호출 로그 · R4 Application Insights · R5 모니터링 에이전트 · R6 네트워크 · R7 probe · R8 알림)이며, 가이드 안의 용어 사전에도 있습니다.
- 가이드 2 에서 프롬프트 · 응답 **본문이 트레이스에 기록**됩니다 (가이드 1 은 메타데이터만 수집). 접근 제어는 가이드 2 의 부록 C 를 보세요.
- 가이드 2 의 `kq` 함수는 기본으로 **최근 1시간**만 조회합니다. 호출한 지 오래되었다면 가이드 2 의 A3 해설대로 `--offset 3d` 를 추가하세요.
