# 비공개 자산 없는 CPU 재현 확인

공개 대상 소스만 별도 임시 폴더로 복사하고 새 가상환경에서 검사한다. 기본값은 현재 작업 파일로, 새 파일과 이름 변경도 포함한다. `internal/`, `local/`, 데이터셋, 체크포인트는 제외한다. 검사 전 Git stage는 필요 없다.

## 확인 결과

- Python 3.13.12의 새 가상환경, pip 없이 실행.
- 외부 Python 패키지를 설치하지 않음.
- 단위 테스트 29개 통과(2026-11-06 FD500 배포 도구 포함).
- STOP / const5 / const10 / accel / decel의 설명용 직선 Action 생성 및 형식 검사 통과.
- 모델 로딩·CUDA 초기화·영상 생성 없음.

이 검사는 같은 Spark에서 **비공개 자산과 기존 Python 패키지에 의존하지 않는 CPU 기능**을 확인한 것이다. 다른 물리 장비에서 GPU 추론까지 확인한 결과가 아니다.

## 재현 명령

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

현재 작업 파일의 경로·크기·문서 링크를 검사한 뒤, 독립 가상환경에서 테스트와 Action 예시를 확인한다. Git이 설치되어 있어야 하며 출력 report는 새 파일명이어야 한다.

```bash
python3 scripts/audit_release.py
python3 scripts/check_clean_cpu.py --report internal/clean_cpu_check.json
```

stage한 내용만 검사하려면 `--staged`를 추가한다. 이 경우 stage하지 않은 변경과 새 파일은 포함되지 않는다. Git index와 작업 파일은 도구가 수정하지 않는다. staged export에는 안전한 tar 필터를 지원하는 Python 3.12 이상을 권장한다.

Action 예시는 camera +Z 방향의 직선 계획이며 회전은 항등이다. 생성된 숫자의 이동량·형식을 검사한 것으로, 측정 pose GT나 영상 모델의 속도 추종 평가에 해당하지 않는다.
