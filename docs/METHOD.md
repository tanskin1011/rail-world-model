# 방법과 데이터

## 연구 질문

공통 초기 모델에서 domain 단계의 실사 RGB 혼합이 이후 카메라 경로 조건 영상 생성에 어떤 차이를 주는가?

## 데이터

포스터 근거 문서의 분할은 가상 294개(train240/validation54), 실사 RGB120개(train107/validation13)이다. 파일 수 비율과 실제 학습 노출 비율을 구별한다. B domain은 600회 노출 중 가상420·실사180을 계획한 70:30 구성이다. FD는 가상 RGB와 pose만 사용한다. 최종 실행별 실제 노출 수·학습 완료 상태는 로컬 원본 로그를 근거로 별도 확정한다.

## Camera Action

OpenCV camera-to-world 행렬을 `T_i`라 하면 인접 프레임의 상대 변환은 `inv(T_i) @ T_(i+1)`이다. 이동 3값과 회전행렬 첫 두 열의 6값을 연결해 9D로 표현한다. 188개 전이를 189 RGB 프레임과 연결한다. 모델에는 뒤에 55개의 0을 붙인 64D가 들어가고 camera domain 2가 선택된다.

STOP은 이동이 0이지만 회전은 항등이다. 따라서 전체가 0인 9D 벡터가 아니다. 추론 때에도 계획된 Action 파일을 넣는다. 학습 영상의 파일 경로만 참조해서 주행을 재생하는 구조가 아니다.

## 학습 범위

domain: 생성부 attention q/k/v/o LoRA. FD: 같은 LoRA와 camera 입력 projector의 허용된 부분. LoRA rank16/alpha32. backbone·VAE·action 출력 head 등을 모두 full SFT한 최종 모델로 설명하지 않는다.

FD에서 첫 영상 latent와 모든 Action은 clean condition이다. 미래 영상 latent의 RF 학습 손실이 LoRA와 입력 projector에 전달된다. 이때 Action을 미래 출력으로 예측하는 정책 학습은 아니다.

## 계보·비교 주의

공통 초기값 자체가 기존 철도 FD_joint300이다. untouched pretrained Base에서 처음 학습한 결과가 아니다. 과거 Edge full-SFT 및 61프레임 Nano 결과는 연구 발전의 배경으로만 구분한다. test1 환경의 과거 노출 이력이 있으므로 새 노선 일반화 성공이라고 표현하지 않는다.
