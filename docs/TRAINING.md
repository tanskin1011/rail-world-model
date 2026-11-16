# 학습 단계와 설정

## 학습 순서

| 단계 | 입력 | 업데이트 대상 | 누적 step |
|---|---|---|---:|
| 선행 철도 적응 | 기존 철도 학습 자료 | 기존 학습 기록에 따름 | 300 |
| 영상 외관 적응 | 가상 RGB·실사 RGB·장면 캡션 | 생성 attention LoRA | 해당 단계300 |
| 카메라 경로 조건 학습 | 가상 RGB·첫 이미지·카메라 Action | 같은 LoRA + 카메라 입력부 일부 | 해당 단계300 |
| 최종 모델 학습 재개 | 같은 카메라 조건 데이터·이전 학습 상태 | 같은 학습 범위 | 300에서500으로 추가200 |

500step은 카메라 조건 학습 단계의 누적 값이다. 선행 철도 적응·영상 적응의 step은 별도로 구분한다. 학습 재개 시 기존 모델·optimizer·scheduler 상태를 이어받았다.

## 데이터 구성

| 자료 | 학습 | 검증 | 사용 |
|---|---:|---:|---|
| 가상 RGB·렌더 카메라 pose | 240 | 54 | 영상 적응·카메라 조건 학습 |
| 실사 RGB | 107 | 13 | 영상 적응 |

영상 적응의 혼합 모델은 가상:실사70:30으로 샘플링한다. 이 비율은 파일 개수 비율과 다르다. 카메라 조건 학습에는 검증된 pose가 있는 가상 데이터만 사용한다.

카메라 조건 샘플은189 RGB 프레임, 프레임 간 상대 이동·회전188개, 장면 캡션을 짝지어 구성한다. 각 Action은9차원이며 실제 모델 입력은64차원이다. 영상 FPS와 pose 시각을 맞추고 첫 이미지가 같은 영상의 첫 프레임인지 확인한다.

## 최종 학습 재개 설정

| 항목 | 기록 값 |
|---|---|
| native backend | Cosmos Framework Omni |
| 영상 | 832×480 · 189프레임 · 24FPS |
| 시작·종료 | 300 → 500step |
| 추가 업데이트 | 200 |
| peak learning rate | 0.0001 |
| 설정된 warmup·scheduler horizon | 10 · 500 |
| LoRA | rank16 · alpha32 |
| 카메라 입력부 | domain2·원래9채널·해당 bias |
| 실행 형태 | 단일 노드·단일 GPU native torch.distributed.run |

재개 설정의 warmup·horizon과 실제 재개 시점의 학습률은 구분한다. 전체 optimizer·scheduler 상태를 이어받았으므로 위 값만으로 새 optimizer를 만들면 같은 학습이 되지 않는다.

## 학습을 이어서 구현할 때 필요한 파일

1. 학습 영상·캡션·Action과 학습/검증 목록
2. 데이터 loader, 카메라 입력부 gradient mask, native config를 만드는 코드
3. 시작 checkpoint의 모델·optimizer·scheduler 상태
4. 합성된 native config와 실제 실행 명령·환경 기록

이 저장소는 [학습 규약](../configs/rail_world_model_protocol.json)과 추론 도구를 제공한다. 내부 native 학습 코드·데이터·전체 학습 재개 checkpoint는 기관 보관본에 있으며, 공개 학습 CLI는 아직 분리하지 않았다. 약48MB의 추론용 변경 가중치에는 optimizer·scheduler 상태가 포함되지 않는다.

후속 구현에서는 데이터 loader와 mask부터 분리하고, 작은 데이터로 입력 shape·업데이트 대상·저장/재개를 검사한 뒤 학습 명령을 연결한다. 비교할 때는 시작 checkpoint·입력 이미지·Action·prompt·seed·sampling 설정을 함께 고정한다.
