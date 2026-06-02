#  사전 훈련 모델로 객체 인식 기본기 익히기
import os
import sys
from ultralytics import YOLO 
import cv2

# 터미널 UTF-8 인코딩 설정
if hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")

# 실행 경로 독립성 확보 (절대경로 전환)
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, "images", "Man_walking_Dog_onLoad.jpg")
model_path = os.path.join(current_dir, "yolov8n.pt")

# YOLOv8 nano 모델 로드
model = YOLO(model_path)

# 객체 인식 실행
# save=True 일 때 탐지 결과(bbox가 그려진 이미지)가 runs/detect/predict 폴더에 자동 저장됩니다.
# results = model.predict(
#   source=image_path, 
#   conf=0.1, 
#   save=True
# )

# vision_sample 디렉토리 경로 탐색
vision_sample_dir = os.path.abspath(os.path.join(current_dir, "..", "part04_multimodal", "vision_sample"))

# vision_sample 폴더 내의 이미지 파일들을 동적으로 수집 (.jpeg, .jpg, .png)
image_extensions = (".jpg", ".jpeg", ".png")
source_path = [
  os.path.join(vision_sample_dir, f)
  for f in os.listdir(vision_sample_dir)
  if f.lower().endswith(image_extensions)
]

results = model.predict(
  source=source_path, 
  conf=0.1, 
  save=True
)



# 결과 리스트의 첫 번째 결과 획득
# result = results[0]

print(f"yolov8n.pt 모델이 탐지 할 수 있는 클래스 : {results[0].names}")
print("------------------------------------------------")

for i, r in enumerate(results, start=1):
  boxes = r.boxes
  if boxes is not None and len(boxes) > 0:    
    print(f"[OK] 이미지 {i} 탐지 개수: ", len(boxes))
    # 탐지된 객체 정보(클래스 및 신뢰도) 상세 출력
    for box in boxes:
      if box.cls is not None and box.conf is not None and box.xyxy is not None and box.xyxyn is not None:
        class_id = int(box.cls[0])
        class_name = r.names[class_id]
        confidence = round(float(box.conf[0]), 2)
        # Tensor 형태인 box.xyxy[0]을 .tolist()를 사용해 파이썬 리스트로 변환하고, 정수형 좌표로 변환
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        # 정규화 좌표 (Normalized coordinates) 추출 [x1n, y1n, x2n, y2n]
        x1n, y1n, x2n, y2n = [round(float(v), 4) for v in box.xyxyn[0].tolist()]
        print(f"   -> [탐지] {class_name} (신뢰도: {confidence}) | 위치: [{x1}, {y1}, {x2}, {y2}] | 정규화: [{x1n}, {y1n}, {x2n}, {y2n}]")
  else : 
    print(f"[OK] 이미지 {i} 탐지 개수: 0")

  print(f"[OK] 이미지 {i} 결과 저장 위치: ", r.save_dir)


# 탐지된 객체 정보 출력
if len(results) > 0:
  result = results[0]
  res_boxes = result.boxes
  if res_boxes is not None:
    print("[OK] 탐지 개수:", len(res_boxes))
    print("[OK] 결과 저장 위치:", result.save_dir)

# OpenCV 라이브러리 임포트 및 시각화 결과 저장
try:
  import cv2
  if len(results) > 0:
    result = results[0]
    # result.plot()은 탐지 결과(바운딩 박스, 레이블, 신뢰도)가 그려진 BGR numpy 배열을 반환합니다.
    plotted_img = result.plot()
    
    # OpenCV를 이용해 파일로 시각화 결과 저장
    output_path = os.path.join(current_dir, "plotted_result.jpg")
    cv2.imwrite(output_path, plotted_img)
    print(f"[OK] OpenCV를 통해 시각화 이미지가 저장되었습니다: {output_path}")
except ImportError:
  print("[WARNING] OpenCV(cv2) 라이브러리가 설치되어 있지 않아 시각화 저장을 생략합니다.")

#  ----------------------------------------------------------
# result.names는 클래스 번호와 클래스 이름을 연결해주는 딕셔너리입니다.

#

# 예를 들어 다음과 같은 형태입니다.

# {

#     0: "person",

#     1: "bicycle",

#     2: "car",

#     ...

# }

#

# YOLO의 내부 결과는 클래스 이름이 아니라 클래스 번호로 들어 있습니다.
# 따라서 번호를 사람이 읽을 수 있는 이름으로 바꾸려면 result.names가 필요합니다.

# result.boxes는 탐지된 박스들의 모음입니다.
# 여기서는 첫 번째 탐지 결과만 꺼내 봅니다.

#

# 주의:

# 만약 탐지된 객체가 하나도 없다면 result.boxes[0]에서 오류가 납니다.
# 실제 서비스에서는 len(result.boxes) > 0인지 먼저 확인하는 것이 안전합니다.
# box.cls는 탐지된 객체의 클래스 번호입니다.

# 예: 0이면 person, 2이면 car

#

# box.cls는 PyTorch Tensor 형태입니다.

# 그래서 box.cls[0]으로 값을 꺼내고 int()로 일반 정수로 바꿉니다.
# box.xywhn은 훈련 라벨에서 사용하는 정규화 좌표입니다.

#

# xywhn의 의미:

# x: 박스 중심의 x좌표
# y: 박스 중심의 y좌표
# w: 박스 너비
# h: 박스 높이
# n: normalized, 즉 0~1 사이 비율로 정규화되었다는 뜻

# 이 좌표는 화면에 박스를 그릴 때보다
# YOLO 모델을 훈련시킬 때 라벨 파일에서 더 많이 사용합니다.

# result.plot()은 탐지 결과를 이미지 위에 그려줍니다.
# 원본 이미지 위에 다음 정보가 표시됩니다.
# - 객체 박스
# - 클래스 이름
# - confidence
# 반환값은 numpy 배열입니다.
# 즉, OpenCV에서 사용하는 이미지 형식과 같습니다.

# ===================================================
# YOLO("yolov8n.pt")로 사전훈련 모델을 불러온다.

# model.predict()로 이미지 탐지를 실행한다.

# results는 리스트이므로 results[0]으로 첫 번째 결과를 꺼낸다.

# result.boxes에는 탐지된 객체 정보가 들어 있다.

# box.cls는 클래스 번호다.

# box.conf는 신뢰도다.

# box.xyxy는 박스 픽셀 좌표다.

# result.plot()으로 결과 이미지를 만들고 cv2.imwrite()로 저장할 수 있다.