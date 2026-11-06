# 개발 규칙

- 코드, 실행 설정, 실험 결과, 대용량 원본 데이터를 구분한다.
- 새 기능은 CPU 검사부터 만들고 기존 GPU 실행을 임의로 시작하지 않는다.
- 결과 주장의 출처와 측정 범위를 남긴다. 초안의 계획을 완료 사실로 바꾸지 않는다.
- 기존 실험 원본은 변경하지 않는다. 내부 연결은 `internal/`에서 관리한다.
- 공개 가능한 예시는 승인 후 `assets/`에 추가한다. symlink를 따라 내부 자료를 일괄 복사하지 않는다.
- 공개 라이선스는 소유권·기관 승인을 확인한 뒤 정한다.

## 현재 구현 범위

| 구성 | 상태 |
|---|---|
| Action 생성·형식 검사 | 표준 라이브러리로 실행 가능 |
| 추론 CLI | 기존 Spark에서 모델 로드·생성·전체 디코딩 확인 |
| 학습 CLI | 기존 내부 실행 코드를 공개 도구로 분리하는 작업 필요 |
| CPU 테스트 | 로컬·독립 가상환경에서 29개 통과 |
| GitHub CI | 테스트와 배포 검사 정의. 이번 수정본의 원격 실행 전 |
| 대표 미디어 | 비교영상 4개·학습 이미지 2개와 출처·판정 제공 |

## 수정 후 검사

저장소 루트에서 실행한다.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/audit_release.py
python3 scripts/check_clean_cpu.py --report internal/clean_cpu_check.json
```

보고서 파일이 이미 있으면 새 이름을 사용한다. 위 검사는 학습·GPU 추론을 실행하지 않으며 Git stage·commit·push도 수행하지 않는다. 공개 후보만 복사해 검사하는 방법은 [CPU 재현 안내](CLEAN_CPU_REPRODUCTION.md)를 참고한다.
