# Nano LoRA Study Status

최종 갱신: 2026-08-05

## 현재 단계

**BridgeData2 기반 실험적 Nano-LoRA 기술 검증 완료, 철도 데이터 실험 설계 단계**

## 완료

- 2×DGX Spark 분산 통신 및 FSDP 학습 경로 확인
- 공식 Nano full-SFT 파생 recipe의 GB10 실행 특성 확인
- 실험적 Nano-LoRA 3→4→10→100-step 저장·재시작 확인
- optimizer가 288개 LoRA tensor만 선택함을 확인
- 15,335,424개 LoRA parameter 학습 및 base-weight 고정 확인
- Base·10-step·100-step에 동일한 3개 입력을 사용한 영상 생성

## 실패·부분 완료

- 공식 compile 설정은 kernel 요구 shared memory 229,520 B가 GB10 한계 101,376 B를 넘어 실패했다.
- compile을 끈 full-SFT는 update 9회까지 완료했고 10번째 backward 이후 checkpoint 저장 전에 중단됐다.
- 따라서 full-SFT 10-step 완료 및 checkpoint 성공으로 판정하지 않는다.

## 미실시

- 철도 데이터 post-training
- LoRA와 full-SFT의 동일조건 속도·peak-memory benchmark
- 전문가 평가 또는 downstream 철도 위험물 탐지 평가
- 학습으로 인한 생성 품질 향상 입증

## 다음 게이트

1. Unitree 정상 순찰 원본과 사용 권한을 확보한다.
2. 기상 변화와 선로 침입 위험물 taxonomy를 확정한다.
3. 소량 Video-to-Video 학습·검증 split을 고정한다.
4. 동일조건 자원 benchmark와 전문가 정성평가표를 준비한다.
5. smoke → 소량 과적합 → held-out 평가 순으로 진행한다.
