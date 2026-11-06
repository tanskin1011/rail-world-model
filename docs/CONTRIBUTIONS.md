# 수행 내용과 기여 범위

철도 적용을 위한 데이터 구성, 후속학습 설정, 비교 평가와 추론 도구를 정리한다. 기반 모델과 기본 Forward Dynamics 구조는 NVIDIA Cosmos를 사용했다.

## 문제 정의

정지·정속·가감속에 대한 반응과 카메라 시점·선로 구조 유지를 각각 평가하도록 구성했다. 텍스트 조건 실험을 거쳐 카메라 Action 조건 학습으로 전환했다.

## 데이터·학습 설계

Isaac Sim의 RGB·pose를 연결하고 프레임 간 상대 변환을 9D Action으로 구성했다. 실제 취득 pose와 촬영 설정에서 재구성한 pose는 신뢰 수준을 구분한다. 실사 pose가 없는 영상에 임의 Action을 정답으로 붙이지 않고 domain 적응 데이터로 사용했다.

공통 철도 초기값에서 영상 외관 적응(domain) → 카메라 경로 조건 학습(FD)으로 나눴다. domain 단계에서 가상 전용 A와 가상·실사 혼합 B를 비교했다. 학습 대상은 생성부 LoRA와 camera 입력 projector 일부다.

## 운영·개발 산출물

입력·prompt·seed·checkpoint·sampling 설정을 기록했다. 기존 가중치를 불러오는 CLI에 입력 형식 검사, 가중치 해시 대조, 전체 영상 디코딩 검사, 작업 상태·로그 조회를 구현했다.

## 기존 기술과의 경계

Cosmos backbone·기본 Forward Dynamics 구조·Wan VAE·tokenizer·NVIDIA 프레임워크는 기존 구성요소다. 프로젝트의 개발 대상은 철도 적용을 위한 데이터 처리·학습 설정·실험 운영·추론 및 검증 도구다.
