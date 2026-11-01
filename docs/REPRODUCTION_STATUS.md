# 재현 이관 상태

## 지금 실행 가능한 것

- Python 표준 라이브러리 기반 Action 형식 검사 CLI
- 단위 테스트
- 기존 근거·원본 경로 인덱스 생성(CPU)
- `infer.py --check`: 실제 기존 입력·native config·토큰 CPU 검사 통과
- `infer.py --run/--status/--logs/--cancel`: 최종 B 로딩용 CLI 구현. 새 GPU end-to-end 검증은 아직 없음

## 기존 Spark에서 확인된 것

- NVIDIA Cosmos Framework native Omni 기반 최종 B 모델과 과거 추론 환경
- 생성부 LoRA와 camera projector를 사용한 후속학습 기록
- 모델·결과 바로가기 및 포스터 근거 문서

기존 위치의 절대경로·외부 의존성을 그대로 public 코드에 복사하지 않는다. NVIDIA framework 전체를 자체 개발 코드로 넣지 않는다.

## 다음 이관 작업 — 아직 미완료

1. 기존 고정 실행본과 편집용 코드를 구분해 프로젝트 고유 부분만 추출.
2. 패키지·NVIDIA 원본 라이선스·파생 코드 출처 검토.
3. 사용자 설정으로 checkpoint/VAE/tokenizer/input/output 경로 지정.
4. 추론 CLI 이관은 구현 및 CPU 검사 완료. 학습 CLI 이관과 추론 GPU 재현 확인은 미완료.
5. GPU 없는 config/입력 dry-run 검증. 이후 명시된 범위에서 GPU 재현 확인.
6. 승인된 최소 예시·환경 버전·실행 결과 추가.

현재 저장소가 이미 새 PC에서 end-to-end 재현 가능하다고 주장하지 않는다. 이번 정리는 새 학습·추론을 실행하지 않는다.
