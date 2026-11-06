# 방법과 데이터

## 연구 질문

공통 초기 모델에서 domain 단계의 실사 RGB 혼합이 이후 카메라 경로 조건 영상 생성에 어떤 차이를 주는가?

## 데이터

| 자료 | Train | Validation | 사용 단계 |
|---|---:|---:|---|
| 가상 RGB·카메라 pose | 240 | 54 | domain·FD |
| 실사 RGB | 107 | 13 | domain |

B의 domain sampling 비율은 가상:실사 = 70:30이다. 파일 개수 비율과 학습 중 추출 비율은 다르다. FD 단계에는 가상 RGB·pose만 사용한다. 실행별 노출 수와 완료 기록은 내부 학습 로그에 보관한다.

## Camera Action

OpenCV camera-to-world 행렬을 `T_i`라 하면 인접 프레임의 상대 변환은 `inv(T_i) @ T_(i+1)`이다. 이동 3값과 회전행렬 첫 두 열의 6값을 연결해 9D로 표현한다. 188개 전이를 189 RGB 프레임과 연결한다. 모델에는 뒤에 55개의 0을 붙인 64D가 들어가고 camera domain 2가 선택된다.

STOP은 이동이 0이지만 회전은 항등이다. 따라서 전체가 0인 9D 벡터가 아니다. 추론 때에도 계획된 Action 파일을 넣는다. 학습 영상의 파일 경로만 참조해서 주행을 재생하는 구조가 아니다.

## 학습 범위

domain 단계는 생성부 attention q/k/v/o의 LoRA를 학습한다. FD 단계는 같은 LoRA와 camera 입력 projector 일부를 학습한다. LoRA는 rank16/alpha32이며, backbone 전체·VAE·Action 출력 head를 모두 학습하는 Full SFT는 사용하지 않는다.

FD에서는 첫 이미지와 모든 Action을 노이즈 없는 조건으로 넣고, 미래 영상 latent에 노이즈를 더해 복원하도록 학습한다. 영상 복원 손실이 LoRA와 입력 projector에 전달된다. 모델의 출력은 미래 영상이며 Action 자체를 예측하는 정책 학습은 아니다.

## 계보·비교 주의

공통 초기값은 철도 학습을 거친 `FD_joint300`이다. 사전학습 Base에서 새로 시작한 실험이 아니다. 과거 Edge Full SFT와 61프레임 Nano 실험은 이 모델의 결과와 구분한다. `test1` 환경은 과거 학습 노출 이력이 있어 새 노선 일반화 평가에 해당하지 않는다.

현재 선택 모델 FD500은 기존 domain 적응 → FD300 이후 같은 학습 범위로 200 updates를 이어 학습한 체크포인트다. FD 단계의 누적 step은500이며, 이전 domain 단계와 선행 철도 학습의 step을 합친 수치가 아니다.
