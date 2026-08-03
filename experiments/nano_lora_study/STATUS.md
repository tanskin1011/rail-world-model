# Nano LoRA Study Status

최종 갱신: 2026-07-31

## 상태

**2-node 실제 학습 전, 설정 검증 완료**

박사님 지시에 따라 NVIDIA 공식 Nano full-SFT를 먼저 재현하고 그 결과를
실험적 Nano-LoRA와 비교한다.

## 준비된 실험

- 실험 A: 공식 Nano full-SFT 파생 10-step smoke test
- 실험 B: 동일 데이터·체크포인트의 Nano-LoRA 10-step smoke test
- 두 설정 모두 `cosmos_framework.scripts.train --dryrun` 통과
- NVIDIA 원본 recipe는 수정하지 않음

## 현재 노드 환경

- Host: `spark-fc00`
- Git commit: `f734253f0f6af3e268372402f44435c38f55ef3e`
- GPU: NVIDIA GB10
- Driver: 580.126.09
- PyTorch: 2.10.0+cu130
- CUDA runtime: 13.0
- NCCL: 2.28.9

PyTorch는 GB10 compute capability 12.1에 대해 컴파일 지원 범위가 12.0까지라는
경고를 출력한다. 기본 CUDA tensor 연산은 통과했지만 custom CUDA kernel
호환성은 실제 학습 smoke test에서 확인해야 한다.

## 다음 게이트

1. 두 번째 Spark에서 `check_local_inputs.sh` 실행
2. 두 노드의 commit, PyTorch, CUDA, driver와 입력 경로 비교
3. ConnectX-7 IP와 NCCL 통신 확인
4. 실험 A 실행
5. A가 통과한 뒤 실험 B 실행
6. 결과를 `RESULT_TEMPLATE.md` 형식으로 기록
