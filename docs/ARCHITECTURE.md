# 모델과 실행 코드

## 입력에서 영상까지

```text
첫 RGB 이미지 ── 영상 인코딩 ──────────────┐
장면 설명 ───── 텍스트 토큰화 ─────────────┤
188×9 카메라 Action ── 64차원 패딩 ───────┤
                     camera domain 2      │
                     카메라 입력 projector│
                                          ▼
                           Cosmos3-Nano 영상 생성부
                           생성 attention LoRA 적용
                           미래 영상 latent 노이즈 제거
                                          │
                                          ▼
                                  Wan VAE 디코딩
                                          │
                                          ▼
                         189프레임 · 832×480 · 24FPS
```

첫 이미지와 카메라 경로는 고정 조건이다. 모델은 사용자가 정한 경로에 대응하는 미래 화면을 생성한다. 카메라 Action은 이동3값과 회전6값으로 구성하고, 뒤에0을 붙여64차원으로 만든다. 자세한 좌표계와 상대 변환은 [방법](METHOD.md)에 정리했다.

## 학습되는 부분

| 부분 | 영상 적응 | 카메라 경로 조건 학습 |
|---|---|---|
| 생성 attention q/k/v/o의 LoRA | 학습 | 학습 |
| 카메라 입력 projector | 고정 | camera domain2·입력9채널과 bias만 학습 |
| 나머지 backbone·VAE·Action 출력부 | 고정 | 고정 |

영상 적응에서는 가상·실사 RGB를 사용한다. 카메라 조건 학습에서는 실제 렌더 카메라 pose가 있는 가상 RGB를 사용한다. 미래 영상 복원 손실이 학습 대상 가중치에 전달된다.

## CLI 호출 흐름

```text
infer.py
  └─ infer_cli.py
       ├─ runtime·PNG·Action·prompt 검사
       ├─ native_worker.py --check-stdin : native 입력 구성 검사
       └─ --run
            ├─ TAO job-record 생성
            ├─ virtualenv runner에 작업 제출
            └─ inference_supervisor.py
                 ├─ 메모리·GPU·디스크 감시
                 └─ native_worker.py
                      ├─ DCP 모델 로드·텐서 해시 대조
                      ├─ 첫 이미지·Action 조건 위치 대조
                      ├─ native 영상 생성·디코딩
                      └─ MP4·설정·검사 결과 저장
```

| 파일 | 역할 |
|---|---|
| [actions.py](../src/rail_world_model/actions.py) | 직선 경로 예시 생성 |
| [contracts.py](../src/rail_world_model/contracts.py) | Action 개수·차원·수치 검사 |
| [infer_cli.py](../src/rail_world_model/infer_cli.py) | 입력 검사와 submit/status/logs/cancel 연결 |
| [inference_supervisor.py](../src/rail_world_model/inference_supervisor.py) | 자원 감시와 본 작업 프로세스 관리 |
| [native_worker.py](../src/rail_world_model/native_worker.py) | NVIDIA native 모델 API 호출·가중치·출력 검사 |
| [restore_weights.py](../scripts/restore_weights.py) | 변경 가중치와 Base로 추론용 DCP 복원 |
| [create_runtime.py](../scripts/create_runtime.py) | 복원한 모델과 장비별 실행 경로 연결 |

native Framework·기반 가중치·TAO runner·자원 감시 모듈은 외부 실행 의존성이다. 저장소의 코드만 확인하려면 [CPU 재현](CLEAN_CPU_REPRODUCTION.md), 실제 영상 생성 준비는 [추론](INFERENCE.md)을 따른다.
