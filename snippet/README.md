# snippet — 실행 가능한 예제 원본

책·실습·슬라이드가 함께 쓰는 설정 파일과 스크립트의 원본을 둘 곳입니다. 원고에 같은 내용을 붙여 넣는 대신 여기 원본을 두고 불러 쓰면, 한 곳만 고쳐도 모든 곳이 바뀝니다.

계획:

- `snippet/<주제>/` 아래에 파일을 둡니다. 예: `snippet/caddy-mtls/Caddyfile`, `snippet/ufw-egress/rules.sh`
- 원고에서는 Quarto의 include 기능으로 불러 씁니다.
- 각 폴더에 `test.sh`를 두고, CI가 컨테이너에서 실제로 실행해 결과를 확인합니다.

아직 비어 있습니다. 옮길 후보는 `lab-runner` 에이전트가 실습을 검증하면서 제안합니다.
