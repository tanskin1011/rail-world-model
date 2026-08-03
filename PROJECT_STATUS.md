# Cosmos 3 Nano 철도 도메인 LoRA Post-Training 검토

최종 갱신: 2026-07-31

## 프로젝트 목표

`cosmos-framework`를 사용하여 Cosmos 3 Nano에 LoRA 기반 post-training을
적용할 수 있는지 검증한다. 기술적 가능성이 확인되면 철도 영상·이미지와
관련 질의응답 데이터를 이용해 철도 도메인 특화 모델로 확장하는 것을
장기 목표로 삼는다.

## 배경과 현재 가설

- NVIDIA의 공개 예제와 문서만으로는 Cosmos 3 Nano의 LoRA 지원 여부가
  명확하지 않은 것으로 보인다. 이 내용은 아직 공식 지원 불가로 확정하지
  않았으며 추가 확인이 필요하다.
- Nano SFT 설정에 `lora_enabled = true`를 추가한 시험 실행은 현재까지
  성공적으로 진행되는 것으로 관찰됐다.
- 실행이 오류 없이 끝나는 것만으로 LoRA 지원이 입증되지는 않는다.
  LoRA 모듈 삽입, 학습 대상 파라미터, gradient, optimizer, 체크포인트
  저장 및 재로딩을 별도로 검증해야 한다.

## 현재 실험 파일

- 실행 스크립트:
  `examples/launch_sft_vision_nano_lora_test.sh`
- 실험 설정:
  `examples/toml/sft_config/vision_sft_nano_lora_test.toml`
- 기본 실험:
  `job.experiment = "vision_sft_nano"`
- 현재 LoRA 설정:
  `model.lora_enabled = true`
- optimizer 선택 기준:
  `optimizer.keys_to_select = ["lora_"]`
- base checkpoint 로딩 시 제외 키:
  `checkpoint.keys_to_skip_loading = ["net_ema.", "lora_"]`
- 현재 smoke-test 길이:
  `trainer.max_iter = 10`

위 두 실험 파일은 2026-07-31 기준 Git에 아직 추가되지 않은 상태다.

## 현재 단계

상태: **기술 가능성 검증 중**

현재까지 확인된 것은 Nano용 LoRA 설정을 활성화했을 때 학습 실행이
진행되는 듯하다는 점이다. LoRA가 실제로 적용되고 저장·복원되는지는 아직
검증 완료로 기록하지 않는다.

## 필수 검증 항목

- [ ] LoRA 어댑터가 의도한 모델 레이어에 실제 삽입되는지 확인
- [ ] 전체 파라미터 수와 학습 가능 파라미터 수 기록
- [ ] base model 파라미터가 동결됐는지 확인
- [ ] 학습 가능 파라미터 이름이 LoRA 파라미터로 제한되는지 확인
- [ ] optimizer가 LoRA 파라미터만 포함하는지 확인
- [ ] LoRA 파라미터에 유효한 gradient가 발생하는지 확인
- [ ] 학습 중 loss가 정상적으로 변화하는지 확인
- [ ] LoRA 어댑터 가중치가 체크포인트에 저장되는지 확인
- [ ] 새 프로세스에서 base model과 어댑터를 다시 로드할 수 있는지 확인
- [ ] 재로딩 후 학습 직후와 동일한 출력을 재현하는지 확인
- [ ] 동일 입력에서 base model과 LoRA 모델의 출력 차이 확인

## 권장 최소 검증 실험

1. 철도 도메인의 소규모 이미지·영상 및 질의응답 데이터 20~100개를
   준비한다.
2. 고정된 seed와 입력 프롬프트로 base model의 기준 출력을 저장한다.
3. 작은 데이터에 의도적으로 과적합할 수 있을 정도로 LoRA 학습을 수행한다.
4. loss, trainable parameter 목록, gradient norm과 체크포인트 키를 기록한다.
5. 학습 프로세스를 종료하고 새 프로세스에서 base model과 LoRA 어댑터를
   다시 로드한다.
6. 동일한 평가 입력으로 base model, 학습 직후 LoRA 모델, 재로딩한 LoRA
   모델을 비교한다.

소규모 데이터에도 적응하지 못하면 LoRA 연결, 학습 대상 선택, loss 또는
데이터 파이프라인을 우선 점검한다. 과적합과 재로딩 재현에 성공하면
철도 도메인 post-training 실험으로 확장한다.

## 철도 도메인 확장 시 평가 방향

- 철도 시설물, 선로, 차량 및 작업 상황 인식
- 철도 안전 관련 상황과 이상 징후 설명
- 철도 전문 용어와 작업 절차에 대한 질의응답
- 일반 장면 이해 성능의 과도한 저하 여부
- 학습 데이터 밖의 노선, 차량 및 환경에 대한 일반화
- base model 대비 정량 평가와 정성 사례 비교

## 다음 작업

1. Nano 모델 생성 경로에서 `lora_enabled`가 소비되는 지점을 추적한다.
2. LoRA 대상 모듈과 trainable parameter를 출력하는 검증 코드를 마련한다.
3. 10-iteration smoke test의 로그와 체크포인트를 검사한다.
4. 저장·재로딩 round-trip 테스트를 작성한다.
5. 철도 소규모 과적합 데이터셋과 고정 평가 프롬프트를 설계한다.

## 작업 원칙

- 공식 지원 여부와 실험적으로 작동하는 기능을 구분해 기록한다.
- 실행 성공만으로 LoRA 적용 성공이라고 판단하지 않는다.
- 모든 비교 실험은 가능한 한 동일한 seed, 입력 및 평가 조건을 사용한다.
- 원본 철도 데이터는 수정하지 않고 실험용 파생 데이터와 구분한다.
- 실험 명령, 환경, 모델 체크포인트, 설정, 로그와 결과물을 재현 가능하게
  남긴다.
- 중요한 실험이 끝날 때마다 이 문서의 상태, 증거와 다음 작업을 갱신한다.
