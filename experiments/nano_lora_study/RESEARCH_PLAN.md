# Rail Post-Training Research Plan

최종 갱신: 2026-08-05

## 1차 목표

Unitree Go2-W/A2 철도 순찰 파이프라인에서 부족한 상황을 보완할 합성 영상을 생성한다.

1. 정상 순찰 영상의 비·안개·눈·야간 변환
2. 사람·고라니·낙석 등 선로 침입 위험물 삽입

## 권장 접근

실제 로봇의 카메라 높이·운동·선로 구조를 유지해야 하므로 Text-to-Video보다 정상 순찰 영상을 조건으로 한 Video-to-Video를 우선한다. Text-to-Video는 시나리오 탐색과 storyboard에 사용한다.

## 데이터 단위

각 clip에 다음 metadata를 고정한다.

- 원본 노선/구간과 사용 권한
- 카메라·로봇 종류 및 이동 상태
- 기상, 조도, 시간대
- 위험물 종류, 위치, 크기, 등장·퇴장 시간
- 선로 점유 여부와 안전거리
- train/validation/test split 및 원본 계보

동일 원본에서 파생된 clip은 서로 다른 split으로 누출하지 않는다.

## 단계별 실험

### 단계 1 — 파이프라인 smoke

소수 clip으로 decode, conditioning, LoRA update, checkpoint 및 재추론을 확인한다. 품질 결론을 내리지 않는다.

### 단계 2 — 소량 과적합 시험

한 가지 시나리오를 의도적으로 학습해 adapter가 조건을 습득할 수 있는지 확인한다. Base와 LoRA를 동일 seed·입력으로 비교한다.

### 단계 3 — held-out 평가

학습에 쓰지 않은 장소·날씨·위험물 조합으로 일반화와 원본 구조 보존을 평가한다.

### 단계 4 — downstream 유효성

합성 데이터를 추가하지 않은 탐지기와 추가한 탐지기를 실제 영상 test set에서 비교한다. 합성 영상 자체의 인상보다 위험물 탐지 성능 개선을 최종 근거로 삼는다.

## 평가 항목

- 프롬프트/조건 충족률
- 선로 geometry 및 카메라 궤적 보존
- 위험물 identity·크기·위치의 시간적 일관성
- flicker, 형태 붕괴, 물리적 관통
- 전문가 사용 가능/수정 필요/폐기 판정
- 실제 held-out 데이터에서 downstream precision, recall 및 false alarm

## 자원 benchmark

full-SFT와 LoRA는 동일 seed, 데이터 순서, token 수, grad accumulation, warm-up 및 checkpoint 비활성 구간에서 비교한다. 각 노드의 peak memory를 독립적으로 기록하고 checkpoint step을 제외한 step time의 평균·중앙값·표준편차를 보고한다.

## 진행 게이트

- 데이터 권한과 비식별화 확인
- taxonomy·metadata·split 동결
- Base 평가 결과 선등록
- smoke 및 checkpoint round-trip 통과
- 전문가 평가 기준 합의
- 실제 철도 test set을 학습·튜닝에서 격리
