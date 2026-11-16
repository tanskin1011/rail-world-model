# 실행 가능한 기능과 남은 작업

## 지금 실행 가능한 것

- Python 표준 라이브러리 기반 Action 형식 검사 CLI
- 단위 테스트
- 복원한500step 모델과 native 실행 도구를 연결하는 `scripts/create_runtime.py`
- 고정된 Hugging Face 파일의 SHA-256 검사와 실행 소스 압축 해제: `scripts/prepare_artifacts.py`
- `infer.py --check`: 기존 입력·모델 설정·토큰 검사
- 설명용 5종 직선 Action 생성·검사. 모델 없이 새 가상환경에서 검사 가능. [CPU 검사 방법](CLEAN_CPU_REPRODUCTION.md)
- `infer.py --run/--status/--logs/--cancel`: 영상 생성·상태·로그·중단 명령. 기존 Spark에서 GPU 생성 1회와 상태·로그 조회를 확인했다. 실행 중 취소 동작은 시험하지 않았다.

## 기존 Spark에서 확인된 것

- NVIDIA Cosmos Framework native Omni 기반 Rail World Model과 과거 추론 환경
- 생성부 LoRA와 camera projector를 사용한 후속학습 기록
- 기존 보고서·비교영상과 실행 설정

장비별 절대경로는 Git 제외 `internal/`에서 관리한다. NVIDIA 프레임워크는 외부 의존성으로 사용한다.

## Spark 외부 모델 보관

500step 추론 변경 가중치·정확한 Base DCP·VAE·tokenizer·실행 소스는 Hugging Face 모델 저장소에서 공개한다. 파일33개 원격 크기·해시 대조, 변경 가중치 재다운로드 해시 검사를 완료했다. 로그인 없는 접근과 manifest 다운로드를 확인했다. [다운로드와 복원](WEIGHTS.md) 참조.

2026-11-16에는 모델 파일을 임시 경로에 배치하고, 보관 ZIP에서 푼 Framework·실행 도구로 복원 절차를 확인했다. 전체1,097개 텐서 해시 대조, 새 runtime 생성, 실제 PNG·Action·텍스트의 native CPU 입력 검사 통과. 설치된 Python 패키지는 기존 환경을 사용했으며 GPU 모델 로드는 수행하지 않았다. 원천 경로의 파일 내용과 수정 시각은 유지했다.

## 남은 작업

1. 내부 학습 코드를 설정 기반의 공개 학습 CLI로 분리.
2. 새 장비에서 모델 의존성을 준비하고 GPU 추론 확인.
3. 실행 중 작업 취소 동작 검증.
4. 소스 코드 라이선스와 자료별 재배포 조건 확정.
