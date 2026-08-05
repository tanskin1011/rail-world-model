# Windows Codex Handoff

최종 갱신: 2026-08-05

## Windows Codex에 전달할 첫 요청

> 이 저장소의 `experiments/nano_lora_study/HANDOFF.md`, `STATUS.md`, `RESULTS.md`, `RESEARCH_PLAN.md`, `WORKLOG.md`를 순서대로 읽고 Cosmos3-Nano 철도 LoRA 연구의 현재 상태를 파악해줘. 기존 결과를 공식 NVIDIA Nano-LoRA 지원이나 철도 특화 성공으로 과장하지 말고, 다음 작업은 `RESEARCH_PLAN.md`의 1차 목표를 기준으로 제안해줘.

## 프로젝트 목적

Cosmos3-Nano를 Unitree Go2-W/A2 철도 순찰용 합성 데이터 생성기로 post-training할 가능성을 연구한다.

1차 생성 목표:

- 비·안개·눈·야간 등 기상 변화
- 사람·고라니·낙석 등 철로 침입 위험물

## 지금까지 완료

- 2×DGX Spark cluster 및 NCCL/RoCE 검증
- BridgeData2 기반 실험적 Nano-LoRA 100-step 완료
- LoRA-only update 및 base-weight freeze 확인
- DCP save/resume: 3→4→10→100 steps 확인
- Base/10/100 고정 프롬프트 영상 각 3개 생성
- full-SFT 원본 9개 iteration 평균 459.57초로 정정
- LoRA optimizer 15,335,424 elements(로그상 full-SFT 대비 약 0.220%) 확인

## 중요한 판단

- NVIDIA 공식 Nano-LoRA recipe가 아니다.
- 기술적 실행 가능성은 확인했지만 철도 domain 학습은 아직 시작하지 않았다.
- 10-step 결과는 Base와 매우 유사하며 100-step은 더 크게 변하지만, 변화가 품질 향상을 뜻하지는 않는다.
- full-SFT 약 109–110 GiB/node는 수동 관찰값이고 LoRA peak-memory 기록은 없어 메모리 비교 불가
- 기존 raw step time 차이는 동일조건 benchmark가 아니므로 속도 향상으로 주장하지 않는다.
- 철도 합성의 우선 방법은 실제 Unitree 정상 순찰 영상을 조건으로 하는 Video-to-Video다.
- Reasoner는 자동 ground truth 생성기가 아니라 생성 조건 충족과 물리 타당성의 보조 검사기로 사용한다.
- Unitree action/policy는 embodiment-specific 동기화 데이터와 안전 검증 전에는 실제 제어에 연결하지 않는다.

## 주요 경로

```text
Recipe:
examples/toml/sft_config/vision_sft_nano_lora_smoke.toml

Training logs:
outputs/nano_lora_study/nano_lora_3step/logs/rank0_to10.log
outputs/nano_lora_study/nano_lora_3step/logs/rank0_to100.log

Evaluation input:
experiments/nano_lora_study/eval/bridge_fixed_t2v.jsonl

Evaluation outputs:
outputs/nano_lora_study/eval/base/
outputs/nano_lora_study/eval/step10/
outputs/nano_lora_study/eval/step100/
```

`outputs/`는 Git에 포함하지 않는다. Windows에서 영상을 보려면 별도 파일 전송이 필요하다.

## 다음 작업 후보

1. Unitree 실제 정상 순찰 영상 수집 규격 정의
2. 철도 시나리오 taxonomy와 구조화 metadata schema 확정
3. Video-to-Video 최소 데이터 실험 설계
4. 전문가 정성 평가표 작성
5. 합성 데이터의 downstream 위험물 탐지 효과 평가 설계

## Git 공유 주의

- Private 저장소 사용을 권장한다.
- checkpoint와 생성 영상은 Git에 넣지 않는다.
- 자격 증명과 SSH key를 commit하지 않는다.
- 문서와 recipe만 Git으로 공유하고 대용량 산출물은 별도 전송한다.
