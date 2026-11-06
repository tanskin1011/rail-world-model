# 실행 가능한 기능과 남은 작업

## 지금 실행 가능한 것

- Python 표준 라이브러리 기반 Action 형식 검사 CLI
- 단위 테스트
- `infer.py --check`: 기존 입력·모델 설정·토큰 검사
- 설명용 5종 직선 Action 생성·검사, 새 가상환경에서 CPU 테스트 29개 통과. [CPU 검사 방법](CLEAN_CPU_REPRODUCTION.md)
- `infer.py --run/--status/--logs/--cancel`: 영상 생성·상태·로그·중단 명령. 기존 Spark에서 GPU 생성 1회와 상태·로그 조회를 확인했다. 실행 중 취소 동작은 시험하지 않았다.

## 기존 Spark에서 확인된 것

- NVIDIA Cosmos Framework native Omni 기반 Rail World Model과 과거 추론 환경
- 생성부 LoRA와 camera projector를 사용한 후속학습 기록
- 기존 보고서·비교영상과 실행 설정

장비별 절대경로는 Git 제외 `internal/`에서 관리한다. NVIDIA 프레임워크는 외부 의존성으로 사용한다.

## 남은 작업

1. 내부 학습 코드를 설정 기반의 공개 학습 CLI로 분리.
2. 새 장비에서 모델 의존성을 준비하고 GPU 추론 확인.
3. 실행 중 작업 취소 동작 검증.
4. 소스 코드 라이선스와 자료별 재배포 조건 확정.
