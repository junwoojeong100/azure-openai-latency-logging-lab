# Azure OpenAI 응답 지연 — 로그 수집 실습

> **EN** — A hands-on lab (Korean) for collecting request-level logs when analyzing Azure OpenAI response latency across the app, the VM, and the Azure OpenAI resource. It builds a fresh lab in your own subscription, applies every setting, and shows how to read the results with KQL.

앱 · VM · Azure OpenAI 세 구간에서 **요청 단위 로그**를 모으는 설정(R1~R8)을 새 리소스 그룹에 직접 적용해 보고, KQL로 지연 구간을 가르는 실습 가이드입니다.

## 바로 보기

**https://junwoojeong100.github.io/azure-openai-latency-logging-lab/** — 한 페이지 실습 가이드 (복사 버튼 · 다크/라이트 · 외부 의존 없음)

`main` 에 push 하면 GitHub Actions(`.github/workflows/pages.yml`)가 [`aoai-logging-hands-on-lab.html`](aoai-logging-hands-on-lab.html) 을 GitHub Pages 에 자동 배포합니다.

## 구성

| 경로 | 내용 |
| --- | --- |
| `snippets/` | 가이드에서 쓰는 코드 R1~R8 (진단 설정 · 메트릭 · 호출 로그 · Application Insights · AMA/DCR · 네트워크 로그 · probe · 알림)과 분석 쿼리 `queries.kql` 28개 |
| `generator/` | 스니펫으로 HTML을 만드는 생성기와 실습용 데모 앱 파일(`vmfiles/`) |
| `generator/run_html.py` | HTML 안의 코드 블록을 문서 순서대로 실행해 가이드가 실제로 동작하는지 확인 (docs-as-tests) |

스니펫 안의 `# >>> slide:이름` / `# <<< slide:이름` 주석은 생성기가 가이드에 발췌할 구간을 표시한 것입니다.

## 사용법

```bash
# 가이드 다시 만들기 (Python 3 표준 라이브러리만 사용) — 생성된 HTML 을 커밋·push 하면 웹에도 반영됩니다
python3 generator/build.py

# 문서 검증 — 실제 Azure 리소스(VM 포함)가 새로 만들어지고 비용이 듭니다 (약 2~3시간, $2 이내 예상)
SUB=<구독 ID> MAIL=<알림 받을 이메일> python3 generator/run_html.py aoai-logging-hands-on-lab.html
```

실습이 끝나면 가이드의 **D · 정리** 단계로 삭제하세요. Connection Monitor · flow log 는 리소스 그룹 밖(NetworkWatcherRG)에 만들어져서 그룹 삭제만으로는 지워지지 않습니다.

## 검증 상태

- 2026-10-23, Korea Central · RHEL 9.8 · gpt-4.1-mini(Global Standard)에서 **2회** 검증했습니다 (단계별 적용 → HTML의 실행 코드 블록 26개를 새 리소스 그룹에서 그대로 재실행). 선택 단계인 Azure Firewall 블록은 따로 실행했고, 분석 쿼리 28개도 실제 워크스페이스에서 오류 없이 실행했습니다.
- **검증하지 못한 것**: Azure Firewall을 거치는 트래픽 경로, 알림 메일의 실제 수신, Private Endpoint 등 환경별 구성, Python 이외의 앱 언어.
- 검증은 리소스 이름 접두사가 다른 사본으로 했습니다. 공개용으로 이름만 중립 값(`lablog`)으로 바꿨고 명령·로직은 같습니다.

## 알아두기

- `contoso-…` 로 시작하는 이름은 예시 자리 표시자입니다. 본인 환경의 이름으로 바꿔 쓰세요.
- 문서 속 "22장 가이드"는 이 실습의 바탕이 된 22장 분량의 로그 수집 슬라이드 가이드(R1~R8)를 가리키며, 이 저장소에는 포함하지 않았습니다.
