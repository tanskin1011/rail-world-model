# Cosmos3-Nano Full-SFT / Experimental LoRA Feasibility Study

> 현재 결과 요약은 `STATUS.md`와 `RESULTS.md`, 다음 철도 실험은 `RESEARCH_PLAN.md`를 우선 확인한다.
> 기존 실행은 동일조건 자원 benchmark가 아니므로 속도·메모리 효율 비교로 해석하지 않는다.

NVIDIA 공식 Nano full-SFT 파생 기준선과 실험적 Nano-LoRA의 실행·검증 절차를 기록한 운영 문서다.

## 실험

| ID | Recipe | 목적 | 성격 |
| --- | --- | --- | --- |
| A | `vision_sft_nano_official_smoke` | 공식 Nano full-SFT 10-step 기준선 | 공식 레시피의 최소 변경 파생본 |
| B | `vision_sft_nano_lora_smoke` | Nano LoRA 삽입·학습·저장 검증 | 실험적 |

두 실험 모두 NVIDIA BridgeData2 subset, Cosmos3-Nano DCP checkpoint,
Wan2.2 VAE를 사용했다. 최초 계획에서는 A 통과 후 B를 실행하려 했으나, 실제로 A는 9 update 후 중단됐고 B는 별도 기술 검증으로 100-step까지 완료됐다.

## 파일 배치

```text
examples/
├── launch_sft_vision_nano_official_smoke.sh
├── launch_sft_vision_nano_lora_smoke.sh
└── toml/sft_config/
    ├── vision_sft_nano_official_smoke.toml
    └── vision_sft_nano_lora_smoke.toml

experiments/nano_lora_study/
├── README.md
├── cluster.env.example
└── check_local_inputs.sh

outputs/nano_lora_study/                 # Git ignored
├── official_full_sft_smoke/
└── nano_lora_smoke/
```

## 1. 각 노드 입력 및 환경 확인

각 Spark의 repository root에서 실행한다.

```bash
bash experiments/nano_lora_study/check_local_inputs.sh
```

두 출력에서 Git commit, Python, PyTorch, CUDA, driver와 입력 경로가
일치해야 한다.

## 2. 클러스터 환경 설정

두 노드에서 예제 파일을 복사하고 `MASTER_ADDR`를 rank 0 Spark의
ConnectX-7 IP로 변경한다.

```bash
cp experiments/nano_lora_study/cluster.env.example \
   experiments/nano_lora_study/cluster.env
set -a
source experiments/nano_lora_study/cluster.env
set +a
```

각 노드에서 rank만 별도로 지정한다.

```bash
# 첫 번째 Spark
export NODE_RANK=0

# 두 번째 Spark
export NODE_RANK=1
```

## 3. 설정 dry-run

실제 학습 없이 각 recipe 구조를 검증한다. 한 노드에서만 수행한다.

```bash
export DATASET_PATH="$PWD/examples/data/BridgeData2-Subset-Synthetic-Captions/sft_dataset_bridge"
export BASE_CHECKPOINT_PATH="$PWD/examples/checkpoints/Cosmos3-Nano"
export WAN_VAE_PATH="$PWD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth"
export IMAGINAIRE_OUTPUT_ROOT="$PWD/outputs/nano_lora_study/dryrun"
export LD_LIBRARY_PATH=

python -m cosmos_framework.scripts.train \
  --sft-toml=examples/toml/sft_config/vision_sft_nano_official_smoke.toml \
  --dryrun

python -m cosmos_framework.scripts.train \
  --sft-toml=examples/toml/sft_config/vision_sft_nano_lora_smoke.toml \
  --dryrun
```

## 4. 실험 A: 공식 Nano full-SFT smoke

두 노드에서 cluster 환경과 각자의 `NODE_RANK`를 설정한 뒤 거의 동시에
실행한다.

```bash
bash examples/launch_sft_vision_nano_official_smoke.sh
```

성공 기준:

- 두 rank가 FSDP process group에 참가한다.
- 10 iteration이 완료된다.
- loss가 유한한 값으로 기록된다.
- iteration 10 checkpoint가 생성된다.
- OOM 또는 NCCL 오류가 없다.

## 5. 실험 B: Nano-LoRA smoke

실험 A가 통과한 뒤 동일한 cluster 환경에서 실행한다.

```bash
bash examples/launch_sft_vision_nano_lora_smoke.sh
```

실행 성공만으로 LoRA 검증이 완료되지는 않는다. 다음 증거가 필요하다.

- LoRA target module이 Nano 모델에 존재한다.
- base parameter는 동결되고 LoRA parameter만 학습 가능하다.
- optimizer parameter가 `lora_` 항목으로 제한된다.
- LoRA parameter에 유효한 gradient가 발생한다.
- checkpoint에 adapter tensor가 저장된다.
- 새 프로세스에서 adapter를 재로딩할 수 있다.

## 6. 결과 기록

각 실행 후 다음을 `PROJECT_STATUS.md`에 기록한다.

- 실행 날짜와 Git commit
- 노드별 환경 및 실제 실행 명령
- 성공·실패와 오류
- 최대 메모리와 iteration당 시간
- 시작·종료 loss
- checkpoint 경로와 크기
- 다음 판단

## 변경 통제

- NVIDIA 원본 `vision_sft_nano.toml`과 launcher는 수정하지 않는다.
- 실험 A는 원본에서 job 경로와 10-step smoke 범위만 변경한다.
- 실험 B는 공식 Super LoRA의 rank, alpha와 target modules를 Nano에 적용한다.
- 데이터, 모델, VAE와 평가 입력은 A와 B에서 동일하게 유지한다.
- 장기 학습은 두 smoke test와 LoRA 구조 검증 이후 결정한다.
