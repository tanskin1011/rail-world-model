# FD500 가중치 배포 준비

현재 선택 모델은 Rail World Model FD500이다. FD300에서 200 updates를 이어 학습했으며 생성부 LoRA와 카메라 입력부 일부를 포함한다. 일반 PEFT `adapter_model.safetensors` 형식이 아니라 native Cosmos Framework DCP의 추론용 delta 묶음이다.

가중치는 로컬 후보로 준비했으며 아직 업로드하지 않았다. Hugging Face 업로드에는 쓰기 권한이 있는 계정 연결이 필요하다. 공개 조건 확인 전에는 비공개로 보관한다.

## 배포 파일과 별도 의존성

| 묶음에 포함 | 사용자가 별도로 준비 |
|---|---|
| 학습된 delta 가중치 | 해시가 일치하는 원본 Cosmos3-Nano Base DCP shard 6개 |
| 경로 없는 metadata recipe·모델 설정 템플릿 | Wan VAE·tokenizer |
| 전체 1,097개 텐서 해시·파일 SHA-256 | 호환 native Cosmos Framework·PyTorch 2.10.x |
| 복원 도구·모델 설명 | 실제 GPU 실행 시 TAO·자원 감시 도구와 로컬 runtime profile |

모델 묶음만 받아 바로 실행하는 독립 모델은 아니다. 최신 Hugging Face safetensors를 이름만 바꿔 Base DCP로 사용할 수 없다. 현재 묶음은 기존 학습에 사용한 정확한 Base DCP 파일을 요구한다.

## 복원

모델 묶음의 `manifest.json`과 SHA-256 목록을 확인한 뒤, 저장소 루트에서 실행한다. 출력은 새 폴더를 지정한다.

```bash
CUDA_VISIBLE_DEVICES='' python3 scripts/restore_weights.py \
  --bundle /path/to/rail-world-model-fd500-bundle \
  --base-model /path/to/Cosmos3-Nano/model \
  --vae /path/to/Wan2.2_VAE.pth \
  --tokenizer /path/to/tokenizer \
  --output /path/to/new-fd500-profile \
  --verify-tensors
```

Base 파일을 해시로 대조하고, 새 `checkpoint/model/.metadata`를 생성한다. 원본 체크포인트와 Base는 수정하지 않는다. `--verify-tensors`는 CPU에서 전체 가중치 값을 읽어 1,097개 텐서 해시를 대조하며 학습·forward·영상 생성을 실행하지 않는다.

복원 결과의 `checkpoint`, `model_config.json`, `weights_manifest.json`을 로컬 runtime profile에 연결한다. 나머지 실행 경로는 [추론 안내](INFERENCE.md)를 참고한다. 복원한 체크포인트에는 optimizer·scheduler 상태가 없으므로 학습 재개용으로 사용하지 않는다.

## 공개 전 확인

외부 업로드 전에는 원래 취득한 기반 모델의 정확한 버전·라이선스 고지와 기관의 가중치 공개 권한을 확인해야 한다. 현재 [NVIDIA 모델 카드](https://huggingface.co/nvidia/Cosmos3-Nano)는 [OpenMDW-1.1](https://openmdw.ai/license/1-1/)을 안내하지만, 이 정보만으로 과거 다운로드 파일에 적용된 조건까지 확정하지 않는다.

이 저장소는 가중치에 새 라이선스를 부여하지 않는다. 로컬 배포 후보 준비와 외부 업로드는 별도 단계다.
