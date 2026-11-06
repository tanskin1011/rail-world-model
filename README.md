# Rail World Model

### 카메라 경로 조건을 이용한 철도 로봇 시점 영상 생성

**첫 이미지 + 장면 설명 + 계획된 카메라 경로 → 미래 RGB 영상**

NVIDIA Cosmos3-Nano를 후속학습해, 카메라 이동 경로를 조건으로 철도 주행 영상을 생성하는 연구 프로젝트입니다. 출력은 RGB 영상이며 로봇의 모터 제어 명령이 아닙니다.

[방법](docs/METHOD.md) · [수행 내용](docs/CONTRIBUTIONS.md) · [결과·한계](docs/RESULTS.md) · [추론 사용법](docs/INFERENCE.md)

![Camera-conditioned world model](assets/pipeline.svg)

도식은 입력과 학습 흐름을 설명합니다. 실제 결과는 아래 비교영상에서 확인할 수 있습니다.

## 문제와 접근

텍스트만으로 정지·정속·가감속을 구분하기 어려워, 카메라의 프레임별 이동·회전값을 입력하는 Forward Dynamics를 적용했습니다.

| 단계 | 수행 내용 | 설계 판단 |
|---|---|---|
| 데이터 | Isaac Sim RGB·카메라 pose 대응, 검수·분할 | 영상과 이동값의 시간축 일치 |
| 조건 표현 | 인접 pose → 상대 이동·회전 9D Action | STOP도 항등 회전이므로 전체 0 벡터가 아님 |
| Domain 적응 | 가상 전용 A / 가상·실사 혼합 B의 생성부 LoRA | 실사 RGB에 가짜 pose를 붙이지 않음 |
| FD 적응 | 가상 RGB·Action으로 LoRA + camera 입력 projector 학습 | 첫 이미지와 Action을 미래 영상의 조건으로 사용 |
| 비교·운영 | 입력·prompt·seed·설정 고정, CLI와 검증 도구 | 움직임 생성과 정확한 제어·장면 보존을 구별 |

생성부 LoRA와 카메라 입력부 일부를 학습했습니다. 공통 초기값은 철도 학습을 거친 `FD_joint300`이며, 전체 가중치를 학습한 Full SFT는 아닙니다. [방법·학습 계보](docs/METHOD.md)

현재 선택 모델은 **FD500**입니다. 기존 FD300에서 같은 학습 범위를 유지해 200 updates를 추가했습니다. 아래 A/B 대표 영상과 CLI 검증 기록은 이전 FD300 결과이며, FD500의 성능 증거로 바꿔 표시하지 않습니다.

## 결과와 한계

| 확인한 항목 | 근거 수준 |
|---|---|
| 기존 가중치를 새 CLI로 사용 | 실제 GPU 실행 1회 통과, 1,097개 tensor hash 대조 |
| 영상 파일 생성 | 832×480 · 189프레임 · 24 FPS, 전체 디코딩 통과 |
| 조건 입력 | 첫 프레임 [0], camera domain2, 188개 Action 확인 |
| 주행 조건 | 감속 요청에서 후반 변화 감소 경향 관찰. STOP 요청에도 전진하는 실패 존재 |
| 실행 환경 | 내부 자산 없이 CPU 검사 가능. GPU 생성은 기존 Spark에서 확인 |

남은 과제는 장면 구조·주변 객체 움직임 유지와 정확한 속도 추종입니다. 실사 혼합 B의 일관된 우위와 새 노선 일반화는 확인하지 못했습니다. [결과·한계](docs/RESULTS.md)

## 대표 비교영상

**A = 가상 전용 domain 적응 / B = 가상·실사 혼합 domain 적응. FD 단계는 같은 가상 데이터·카메라 조건을 사용합니다.** 이미지를 누르면 대응 MP4로 이동합니다.

| 감속 요청: 후반 변화 감소 경향 | STOP 실패: 정지 요청에도 전진 |
|---|---|
| [![A/B 감속](assets/results/ab_decel30.jpg)](assets/results/ab_decel30.mp4) | [![A/B STOP 실패](assets/results/ab_stop.jpg)](assets/results/ab_stop.mp4) |

- [감속 A/B 영상](assets/results/ab_decel30.mp4) · [가속 A/B 영상](assets/results/ab_accel10.mp4) · [STOP 실패 A/B 영상](assets/results/ab_stop.mp4)
- [Isaac Sim 원본 / Rail World Model 생성 비교](assets/results/sim_gt_vs_b_decel30.mp4)
- [학습 이미지·대표 프레임·선택 이유와 한계](docs/MEDIA_GALLERY.md)

기존 결과를 189프레임·24 FPS로 편집했습니다. 감속 경향과 STOP 실패, 구조 변형을 함께 확인할 수 있습니다. 실제 km/h를 측정한 평가는 아닙니다.

## 빠르게 실행해 보기 — GPU·비공개 데이터 불필요

Python 3.10 이상. 외부 Python 패키지가 필요 없습니다.

```bash
git clone https://github.com/tanskin1011/cosmos3-nano-rail-lora.git rail-world-model
cd rail-world-model
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m rail_world_model make-action \
  --profile const10 --output /tmp/rail_demo_const10.json
PYTHONPATH=src python3 -m rail_world_model validate-action \
  /tmp/rail_demo_const10.json --transitions 188
```

출력 파일이 이미 있으면 새 이름을 사용하세요. 이 명령은 직선 이동 계획을 숫자로 만들고 형식을 검사합니다. 모델을 불러오거나 영상을 생성하지 않습니다.

실제 영상 생성은 원본 Nano 의존 가중치·최종 checkpoint·VAE·tokenizer·검증된 native 환경 및 로컬 runtime profile이 필요합니다.

```bash
python3 infer.py --image input.png --action action.json \
  --prompt-file scene.txt --output outputs/demo --check
python3 infer.py --image input.png --action action.json \
  --prompt-file scene.txt --output outputs/demo --run
```

[실행·상태·로그·중단](docs/INFERENCE.md) · [GPU 검증 범위](docs/CLI_VERIFICATION.md) · [비공개 자산 없는 CPU 재현](docs/CLEAN_CPU_REPRODUCTION.md)

## 모델 가중치

FD500 추론용 delta 묶음을 로컬에서 준비했습니다. 가중치는 아직 외부 저장소에 업로드하지 않았습니다.

묶음에는 추가 학습 가중치와 복원 도구가 들어 있으며, 해시가 일치하는 원본 Base DCP·VAE·tokenizer가 별도로 필요합니다. [가중치 구성·복원 방법](docs/WEIGHTS.md)

## 개발 구조

```text
infer.py                    # 추론 CLI 진입점
src/rail_world_model/        # Action 검사·예시, 추론·자원 감시
configs/                    # 연구 설정·로컬 runtime 예시
configs/rail_world_model_protocol.json # 학습·입출력 규약 요약
tests/                      # 모델 없이 실행하는 테스트
docs/                       # 방법·결과·재현·공개 범위
assets/                     # 자체 구조도
local/                      # 현재 Spark의 데이터·학습 코드·모델 연결 (Git 제외)
internal/                   # 실제 runtime 설정·가중치 해시·근거 (Git 제외)
```

NVIDIA 프레임워크는 외부 의존성으로 두고, 이 저장소에는 철도 적용 코드·설정·문서·선별된 결과를 보관합니다. 모델 가중치와 원천 데이터는 포함하지 않습니다.

폴더별 역할은 [프로젝트 구조](docs/PROJECT_LAYOUT.md)를 참고하세요. 원격 저장소 URL에는 이전 이름인 `cosmos3-nano-rail-lora`가 남아 있습니다.

[외부 구성요소·권리](THIRD_PARTY.md) · [공개 검토](docs/RELEASE_CHECKLIST.md) · [개발 상태](docs/DEVELOPMENT.md)
