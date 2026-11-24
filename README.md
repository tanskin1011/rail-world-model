# Rail World Model

**첫 이미지와 카메라 궤적으로 철도 주행 영상을 생성하는 조건부 월드모델**

Camera-trajectory-conditioned railway video generation with Cosmos3-Nano, LoRA adaptation and Forward Dynamics.

[모델 가중치](https://huggingface.co/tanskin02/rail-world-model-camera-500step) · [빠른 실행](#빠른-실행) · [구조](#구조와-학습) · [평가](#결과와-평가) · [개발](#개발과-검증)

## 생성 결과

같은 감속 궤적을 서로 다른 첫 이미지에 입력한 **FD500**의 기존 생성 결과다. 미리보기를 누르면 전체 영상을 볼 수 있다.

| 실사 이미지 조건 | 합성 이미지 조건 |
|---|---|
| [![실사 첫 이미지에서 생성한 FD500 감속 영상](assets/results/fd500_real_decel.gif)](assets/results/fd500_real_decel.mp4) | [![학습에 노출된 합성 이미지에서 생성한 FD500 감속 영상](assets/results/fd500_sim_decel.gif)](assets/results/fd500_sim_decel.mp4) |
| 높은 열차 시점과 곡선 선로를 유지하며 후반 배경 이동이 감소하는 경향 | 낮은 철도 시점에서 가까운 전주가 지나가고 후반 배경 이동이 감소하는 경향 |

각 영상은 **832 × 480 · 189프레임 · 24 FPS**다. 감속은 입력한 카메라 계획이며, 실제 출력 속도나 자동제동 성능을 측정한 결과는 아니다. 합성 예시는 학습에 노출된 장면이다. [생성 조건·출처·편집 기록](docs/MEDIA_GALLERY.md)

## 해결하려는 문제

철도 로봇의 이동 조건을 바꿨을 때 카메라에 보일 장면을 생성하는 것이 목표다. 텍스트로 정지·가감속을 요청하는 실험에서 출발해, 프레임별 상대 이동·회전을 직접 입력하는 방식으로 확장했다. **이동 조건에 대한 반응**과 **선로·시설물의 보존**을 함께 확인한다.

| 항목 | 현재 구현 |
|---|---|
| 입력 | RGB 첫 이미지 + 장면 설명 + 카메라 Action `188 × 9` |
| 출력 | 미래 RGB 영상, 189프레임·832 × 480·24 FPS |
| 기반 모델 | NVIDIA Cosmos3-Nano, native Cosmos Framework Omni |
| 학습 대상 | 생성 attention LoRA(rank 16 / alpha 32) + 카메라 입력 projector 일부 |
| 선택 체크포인트 | FD500: FD300에서 optimizer·scheduler 상태를 이어 추가 200 updates |
| 공개 범위 | 프로젝트 코드·테스트·선별 영상, Hugging Face 추론용 가중치·실행 소스 |

출력은 주행 영상이다. 로봇의 제어 명령을 예측하는 정책이나 상호작용형 시뮬레이터는 이 저장소의 구현 범위에 포함하지 않는다.

## 구조와 학습

![합성 RGB·pose와 실사 RGB의 학습 단계 및 카메라 조건 추론 구조](assets/pipeline.svg)

1. **데이터 구성:** Isaac Sim의 RGB와 렌더 카메라 pose를 연결하고, 실사 RGB는 영상 외관 적응에 사용했다.
2. **영상 적응:** 가상 RGB 전용 A와 가상·실사 70:30 샘플링 B를 비교했다.
3. **카메라 조건 학습:** 검증된 합성 pose로 만든 Action과 첫 이미지를 조건으로, 미래 영상 latent를 복원하도록 LoRA와 카메라 입력부를 학습했다.
4. **추론 도구:** 입력 형식·조건 주입·로드 가중치 해시·출력 디코딩 검사와 작업 상태·로그·자원 감시를 연결했다.

| 데이터 | Train clips | Validation clips | 사용 단계 |
|---|---:|---:|---|
| 합성 RGB + 카메라 pose | 240 | 54 | 영상 적응·카메라 조건 학습 |
| 실사 RGB | 107 | 13 | 영상 적응 |

카메라 `c2w` 행렬을 `T_i`라 하면 `inv(T_i) @ T_(i+1)`에서 이동 3값과 회전행렬 첫 두 열 6값을 얻는다. 이 **9D Action** 뒤에 0을 붙여 모델의 64D 입력으로 전달한다. 정지는 이동 0·항등 회전으로 표현한다.

공통 시작점은 이미 철도 학습을 거친 `FD_joint300`이다. A/B 비교는 같은 시작점에서 **실사 혼합 여부**를 바꾼 실험이며, 원본 사전학습 Base와의 비교로 해석하지 않는다. Cosmos backbone과 기본 FD 구조는 NVIDIA의 구성요소다. 프로젝트에서 수행한 작업은 데이터·Action 구성, 학습 설정, 비교 실험과 추론·검증 도구 개발이다.

[기여 범위](docs/CONTRIBUTIONS.md) · [Action 변환과 방법](docs/METHOD.md) · [학습 설정](docs/TRAINING.md) · [실행 코드 구조](docs/ARCHITECTURE.md)

## 결과와 평가

| 확인할 내용 | 공개 근거 | 현재 판단 |
|---|---|---|
| 최신 모델의 감속 반응 | FD500 실사·합성 입력 영상 2개 | 후반 배경 이동 감소를 정성 관찰 |
| 데이터 혼합에 따른 차이 | FD300 A/B의 STOP·가속·감속 비교 | B의 일관된 우위는 확인하지 못함 |
| 정지 조건 준수 | FD300 STOP A/B 영상 | 정지 입력에도 전진하는 실패 |
| 장면 보존 | 시뮬레이터 원본/FD300 생성 비교 | 레일·시설물 변형과 세부 외관 변화가 남음 |
| FD500의 FD300 대비 개선·미학습 노선 일반화 | 대응 비교를 추가할 예정 | 아직 검증하지 않음 |

<details>
<summary>이전 FD300의 동일 조건 비교 영상</summary>

| 감속 A/B | STOP 실패 A/B |
|---|---|
| [![동일 조건의 FD300 A/B 감속 비교](assets/results/ab_decel30.jpg)](assets/results/ab_decel30.mp4) | [![정지 입력에도 전진하는 FD300 A/B 실패 사례](assets/results/ab_stop.jpg)](assets/results/ab_stop.mp4) |

[가속 A/B](assets/results/ab_accel10.mp4) · [시뮬레이터 원본/생성 비교](assets/results/sim_gt_vs_b_decel30.mp4)

</details>

공개 영상은 사례별 정성 근거다. 기존 GT 대응 지표는 내부 기록에 보관돼 있어 이 페이지에 수치로 제시하지 않는다. 다음 검증은 FD300/FD500에 동일 이미지·Action·prompt·seed를 사용하고, 정지·정속·가감속의 조건 준수와 구조 보존을 분리해 측정하는 것이다. [현재 결과](docs/RESULTS.md) · [후속 평가 프로토콜](docs/EVALUATION.md)

## 빠른 실행

### 1. 모델 없이 입력 예제 준비

Python 3.10 이상과 Git을 사용한다. 아래 명령은 Windows·Linux에서 Python 표준 라이브러리만으로 실행하며 모델을 내려받거나 GPU를 사용하지 않는다. Linux에서 Python 명령이 `python3`이면 바꿔 실행한다.

```bash
git clone https://github.com/tanskin1011/rail-world-model.git
cd rail-world-model
python scripts/prepare_demo.py --profile decel --output local/demo
```

`DEMO_INPUTS_READY`가 출력되면 다음 파일이 준비된다.

```text
local/demo/
├── input.png           # 공개된 합성 학습 이미지, 832 × 480
├── action.json         # 188 × 9 카메라 계획
├── scene.txt           # 이동 조건을 넣지 않은 장면 설명
└── demo_manifest.json  # 입력 해시·규격·출처·계획 이동량
```

프로파일은 `stop`, `const5`, `const10`, `accel`, `decel`을 지원한다. 예제 `decel`은 **10→0 km/h의 수학적 직선 계획**으로, 상단의 기존 30→0 감속 영상과 입력이 다르다. 이 샘플은 실행 확인용이며 미학습 환경 평가용 데이터가 아니다. 기존 출력 폴더는 덮어쓰지 않는다.

### 2. 가중치와 native 실행 환경 준비

FD500 추론 가중치·정확한 Base DCP·VAE·tokenizer·호환 실행 소스 약 **34.4 GB**를 공개한다. [다운로드·설치·복원 안내](docs/WEIGHTS.md)의 순서대로 준비하고 `internal/runtime_500step.json`을 생성한다.

```bash
hf download tanskin02/rail-world-model-camera-500step --revision 379bea5f3a00a51a1aaea402bc774a4e27669f37 --local-dir local/artifacts/camera-500step
python scripts/prepare_artifacts.py --artifacts local/artifacts/camera-500step --support-output local/runtime_sources
```

GPU 생성은 **Linux native 환경**을 기준으로 한다. 기존 환경은 aarch64·Python 3.13.12·PyTorch 2.10.0+cu130·Framework 1.2.2다. 새 장비의 최소 VRAM·생성 시간은 아직 측정하지 않았다. 프로젝트의 표준 라이브러리 도구와 native 모델의 설치 의존성은 구분한다.

### 3. 입력 검사 후 영상 생성

위 복원·환경 설정을 마친 뒤 실행한다. `--check`는 native CPU 입력 검사이며, `--run`에서 GPU 작업을 제출한다.

```bash
python infer.py --runtime internal/runtime_500step.json --image local/demo/input.png --action local/demo/action.json --prompt-file local/demo/scene.txt --output outputs/demo --check
python infer.py --runtime internal/runtime_500step.json --image local/demo/input.png --action local/demo/action.json --prompt-file local/demo/scene.txt --output outputs/demo --run
```

생성 영상은 `outputs/demo/video/vision.mp4`에 저장된다. 입력·모델 설정·조건 주입·해시·실행 상태도 함께 기록한다. `--run`이 반환하는 `job_dir`로 상태·로그·중단 명령을 사용한다. [CLI 명령과 출력](docs/INFERENCE.md)

### 재현 확인 범위

| 단계 | 확인된 범위 |
|---|---|
| 공개 CPU 도구 | Action 검사·배포 파일 감사·독립 가상환경 검사 제공 |
| FD500 가중치 복원 | 기존 기록에서 전체 1,097개 텐서 해시 및 native CPU 입력 검사 통과 |
| CLI GPU 생성 | 기존 Spark의 FD300에서 생성·MP4 전체 디코딩 확인 |
| 새 장비의 FD500 GPU 생성 | 추가 검증 필요 |
| 공개 코드로 학습 재현 | 내부 loader·gradient mask·native 학습 CLI 분리 필요 |

[검증 기록과 남은 작업](docs/REPRODUCTION_STATUS.md) · [CPU 독립 검사 기록](docs/CLEAN_CPU_REPRODUCTION.md)

## 개발과 검증

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/audit_release.py
python scripts/check_clean_cpu.py --report internal/clean_cpu_check.json
```

CPU 도구는 `python -m rail_world_model`로도 호출할 수 있다. 테스트는 GPU·가중치·비공개 데이터 없이 실행한다. 심볼릭 링크 생성이 허용되지 않은 Windows에서는 관련 테스트만 사유와 함께 건너뛴다. 독립 검사 report에는 실행·통과·건너뛴 개수가 기록된다.

```text
src/rail_world_model/   Action 처리·추론 CLI·자원 감시
scripts/               공개 샘플 준비·가중치 복원·배포 검사
configs/               실행 설정 예시·학습 규약
tests/                 CPU 계약·파일 처리 테스트
docs/                  학습·실행·결과·평가 문서
assets/                구조도·공개 대표 영상
```

장비별 경로·실험 원본은 Git 제외 `local/`, `internal/`에서 관리한다. 소스 코드의 일반 재사용 라이선스는 아직 확정하지 않았다. 기반 모델과 외부 소프트웨어의 이용 조건, 자료별 출처는 [THIRD_PARTY.md](THIRD_PARTY.md)를 따른다.

## 관련 프로젝트

- [NVIDIA Cosmos](https://github.com/NVIDIA/cosmos): 기반 모델과 Physical AI 개발 도구.
- [DreamDojo](https://github.com/NVIDIA/DreamDojo): 로봇 월드모델의 학습·평가 문서 구성 참고.
- [DIAMOND](https://github.com/eloialonso/diamond): 실행 예제, 설정과 seed별 결과 연결 방식 참고.
- [DreamerV3](https://github.com/danijar/dreamerv3): 방법·벤치마크·설치·로그를 연결하는 연구 코드 구성 참고.

위 프로젝트와 Rail World Model은 연구 목표와 평가 환경이 다르며, 성능 비교 대상으로 제시한 것은 아니다.
