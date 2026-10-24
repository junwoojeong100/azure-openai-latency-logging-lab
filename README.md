# Azure OpenAI 응답 지연 — 모니터링 실습 (두 가지 방법)

> **EN** — Two hands-on labs (Korean) for monitoring Azure OpenAI response latency at request level. (1) Keep the app on a VM and add logging around Azure OpenAI. (2) Move the model call into a Microsoft Foundry prompt agent or a Microsoft Agent Framework (MAF) hosted agent, where traces arrive without telemetry code. Both build a fresh lab in your own subscription and were run end to end.

## 가이드 두 개

| | 가이드 | 요약 | 웹 |
| --- | --- | --- | --- |
| 1 | **AOAI + VM 앱 — 로그 수집 (R1~R8)** | 이미 있는 앱을 그대로 두고 진단 설정 · 에이전트 · 앱 코드 · probe · 알림으로 요청 단위 로그를 모읍니다 | [열기](https://junwoojeong100.github.io/azure-openai-latency-logging-lab/) |
| 2 | **Foundry 에이전트 — 같은 모니터링, 훨씬 짧게** | 프롬프트 에이전트 · MAF 호스티드 에이전트로 옮기면 모니터링 설정 코드가 **234줄 → 35줄**, 에이전트 코드 안의 텔레메트리 코드는 **0줄**, 환경은 `azd up` 한 번 | [열기](https://junwoojeong100.github.io/azure-openai-latency-logging-lab/foundry-agents-monitoring-lab.html) |

두 가이드는 서로 링크되어 있습니다. `main` 에 push 하면 GitHub Actions(`.github/workflows/pages.yml`)가 두 HTML 을 GitHub Pages 에 자동 배포합니다.

## 구성

| 경로 | 내용 |
| --- | --- |
| `aoai-logging-hands-on-lab.html` · `foundry-agents-monitoring-lab.html` | 생성된 한 페이지 가이드 (복사 버튼 · 다크/라이트 · 외부 의존 없음) |
| `snippets/` | 가이드 1 의 코드 R1~R8 (진단 설정 · 메트릭 · 호출 로그 · Application Insights · AMA/DCR · 네트워크 로그 · probe · 알림)과 분석 쿼리 `queries.kql` 28개 |
| `foundry/` | 가이드 2 의 azd 프로젝트: `azure.yaml`(Foundry 프로젝트 · 모델 · 프롬프트 에이전트 · 호스티드 에이전트 정의), `src/report-maf-agent/`(MAF 에이전트 코드), `scripts/`(Application Insights 연결 · 알림), `invoke_agents.py`(클라이언트), `queries.kql`(분석 쿼리 11개) |
| `generator/` | 두 HTML 을 만드는 생성기(`build.py` · `build_foundry.py`), 가이드 1 의 데모 앱 파일(`vmfiles/`), 문서 검증 러너(`run_html.py` · `run_foundry_html.py`) |

스니펫 안의 `# >>> slide:이름` / `# <<< slide:이름` 주석은 생성기가 가이드에 발췌할 구간을 표시한 것입니다. 가이드 2 의 줄 수 · 비교표는 빌드할 때 `snippets/` 와 `foundry/` 파일에서 직접 셉니다.

## 사용법

### 가이드 1 — AOAI + VM 앱

```bash
# 가이드 다시 만들기 (Python 3 표준 라이브러리만 사용) — 생성된 HTML 을 커밋·push 하면 웹에도 반영됩니다
python3 generator/build.py

# 문서 검증 — 실제 Azure 리소스(VM 포함)가 새로 만들어지고 비용이 듭니다 (로그 대기 포함 약 40분 · 선택 Firewall·정리 블록 제외 · $2 이내 예상)
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

# 문서 검증 — 실제 Azure 리소스가 새로 만들어지고 비용이 듭니다 (약 20분 · $1 이내 예상)
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

## 알아두기

- `contoso-…` 로 시작하는 이름은 예시 자리 표시자입니다. 본인 환경의 이름으로 바꿔 쓰세요.
- 문서 속 "22장 가이드"는 가이드 1 의 바탕이 된 22장 분량의 로그 수집 슬라이드 가이드(R1~R8)를 가리키며, 이 저장소에는 포함하지 않았습니다.
- 가이드 2 에서 프롬프트 · 응답 **본문이 트레이스에 기록**됩니다 (가이드 1 은 메타데이터만 수집). 접근 제어는 가이드 2 의 부록 C 를 보세요.
