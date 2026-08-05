# Experimental Results

최종 갱신: 2026-08-05

## 연구 범위

BridgeData2 예제로 Cosmos3-Nano에 LoRA를 실험적으로 삽입하고 선택학습·DCP 저장·재시작·고정 입력 추론을 검증했다. NVIDIA 공식 Nano-LoRA recipe 검증이나 철도 데이터 학습 결과가 아니다.

## 공식 Nano full-SFT 파생 기준선

- 공식 설정의 compile kernel은 shared memory 229,520 B를 요구해 GB10 한계 101,376 B를 초과했다.
- compile을 끄면 optimizer update 9회가 완료됐다.
- 10번째 backward와 grad norm 기록 후 checkpoint 저장 전에 중단됐다.
- 완료된 9회 평균 iteration time은 459.57초, 중앙값은 444.90초다.
- 약 109–110 GiB/node는 당시 수동 관찰값이며 원본 memory telemetry는 보존되지 않았다.

## 실험적 Nano-LoRA

- LoRA: rank 16, alpha 32, q/k/v/o projection target.
- 144개 모듈, 15,335,424개 trainable LoRA parameter, 15,156,222,144개 frozen base parameter.
- optimizer: 전체 1,092 tensor 중 LoRA 288 tensor만 선택.
- iteration 1→3 local LoRA shard 236/288 변화, 최대 절댓값 변화 약 5.99e-6.
- base-weight sample 20/20 bitwise unchanged.
- DCP save/resume 3→4→10→100 확인.
- 100-step 완료.

LoRA shard 변화와 base sample 검증의 독립 분석 산출물은 보존되지 않아 WORKLOG 기반 2차 증거로 구분한다. optimizer 선택과 trainable parameter 수는 원본 runtime log로 확인된다.

## 자원·시간 비교

| 지표 | full-SFT | Nano-LoRA | 판정 |
| --- | ---: | ---: | --- |
| optimizer tensor | 405 | 288 | 원본 로그 확인 |
| optimizer elements | 6,965,486,784/rank | 15,335,424 | LoRA 약 0.220% |
| iteration mean | 459.57초, n=9 | 310.12초, n=89 | 설명 통계만 가능 |
| peak memory/node | 약 109–110 GiB, 수동 관찰 | 기록 없음 | 비교 불가 |

실행 구간, checkpoint 주기, EMA 및 시스템 상태가 달라 “LoRA로 빨라졌다/메모리가 절감됐다”고 주장하지 않는다.

## 생성 비교

`bridge_fixed_t2v.jsonl`의 세 입력에 대해 Base·step10·step100 총 9개 영상을 생성했다.

- seed101: BridgeData2 유사 sweeping 동작
- seed102: BridgeData2 유사 pouring 동작
- seed103: 학습에 없는 rail-themed composition 탐색

동일 prompt와 seed에서 결과가 변했지만 변화가 품질 향상을 의미하지 않는다. seed103도 철도 특화 학습 증거가 아니다.

## 현재 결론

Nano 모델 코드 경로에서 LoRA adapter만 선택해 학습하고 DCP로 100-step까지 이어갈 기술적 가능성을 확인했다. 다음 주장은 아직 불가능하다.

- NVIDIA 공식 Nano-LoRA 지원
- 철도 특화 학습 성공
- full-SFT 10-step/checkpoint 성공
- LoRA의 속도 또는 메모리 효율 향상
- 100-step 생성 품질 향상
