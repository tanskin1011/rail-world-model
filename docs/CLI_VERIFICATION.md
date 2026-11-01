# CLI end-to-end 검증

## 범위

최종 Nano B를 불러오는 새 CLI에서 기존 첫 이미지와 정속10 카메라 Action으로 단일 영상을 생성했다. 새 학습·조건 탐색·추가 seed 실행은 하지 않았다. 기관 입력·영상·가중치·서버 경로는 이 문서에 배포하지 않는다.

| 확인 항목 | 결과 |
|---|---|
| CPU 계약 테스트 | 10개 통과 |
| 기존 tokenizer 입력 | 원문 prompt 유지, 잘림 없음 |
| 실제 로드 가중치 | 최종 B의 1,097개 tensor typed hash 일치 |
| 모델 mode/domain | forward_dynamics / camera_pose domain2 |
| 관측 영상 조건 | 첫 프레임 [0] |
| Action 조건 | 188개 전이 전체, 모델 입력 188×64 |
| 샘플링 | seed401, UniPC 30 steps, guidance1, shift10 |
| 출력 | 832×480, 189프레임, 24 FPS |
| 전체 MP4 디코딩 | 통과 |
| 실행 종료 | 0, backend COMPLETE 및 모델 RESULT COMPLETE |
| 추가 학습·다운로드 | 없음 |

상태·로그 조회를 실제 작업에서 확인했다. 실행 중 cancel의 실제 종료 동작, 다른 PC, 다른 모델, 다른 해상도·프레임 수는 이번 검증 범위가 아니다.

## 해석

이 검사는 **기존 학습 가중치를 새 명령어로 불러와 영상 파일을 만들 수 있는가**를 확인한다. 주행 제어 정확도·장면 보존·일반화 성능의 새로운 연구 평가가 아니다. `semantic_review_pending=true`를 유지하며, 한 번의 추론 성공을 연구 전체의 성공으로 확대하지 않는다.

정확한 실행 명령·입력 SHA-256·실제 checkpoint·유효 args·worker 로그·자원 기록은 로컬 Git 제외 출력 폴더에 보존한다. 이번 검증 영상 역시 공개 자료가 아니다.
