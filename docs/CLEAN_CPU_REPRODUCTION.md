# 비공개 자산 없는 CPU 재현 확인

포트폴리오 저장소에서 무엇을 바로 실행할 수 있는지 확인하기 위해, Git index의 소스만 별도 임시 폴더로 내보내고 새 가상환경을 만들었다. `internal/`, `outputs/`, 데이터셋, 체크포인트가 포함되지 않은 것을 검사했다.

## 확인 결과

- Python 3.13.12의 새 가상환경, pip 없이 실행.
- 외부 Python 패키지를 설치하지 않음.
- 단위 테스트 16개 통과.
- STOP / const5 / const10 / accel / decel의 설명용 직선 Action 생성 및 형식 검사 통과.
- 모델 로딩·CUDA 초기화·영상 생성 없음.

이 검사는 같은 Spark에서 **비공개 자산과 기존 Python 패키지에 의존하지 않는 CPU 기능**을 확인한 것이다. 다른 물리 장비에서 GPU 추론까지 확인한 결과가 아니다.

## 재현 명령

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

개발자는 변경사항을 stage한 후 아래 보조 검사도 실행할 수 있다. Git index를 내보내므로 작업 트리의 stage하지 않은 변경은 포함되지 않는다. 안전한 tar 필터를 지원하는 Python 3.12 이상을 권장한다. 출력 report는 새 파일명이어야 한다.

```bash
git add <검토한-파일>
python3 scripts/check_clean_cpu.py --report internal/clean_cpu_check.json
```

Action 예시는 camera +Z 방향의 직선 계획이며 회전은 항등이다. 수학적으로 계획한 이동량 비율이 다르다는 사실은 **생성 모델이 실제로 같은 속도 비율을 재현한다는 뜻이 아니다.** 측정 pose GT, 연구 데이터 추가분, 모델 평가 결과로 사용하지 않는다.
