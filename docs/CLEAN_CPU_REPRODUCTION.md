# 비공개 자산 없는 CPU 재현 확인

공개 대상 소스만 별도 임시 폴더로 복사하고 새 가상환경에서 검사한다. 기본값은 현재 작업 파일로, 새 파일과 이름 변경도 포함한다. `internal/`, `local/`, 데이터셋, 체크포인트는 제외한다. 검사 전 Git stage는 필요 없다.

## 확인 결과

### 2026-11-24 Windows 검사

| 항목 | 결과 |
|---|---|
| 환경 | Windows · Python 3.12.14 |
| 공개 소스 독립 검사 | 임시 폴더 복사·pip 없는 새 가상환경에서 통과 |
| 단위 테스트 | 47개 중 38개 통과·9개 건너뜀, 실패·오류 0 |
| 건너뛴 사유 | 호스트의 심볼릭 링크 생성 권한 부족 |
| Action 생성·형식 검사 | STOP·const5·const10·accel·decel 통과 |
| 공개 샘플 | prepare_demo로 이미지·Action·prompt·해시 생성, 추론 요청 형식 연결 검사 통과 |
| 모델·GPU·외부 패키지 | 모델 로드·GPU 생성·외부 Python 패키지 설치 없음 |

실행 근거는 로컬 Git 제외 `internal/clean_cpu_20261124.json`에 보관한다. 심볼릭 링크 검사의 실제 실행과 Linux·다른 Python 버전은 CI에서 별도로 확인한다. 이 기록은 새 장비의 FD500 GPU 추론을 검증하지 않는다.

### 기존 Spark 검사

아래 항목은 2026-11-06의 기존 Spark 검사 기록이다.

- Python 3.13.12의 새 가상환경, pip 없이 실행.
- 외부 Python 패키지를 설치하지 않음.
- 단위 테스트 30개 통과(2026-11-06 FD500 배포·미리보기 검사 포함).
- STOP / const5 / const10 / accel / decel의 설명용 직선 Action 생성 및 형식 검사 통과.
- 모델 로딩·CUDA 초기화·영상 생성 없음.

이 검사는 같은 Spark에서 **비공개 자산과 기존 Python 패키지에 의존하지 않는 CPU 기능**을 확인한 것이다. 다른 물리 장비에서 GPU 추론까지 확인한 결과가 아니다.

현재 검사 도구는 Windows와 Linux의 가상환경 경로를 구분한다. 심볼릭 링크를 만들 권한이 없는 환경에서는 해당 테스트만 사유와 함께 건너뛴다. `unit_tests_passed`, `unit_tests_skipped`를 함께 확인해야 하며, 모든 테스트를 실행했다고 해석하지 않는다.

## 재현 명령

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

현재 작업 파일의 경로·크기·문서 링크를 검사한 뒤, 독립 가상환경에서 테스트와 Action 예시를 확인한다. Git이 설치되어 있어야 하며 출력 report는 새 파일명이어야 한다.

```bash
python3 scripts/audit_release.py
python3 scripts/check_clean_cpu.py --report internal/clean_cpu_check.json
```

모델 없이 공개 입력을 준비하는 명령도 별도로 제공한다. Python 명령이 `python`인 환경에서는 위의 `python3`를 바꿔 사용한다.

```bash
python scripts/prepare_demo.py --profile decel --output local/demo
```

stage한 내용만 검사하려면 `--staged`를 추가한다. 이 경우 stage하지 않은 변경과 새 파일은 포함되지 않는다. Git index와 작업 파일은 도구가 수정하지 않는다. staged export에는 안전한 tar 필터를 지원하는 Python 3.12 이상을 권장한다.

Action 예시는 camera +Z 방향의 직선 계획이며 회전은 항등이다. 생성된 숫자의 이동량·형식을 검사한 것으로, 측정 pose GT나 영상 모델의 속도 추종 평가에 해당하지 않는다.
