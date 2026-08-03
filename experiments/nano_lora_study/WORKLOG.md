# Cosmos3-Nano Post-training Worklog

최종 갱신: 2026-07-31

## 목적과 현재 판정

NVIDIA 공식 Cosmos3-Nano full-SFT를 먼저 기준선으로 재현하고, 이후 실험적 Nano-LoRA의 타당성과 효율을 동일 조건에서 비교한다.

- 학습 가능성: 확인
- 2-node FSDP/NCCL 통신: 확인
- 10-step 완주 및 checkpoint 저장: 미확인
- 공식 `torch.compile` 설정: 현재 GB10에서 실패
- GB10 호환 실행: `model.config.compile.enabled=false` 필요
- Nano-LoRA 실제 학습 정확성: 아직 미검증

두 DGX Spark에서 full-SFT는 optimizer update까지 작동했다. Compile을 끈 실행은 9 iteration을 완료하고 10번째 backward까지 도달했으나, 터미널/원격 세션 이상 이후 checkpoint 저장 전에 종료됐다. Full-SFT는 장기 학습안 확정보다 Nano-LoRA 비교 기준선으로 사용한다.

## 실험 환경

| 구분 | Rank 0 | Rank 1 |
| --- | --- | --- |
| Host | `spark-fc00` | `spark-f64e` |
| GPU | NVIDIA GB10 | NVIDIA GB10 |
| Driver | 580.126.09 | 580.126.09 |
| PyTorch | 2.10.0+cu130 | 2.10.0+cu130 |
| CUDA runtime | 13.0 | 13.0 |
| NCCL | 2.28.9 | 2.28.9 |
| Git commit/source | `f734253f0f6af3e268372402f44435c38f55ef3e` | 동일 source 복제 |

- ConnectX-7 IP: rank 0 `169.254.70.245`, rank 1 `169.254.33.231`
- `NCCL_SOCKET_IFNAME=enp1s0f1np1`
- NCCL 로그에서 `NET/IB`, `rocep1s0f1`, `roceP2p1s0f1` 사용 확인
- NCCL `all_reduce`: 양 rank 모두 `3.0 PASS`

입력 무결성:

| 입력 | 검증값 | 양 노드 일치 |
| --- | --- | --- |
| BridgeData2 manifest SHA-256 | `67955a402ba68de2686d7c139df96c144c9774fc83fb742600aa0b042b86ca76` | 예 |
| Wan2.2 VAE SHA-256 | `20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36` | 예 |
| Cosmos3-Nano checkpoint 크기 | 31,502,248,722 bytes | 예 |

## 기준선 설정

- Launcher: `examples/launch_sft_vision_nano_official_smoke.sh`
- TOML: `examples/toml/sft_config/vision_sft_nano_official_smoke.toml`
- 공식 recipe 대비 실험 식별자, `max_iter: 500 -> 10`, `save_iter: 100 -> 10` 변경
- LoRA 비활성화 상태의 full-SFT
- 실제 실행 전 `--dryrun` 통과

## 실행 이력

### 시도 1 — 원격 `ffprobe` 누락

분산 초기화와 data manifest 읽기까지 성공했으나 rank 1 DataLoader에서 `ffprobe`를 찾지 못했다. Rank 0의 FFmpeg runtime을 원격 project 내부 `.tools/ffprobe/`에 복제했다. OS 전역 package는 변경하지 않았다.

### 시도 2 — 원격 `ffmpeg` 누락

Metadata 조회는 통과했지만 실제 frame decode에서 `ffmpeg`가 없어 종료됐다. 동일 project bundle에 `ffmpeg`와 library를 추가하고 원격에서 FFmpeg 6.1.1 실행을 확인했다.

### 시도 3 — 공식 compile 설정의 GB10 비호환

첫 backward의 Triton kernel compile에서 실패했다.

- required shared memory: 229,520 bytes
- GB10 hardware limit: 101,376 bytes
- 근거: `outputs/nano_lora_study/official_full_sft_smoke/logs/rank0_retry2.log:1041`

이는 전체 GPU memory OOM이 아니라 개별 kernel의 shared-memory resource 초과다. `model.config.compile.enabled=false` override는 dry-run을 통과했다.

### 시도 4 — GB10 호환 full-SFT

- Checkpoint 적재: `outputs/nano_lora_study/official_full_sft_smoke/logs/rank0_gb10_no_compile.log:924`
- FSDP 학습 시작: `outputs/nano_lora_study/official_full_sft_smoke/logs/rank0_gb10_no_compile.log:927`
- Rank당 보고 parameter: 6,965,486,784
- 관찰 memory: 약 109–110 GiB/node
- 관찰 GPU utilization: 약 96%
- CUDA OOM, NaN, NCCL timeout은 관찰되지 않음

## 학습 지표

| Iteration | Loss | Grad norm (clip 전) | Time (s) | 로그 근거 |
| ---: | ---: | ---: | ---: | --- |
| 1 | 0.2477 | 0.55469 | 496.18 | rank0:940-941 |
| 2 | 0.2531 | 0.42969 | 383.35 | rank0:942-943 |
| 3 | 0.3147 | 0.47461 | 407.87 | rank0:944-945 |
| 4 | 0.2531 | 0.55078 | 441.55 | rank0:946-947 |
| 5 | 0.2245 | 0.50781 | 448.64 | rank0:948-949 |
| 6 | 0.2372 | 0.40039 | 432.42 | rank0:951-952 |
| 7 | 0.1991 | 0.56250 | 595.96 | rank0:956-957 |
| 8 | 0.2359 | 0.64844 | 485.24 | rank0:959-960 |
| 9 | 0.2190 | 0.91406 | 444.90 | rank0:962-963 |

- 완료 optimizer update: 9
- 평균 loss: 약 0.2427; 범위 0.1991–0.3147
- 평균 iteration: 약 437.35초(7.29분); 범위 383.35–595.96초
- 10번째 backward와 grad norm `0.49414`: `outputs/nano_lora_study/official_full_sft_smoke/logs/rank0_gb10_no_compile.log:965`
- 10번째 optimizer 완료 로그 및 checkpoint 없음
- 설정된 `grad_clip.clip_norm=0.1`; 표의 norm은 clipping 전 값

이 짧은 loss만으로 수렴이나 품질 향상을 주장하지 않는다.

## 중단 진단

화면/TTY가 무응답처럼 보인 뒤 재접속이 수행됐다. 이후 rank 0 학습 process는 없었고 log는 10번째 grad norm에서 끝났다. Checkpoint는 없었다. Rank 1은 ping에 응답했으나 SSH banner에서 timeout됐다.

로그에 `CUDA out of memory`, exit 137 또는 명시적 Linux OOM 기록은 없다. 따라서 현재 증거로 system memory OOM을 확정할 수 없다. TTY/SSH에 결합한 실행 방식과 rank 1 SSH 이상이 관여했을 가능성이 있으며 kernel OOM log 확인 전에는 단정하지 않는다.

## 해석과 의사결정

확인된 사실:

1. 2×DGX Spark의 FSDP와 NCCL/RoCE 경로는 작동한다.
2. Nano full-SFT는 compile off에서 반복 optimizer update가 가능하다.
3. 약 110 GiB/node와 평균 7.29분/iteration으로 비용이 높다.
4. 공식 compile 설정은 현재 GB10/PyTorch/Triton 조합에서 실패한다.
5. Checkpoint save/resume은 아직 미검증이다.

아직 주장할 수 없는 것:

1. 모델 품질 향상 또는 철도 domain 특화 성공
2. Nano-LoRA가 실제로 올바르게 학습됨
3. LoRA가 full-SFT보다 빠르거나 memory를 절감함
4. 마지막 중단이 OOM이었음

적은 철도 data의 반복 실험을 위해 Nano-LoRA의 trainable parameter, optimizer memory, checkpoint size, base-weight 불변성을 다음 단계에서 검증할 가치가 충분하다.

## 다음 실행 게이트

1. Rank 1 SSH와 kernel OOM 기록 확인
2. 양 노드 `ffmpeg`/`ffprobe` preflight 추가
3. 학습을 TTY에서 분리한 persistent runner 사용
4. Memory/GPU/kernel log 독립 수집
5. 공유 checkpoint storage 또는 DCP shard 수집 방식 확정
6. `save_iter=1` 짧은 full-SFT로 save/load/resume 검증
7. 동일 seed/data/step의 Nano-LoRA smoke
8. LoRA gradient, base-weight 불변, adapter 저장/reload 검증

## PPT용 핵심 문장

> 두 대의 DGX Spark에서 Cosmos3-Nano full-SFT의 학습 가능성은 확인했으나, GB10 compile 호환성과 약 110 GiB/node·평균 7.29분/step의 높은 비용 때문에 철도 소량 데이터 적용에는 Nano-LoRA의 정식 검증이 다음 연구 단계로 타당하다.

PPT에는 “10-step 성공” 또는 “checkpoint 생성 성공”으로 표현하지 않는다. 정확한 표현은 “9 optimizer steps 완료, 10번째 backward 완료 후 저장 전 중단”이다.

## Nano-LoRA 3-step 결과 (추가 기록)

- BridgeData2 기반 2-node Nano-LoRA 3/3 iteration 완료
- Loss(rank 0): 0.2459, 0.2517, 0.3107
- 매 iteration DCP checkpoint 저장 성공; latest `iter_000000003`
- Model metadata: LoRA tensor 288개, 총 15,335,424 parameters
- Iteration 1→3 local LoRA shards: 288개 중 236개 변화, max abs delta 약 5.99e-6
- Base-weight shard 표본 20개: 모두 bitwise unchanged
- Optimizer 구성 로그: total tensors 1,092, trainable/selected tensors 288, selected elements 15,335,424
- Auto-resume가 `iter_000000003`의 model/optim/scheduler/trainer를 인식함
- 전체 재적재는 노드별 로컬 filesystem에 DCP shard가 분리된 상태와 반복 RoCE GID 변경 경고 속에서 정체되어 중단함
- 판정: LoRA 주입·선택 학습·weight 변화·저장은 확인; 완전한 reload는 공유/통합 checkpoint storage 구성 후 재검증 필요
