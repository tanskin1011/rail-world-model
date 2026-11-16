# Rail World Model 프로젝트 구조

프로젝트 이름은 Rail World Model, Python 패키지는 `rail_world_model`이다. 기반 모델은 NVIDIA Cosmos3-Nano이며 A/B는 데이터 혼합 방식의 비교 실험을 가리킨다.

```text
rail-world-model/
├── infer.py
├── src/rail_world_model/       # CLI·Action 처리·실행 코드
├── configs/
│   ├── rail_world_model_protocol.json
│   └── runtime.example.json
├── tests/
├── docs/
├── assets/                    # 공개 검토된 대표 결과
├── local/                     # 로컬 연구 자산, Git 제외
│   ├── data/                  # 영상·Action·학습 목록
│   ├── src/training/          # 기존 학습 코드 보관본
│   ├── configs/               # 기존 기본 recipe
│   ├── checkpoints/final/     # 최종 체크포인트 연결
│   ├── inputs/
│   ├── outputs/
│   └── scripts/
└── internal/                  # 장비별 실행 설정, Git 제외
    ├── runtime.json
    ├── model_config.json
    ├── weights_fd500.json     # 현재 최종 모델 텐서 해시
    └── weights_manifest.json  # 이전300step 검증 기록
```

`internal/runtime.json`이 실제 체크포인트와 모델 설정·가중치 검증 목록을 연결한다. 현재 기본 설정은 `weights_fd500.json`을 사용한다. 새 장비에서 복원한 모델은 `scripts/create_runtime.py`로 별도 설정 파일에 연결한다. 모델 가중치 자체는 기존 원본을 사용한다. `local/configs/`의 기본 TOML은 최종 실행 설정 전체가 아니며, 실제 학습 기록의 `RUN_SPEC` 및 Python compose를 함께 확인한다.

과거 경로의 호환 링크와 원본 실험 이름은 기존 기록의 재현을 위해 보존한다. `nano` 호환 링크는 Git에서 제외하고 파일 관리자에서도 숨긴다. 새 문서·코드에서는 `local/`을 사용한다.

`local/`, `internal/`, 체크포인트와 원천 데이터는 GitHub 배포에서 제외한다.

공개 전 `python3 scripts/audit_release.py`로 현재 파일을 검사한다. 새 파일·이름 변경도 포함하며, 내부 경로·과대 파일·배포 대상 밖 문서 링크를 찾는다. 장비 내부 전달 설명은 Git 제외 `internal/INTERNAL_DELIVERY.md`에서 별도로 보관한다.
