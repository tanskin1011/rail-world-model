# Cosmos3-Nano 철도 도메인 LoRA Post-Training 연구

최종 갱신: 2026-08-05

## 목표

Cosmos3-Nano를 Unitree Go2-W/A2 철도 순찰용 합성 영상 생성기로 post-training할 가능성을 검토한다.
1차 목표는 비·안개·눈·야간 등 기상 변화와 사람·고라니·낙석 등 선로 침입 위험물 영상 생성이다.

## 현재 상태

BridgeData2 예제를 이용한 **실험적 Nano-LoRA 기술 검증**까지 완료했다. 철도 데이터 학습은 아직 시작하지 않았다.

| 항목 | 판정 |
| --- | --- |
| 2×DGX Spark FSDP/NCCL/RoCE | 확인 |
| 공식 Nano full-SFT 파생 실행 | optimizer update 9회 완료; 10번째 backward 후 저장 전 중단 |
| 공식 compile 설정 | GB10 shared-memory 한계로 실패 |
| 실험적 Nano-LoRA | 100-step 완료 |
| LoRA-only optimizer 선택·base freeze | 확인 |
| DCP save/resume | 3→4→10→100 확인 |
| Base/10/100 고정 입력 추론 | 각 3개 완료 |
| 철도 특화 학습 | 미실시 |
| 동일조건 속도·메모리 비교 | 미실시 |

## 연구 판정

- 이 설정은 NVIDIA가 공식 지원하는 Nano-LoRA recipe가 아니다.
- full-SFT를 “10-step 완료” 또는 “checkpoint 저장 성공”으로 표현하지 않는다.
- 출력 변화 자체는 품질 향상의 증거가 아니다.
- LoRA의 학습 변수 감소는 확인했지만 메모리 절감 및 속도 향상은 아직 입증되지 않았다.
- 현재 결과를 철도 특화 학습 성공으로 표현하지 않는다.

## 확인된 수치

| 항목 | Nano full-SFT | 실험적 Nano-LoRA |
| --- | ---: | ---: |
| optimizer 선택 tensor | 405 | 288 |
| 로그상 optimizer element | 6,965,486,784/rank | 15,335,424 |
| 완료 update | 9 | 100 |
| 기존 로그 평균 iteration time | 459.57초 (n=9) | 310.12초 (steps 11–100, step 61 제외, n=89) |
| peak memory/node | 약 109–110 GiB 수동 관찰; telemetry 없음 | 보존된 수치·telemetry 없음 |

시간은 checkpoint 주기, EMA, 실행 구간 등이 달라 설명 통계일 뿐 인과적 속도 향상을 뜻하지 않는다.

## 문서 읽는 순서

1. `experiments/nano_lora_study/HANDOFF.md`
2. `experiments/nano_lora_study/STATUS.md`
3. `experiments/nano_lora_study/RESULTS.md`
4. `experiments/nano_lora_study/RESEARCH_PLAN.md`
5. `experiments/nano_lora_study/WORKLOG.md`

대용량 checkpoint, 원본 데이터 및 생성 영상은 `outputs/`에 있으며 Git에 포함하지 않는다.
