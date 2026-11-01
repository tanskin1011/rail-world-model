# 최종 Nano B 가중치로 영상 생성

현재 Spark의 기존 venv·native Cosmos Framework·최종 FD_joint300 DCP·LoRA 설정을 연결했다. 재학습이나 체크포인트 변환은 하지 않는다. 실제 연결 경로는 Git 제외 `internal/runtime.json`에만 있다.

## 1. 입력

- **이미지:** RGB PNG, 정확히 832×480. 자동 crop/resize 없음.
- **Action:** JSON 배열, 188행×9열. 프레임마다 카메라 기준 상대 이동3 + 회전 첫 두 열6.
- **Prompt:** 장면 설명을 적은 UTF-8 텍스트. 생략하면 짧은 기본 장면 설명을 사용한다. 주행 조건은 Action으로 준다.
- **출력:** 아직 존재하지 않는 폴더. 덮어쓰기·자동 재개 없음.

```bash
cd rail-world-model

# 검사만: 모델 로딩·GPU 초기화·영상 생성 없음
python3 infer.py --image /path/to/input.png --action /path/to/action.json \
  --prompt-file /path/to/prompt.txt --output outputs/my_run --check

# 실제 생성: 같은 인자에서 --check를 --run으로 변경
python3 infer.py --image /path/to/input.png --action /path/to/action.json \
  --prompt-file /path/to/prompt.txt --output outputs/my_run --run
```

`/path/to/...`는 실제 파일로 바꾸는 예시다. 현재 Spark의 바로 실행할 수 있는 기존 입력 명령은 Git 제외 `internal/EXAMPLE_COMMANDS.md`에 있다.

## 2. 상태·로그·중단

`--run`이 출력하는 `job_dir` 값을 사용한다. 태스크는 연결이 끊겨도 유지되는 virtualenv runner로 제출된다.

```bash
python3 infer.py --status /absolute/path/to/job_dir
python3 infer.py --logs /absolute/path/to/job_dir
python3 infer.py --cancel /absolute/path/to/job_dir
```

실행 시각에 다른 GPU 계산 작업이 있으면 시작하지 않는다. 기존에 검증한 원격 데스크톱 프로그램만 감시 도구의 고정 binary 검증을 거쳐 구분한다. 모르는 프로세스를 종료하지 않는다. RAM 48GiB 안전선·swap 증가 1GiB 등 기존 자원 감시 정책을 유지한다. 최초 자원 센서 확인에 약 1분이 걸린다.

## 3. 고정 조건과 결과

189프레임·24 FPS·832×480, seed401(선택 변경 가능), UniPC 30 steps, guidance1, shift10. 첫 영상 프레임 `[0]`, camera domain2, Action188개 전체 조건. Prompt upsampling·음성·다운로드·학습 없음.

- `video/vision.mp4`: 생성 영상
- `video/sample_args.json`: 실제 유효 추론 조건
- `request.json`: 입력·설정·SHA-256
- `WEIGHTS_VERIFIED.json`: 로드 후 1,097개 텐서의 최종 B 해시 대조
- `CONDITIONING_VERIFIED.json`: 실제 native batch의 조건 위치·Action shape
- `RESULT.json`: 프레임 수·FPS·전체 디코딩 검사, 기술적 완료만 의미
- `worker.stdout.log`, `worker.stderr.log`, `resources.jsonl`: 실행·자원 기록
- `ERROR.json`: 실패 이유. 실패 시 자동 재시도·규격 축소 없음

## 검증 수준

새 CLI의 CPU 검사, 실제 기존 입력, 토큰 잘림 없음, Action 계약 및 단위 테스트를 확인했다. 이어 기존 첫 이미지와 정속10 Action으로 GPU end-to-end 실행 1회를 수행했고, 최종 가중치 대조·생성·MP4 전체 디코딩까지 종료코드 0으로 통과했다. [검증 범위](CLI_VERIFICATION.md)를 참고한다. 임의의 모든 새 입력에 대한 성공이나 정확한 속도 재현을 보장하는 결과는 아니다.

현재는 **이 Spark의 기존 자산을 연결한 CLI**다. compact DCP가 원래 frozen base shard를 참조하므로 iter300 폴더 하나만 다른 PC로 복사해도 작동하는 독립 모델 패키지는 아니다. 다른 PC에서는 원본 모델·VAE·tokenizer·프레임워크·자원 감시/TAO 도구를 갖추고 새 로컬 runtime profile을 작성해야 한다.
