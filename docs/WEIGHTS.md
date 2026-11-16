# 모델 다운로드와 복원

현재 선택 모델은 Rail World Model FD500이다. FD300에서 200 updates를 이어 학습했으며 생성부 LoRA와 카메라 입력부 일부를 포함한다. 일반 PEFT `adapter_model.safetensors` 형식이 아니라 native Cosmos Framework DCP의 추론용 delta 묶음이다.

가중치와 실행 소스는 [Hugging Face](https://huggingface.co/tanskin02/rail-world-model-camera-500step)에서 공개한다. 로그인이나 접근 승인 없이 내려받을 수 있다.

## 다운로드·파일 검사

Hugging Face CLI를 설치한 뒤 프로젝트 루트에서 실행한다. 공개 파일 다운로드에는 토큰이 필요 없다.

```bash
hf download tanskin02/rail-world-model-camera-500step \
  --revision 379bea5f3a00a51a1aaea402bc774a4e27669f37 \
  --local-dir local/artifacts/camera-500step

python3 scripts/prepare_artifacts.py \
  --artifacts local/artifacts/camera-500step \
  --support-output local/runtime_sources
```

모델 자료는 약34.4GB. 첫 명령은 고정 버전의 파일을 내려받고, 두 번째 명령은 SHA-256을 확인한 뒤 실행 소스를 새 폴더에 푼다. 완료 시 `ARTIFACTS_VERIFIED` 출력. 이미 압축을 푼 경우 `--support-output`을 빼면 파일 검사만 수행한다.

`local/runtime_sources/runtime_support/` 아래의 `native_framework`, `guard_sources`, `inventory_sources`, `tao_skill_bank`가 추론에 사용하는 코드다. `local/runtime_sources/ENVIRONMENT.json`에는 기존 환경의 Python·패키지 버전을 기록했다.

## 배포 파일과 별도 의존성

| Hugging Face 보관 내용 | 새 장비에서 준비할 내용 |
|---|---|
| 학습된 delta·Base DCP shard 6개 | CUDA 지원 NVIDIA GPU·충분한 메모리·디스크 공간 |
| metadata recipe·모델 설정 템플릿·VAE·tokenizer | PyTorch 2.10.x를 사용하는 호환 Python 환경 |
| 전체 1,097개 텐서 해시·파일 SHA-256 | 압축에 들어 있는 Framework의 의존 패키지 설치 |
| 복원 코드·Framework·TAO runner·자원 감시 소스 | 새 장비 경로를 담은 runtime profile |

저장된 파일은 기존 Spark의 원본 경로에 접근하지 않고 복원할 수 있도록 구성했다. 기반 DCP는 `base/model/`, 변경 가중치는 `model_bundle/`에 있다. 다른 기반 가중치로 바꾸면 해시 검사를 통과하지 못한다.

## 실행 환경 설치

기존 환경은 Linux aarch64·Python3.13.12·PyTorch2.10.0+cu130·torchvision0.25.0+cu130·Framework1.2.2. 다운로드한 Framework의 `docs/setup.md`, `pyproject.toml`과 `ENVIRONMENT.json`을 기준으로 새 GPU와 CUDA에 맞는 환경을 설치한다. FFmpeg도 설치하고 실행 파일 경로를 확인한다.

Framework의 설치 명령은 다음과 같다. 프로젝트 저장소가 아닌, 압축을 푼 **Framework 폴더**에서 실행한다.

```bash
cd local/runtime_sources/runtime_support/native_framework
uv sync --all-extras --group=cu130-train
source .venv/bin/activate
export LD_LIBRARY_PATH=''
```

설치 후 Rail World Model 저장소 루트로 돌아와 아래 복원 명령을 실행한다. 이 설치 경로는 CUDA13.0용이며, 새 장비의 의존 패키지 설치·GPU 실행은 별도 확인이 필요하다. 다른 CUDA 구성은 함께 보관한 `docs/setup.md` 참조. `runtime_support.zip`에는 설치된 가상환경이나 패키지 lock 전체가 포함돼 있지 않다.

## 복원

모델 묶음의 `manifest.json`과 SHA-256 목록을 확인한 뒤, 저장소 루트에서 실행한다. 출력은 새 폴더를 지정한다.

```bash
CUDA_VISIBLE_DEVICES='' python scripts/restore_weights.py \
  --bundle local/artifacts/camera-500step/model_bundle \
  --base-model local/artifacts/camera-500step/base/model \
  --vae local/artifacts/camera-500step/vae/Wan2.2_VAE.pth \
  --tokenizer local/artifacts/camera-500step/tokenizer \
  --output local/model_profiles/camera-500step \
  --verify-tensors
```

Base 파일을 해시로 대조하고, 새 `checkpoint/model/.metadata`를 생성한다. 원본 체크포인트와 Base는 수정하지 않는다. `--verify-tensors`는 CPU에서 전체 가중치 값을 읽어 1,097개 텐서 해시를 대조하며 학습·forward·영상 생성을 실행하지 않는다.

복원 결과의 `checkpoint`, `model_config.json`, `weights_manifest.json`을 로컬 실행 설정에 연결한다. 복원한 체크포인트는 영상 추론용이며 optimizer·scheduler 상태는 포함하지 않는다.

## 새 장비의 실행 경로 연결

아래 명령도 프로젝트 루트에서 실행한다. `--python`은 Framework 환경의 Python, `--ffmpeg`는 설치한 FFmpeg 실행 파일 경로. 나머지는 위에서 내려받고 복원한 폴더다. 기존 설정을 보존하도록 `--output`에는 새 파일명을 사용한다.

```bash
python3 scripts/create_runtime.py \
  --model-profile local/model_profiles/camera-500step \
  --python local/runtime_sources/runtime_support/native_framework/.venv/bin/python \
  --framework local/runtime_sources/runtime_support/native_framework \
  --base-checkpoint local/artifacts/camera-500step/base \
  --ffmpeg /path/to/ffmpeg \
  --guard-sources local/runtime_sources/runtime_support/guard_sources \
  --inventory-sources local/runtime_sources/runtime_support/inventory_sources \
  --bank local/runtime_sources/runtime_support/tao_skill_bank \
  --output internal/runtime_500step.json

python3 infer.py --runtime internal/runtime_500step.json \
  --image input.png --action action.json --prompt-file scene.txt \
  --output outputs/first_run --check
```

설정 생성 도구는 파일·도우미 모듈·기반 가중치 참조를 검사한다. 이후 `infer.py --check`에서 native 입력을 확인하고, 실제 생성할 때 `--run`으로 바꾼다. 입력 이미지·Action·프롬프트 준비는 [영상 추론](INFERENCE.md) 참조.

## 이용 조건

기반 모델과 외부 소프트웨어의 원래 이용 조건을 유지한다. [NVIDIA 모델 카드](https://huggingface.co/nvidia/Cosmos3-Nano)와 함께 보관한 라이선스 고지를 확인한다. 재배포 시에는 자료별 적용 조건을 확인한다.

`model_bundle/` 안의 권리 검토 문서는 배포 묶음을 준비한 시점의 기록이다. 현재 저장소의 공개 상태와 다운로드 방법은 이 문서와 Hugging Face 저장소 설명을 기준으로 확인한다.
