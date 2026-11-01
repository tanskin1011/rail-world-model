# Rail World Model

철도 로봇의 **첫 관측 이미지와 계획된 카메라 이동 경로로 미래 영상을 생성**하는 연구 프로젝트.

> 연구 코드 개편 브랜치. 기관 원본 데이터·가중치·내부 경로·미공개 측정값은 포함하지 않는다. 아래 CPU 도구를 검증했으며 GPU CLI 재현 상태는 사용 설명서에 구분해 기록한다. 원본 실험은 이동하거나 변경하지 않는다.

## 연구 흐름

1. 텍스트 조건만으로 주행 방향·정지·가감속을 안정적으로 구분하기 어려웠다.
2. Isaac Sim 영상과 프레임별 카메라 pose를 연결하고, 상대 이동 9D Action을 조건으로 사용했다.
3. 전체 후속학습, Action 부분 학습, LoRA 등 기존 실험을 거쳐 Nano 기반 비교로 발전했다. 서로 다른 모델·데이터·프레임 수의 결과를 순수한 단일변수 비교로 해석하지 않는다.
4. 공통 철도 FD_joint300 초기값에서 **domain 적응 → camera-conditioned FD 적응**을 수행했다.
5. A는 가상 RGB, B는 가상·실사 RGB를 domain 단계에 사용한다. FD 단계는 두 모델 모두 가상 RGB와 카메라 Action을 사용한다. 실사 RGB에 가짜 pose를 붙이지 않는다.
6. 같은 첫 이미지·Action·prompt·seed로 비교한다. 움직임 생성과 정확한 주행 제어, 장면 보존은 별도로 평가한다.

### 입력 → 처리 → 결과

```text
Isaac Sim RGB + acquired camera poses ──> 상대 pose 9D Action
실사 RGB ──────────────────────────────> domain 적응 데이터
                      ↓
          Domain LoRA → FD LoRA + camera 입력 projector
                      ↓
   첫 RGB + 장면 설명 + 계획된 Action → 미래 RGB 영상
                      ↓
    정지/이동·속도 순서·가감속·선로/주변 구조 평가
```

실제 로봇 제어 명령을 직접 출력하는 정책 모델은 아니다.

## 개발 구조

| 경로 | 역할 |
|---|---|
| `src/rail_world_model/` | 가벼운 데이터 계약 검증 도구 |
| `configs/` | 장비 경로가 없는 연구 설정 요약 |
| `tests/` | GPU 없는 단위 테스트 |
| `docs/` | 방법·결과·재현 단계·공개 검토 |
| `scripts/` | 로컬 실험 근거 인덱스 생성 |
| `internal/` | 원본 절대경로·근거 해시. Git 제외 |
| `assets/` | 공개 승인된 예시 전용. 현재 비어 있음 |

## 실행 가능한 CPU 명령

Python 3.10 이상, 외부 패키지 불필요:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m rail_world_model validate-action /path/to/action.json --transitions 188
```

Spark에서만 사용하는 근거 위치 조회 스크립트와 결과 목록은 Git 제외로 관리한다.

## 핵심 문서

- [최종 가중치 추론 CLI](docs/INFERENCE.md) — CPU 검사와 단일 GPU 영상 생성 확인
- [CLI 검증 범위](docs/CLI_VERIFICATION.md) — 확인한 것과 미검증 사항
- [방법과 데이터](docs/METHOD.md)
- [확인된 결과와 한계](docs/RESULTS.md)
- [개발·이관 상태](docs/REPRODUCTION_STATUS.md)
- [GitHub 공개 전 검토](docs/RELEASE_CHECKLIST.md)

11월 1일의 오송 이미지 교체 추론은 요청에 따라 이번 포트폴리오 범위에서 제외했다. 대용량 데이터·모델·NVIDIA 프레임워크 전체 복사본도 포함하지 않았다.
