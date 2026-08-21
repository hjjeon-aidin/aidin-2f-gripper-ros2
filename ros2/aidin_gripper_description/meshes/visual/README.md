# meshes/visual/

SolidWorks에서 내보낸 실제 STL을 여기에 넣으세요. `urdf/aidin_gripper*.urdf` 가
참조하는 파일명은 다음 두 개뿐입니다 (핑거는 좌우 대칭 부품이라 STL 1개를 공유
— `ee_finger_r2`/`gripper_finger_2` 쪽 조인트에서 `rpy="0 0 3.14159265"` 로
180° 회전시켜 재사용):

| 파일 | 용도 |
|---|---|
| `gripper_base.stl` | 베이스(하우징+모터+감속기) |
| `gripper_finger.stl` | 핑거 1개 형상 (양쪽 공통) |

STL 출력 단위는 mm 기준이며 URDF 쪽 `scale="0.001 0.001 0.001"` 로 m 변환합니다.
좌우 전용(미러) 부품으로 다시 설계하게 되면 `gripper_finger_L.stl` /
`gripper_finger_R.stl` 두 개로 나누고, 각 조인트의 `rpy` 180° 회전을 제거한 뒤
URDF의 `<mesh filename=.../>` 두 줄만 갈아 끼우면 됩니다.
