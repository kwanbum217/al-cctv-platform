# 포토샵 빨간 박스 → YOLO xywhn 라벨 자동 변환

# 목표:
# 포토샵(또는 그림판)으로 이미지에 빨간색 박스를 직접 그린 뒤,
# 그 픽셀 위치를 자동으로 읽어 YOLO 훈련용 .txt 라벨 파일을 만든다.

# [입력] 포토샵으로 빨간 박스 그린 이미지#          ↓
# [처리] 빨간 픽셀 감지 → 윤곽선 → 외접 사각형 → xywhn 변환          ↓
# [출력] YOLO .txt 라벨  +  디버그 이미지 (초록 박스로 재확인)

import cv2
import numpy as np 
import os
import sys

# 터미널 UTF-8 인코딩 설정
if hasattr(sys.stdout, "reconfigure"):
  getattr(sys.stdout, "reconfigure")(encoding="utf-8")

def red_boxes_to_yolo_labels(image_path, class_id=0, red_lower=(0, 0, 150), red_upper=(80, 80, 255)) :
  """
    포토샵으로 빨간 박스를 그린 이미지 → YOLO xywhn 라벨 변환 함수.

    [동작 순서]
      1) 이미지 읽기
      2) BGR 범위 마스킹으로 빨간 픽셀만 추출
      3) 노이즈 제거 (작은 점 무시)
      4) 윤곽선 검출 → 외접 사각형(xyxy) 계산
      5) xyxy → xywhn 변환 (YOLO 정규화 포맷)

    Parameters
    ----------
    image_path : str   분석할 이미지 경로 (포토샵으로 빨간 박스 그린 이미지)
    class_id   : int   이 이미지 박스들의 클래스 번호 (0=person, 1=car ...)
    red_lower  : tuple 빨간색으로 인식할 BGR 하한값 (기본: 어두운 빨간까지 포함)
    red_upper  : tuple 빨간색으로 인식할 BGR 상한값

    Returns
    -------
    labels    : list[str]     YOLO 라벨 줄 리스트  ["0 cx cy w h", ...]
    debug_img : np.ndarray    감지 결과를 초록으로 표시한 확인용 이미지
  """

  # 이미지 읽기
  # cv2.imread() : 파일을 BGR numpy 배열로 읽음
  img = cv2.imread(image_path)
  if img is None:
      raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")
      
  H, W = img.shape[:2]   # 높이(H), 너비(W) — xywhn 정규화할 때 나눌 값

  # ── Step 1: 빨간 픽셀만 마스킹 ──────────────────────────────
  # OpenCV는 BGR 순서! 빨간색 = B낮음, G낮음, R높음
  #   lower = (B하한, G하한, R하한)
  #   upper = (B상한, G상한, R상한)
  # cv2.inRange() : 범위 안 픽셀 → 255(흰색), 범위 밖 → 0(검정)
  lower = np.array(red_lower, dtype=np.uint8)
  upper = np.array(red_upper, dtype=np.uint8)
  mask = cv2.inRange(img, lower, upper)
  
  # ── Step 2: 노이즈 제거 ──────────────────────────────────────
  # MORPH_CLOSE : 마스크 안의 작은 구멍을 메움
  # → 박스 테두리 선이 끊어져 있어도 하나로 연결됨
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
  mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

  # ── Step 3: 윤곽선 검출 ──────────────────────────────────────
  # findContours() : 흰색 덩어리의 외곽선 좌표 목록 반환
  # RETR_EXTERNAL : 가장 바깥 윤곽선만 검출 (내부 중첩 무시)
  # CHAIN_APPROX_SIMPLE : 꼭짓점만 저장 (메모리 절약)
  contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

  labels = []
  debug_img = img.copy()   # 원본 보존, 확인용 이미지에만 초록 박스 그림

  for cnt in contours:
    if cv2.contourArea(cnt) < 10:    # 윤곽선 면적 10 미만(노이즈)은 무시
      continue

    # ── Step 4: 외접 사각형 계산 ─────────────────────────────
    # boundingRect() : 윤곽선을 완전히 감싸는 최소 사각형
    # 반환값: 좌상단 x, 좌상단 y, 너비, 높이  (xyxy가 아닌 xywh 픽셀!)
    bx, by, bw, bh = cv2.boundingRect(cnt)

    # ── Step 5: xyxy → xywhn 변환 ────────────────────────────
    # YOLO 라벨 형식: 중심좌표(cx,cy) + 크기(w,h) 를 0~1 비율로 표현
    #  cx = (좌상단x + 너비/2) / 이미지너비    ← 중심 x의 비율
    #  cy = (좌상단y + 높이/2) / 이미지높이    ← 중심 y의 비율
    #  nw = 너비 / 이미지너비                  ← 박스 너비의 비율
    #  nh = 높이 / 이미지높이                  ← 박스 높이의 비율
    cx = (bx + bw / 2) / W
    cy = (by + bh / 2) / H
    nw = bw / W
    nh = bh / H

    # YOLO .txt 한 줄 형식: "클래스번호 cx cy w h"
    label_line = f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}"
    labels.append(label_line)

    # 디버그 이미지: 감지된 박스를 초록으로 덧그림 (육안 확인용)
    cv2.rectangle(debug_img, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
    cv2.putText(debug_img, f"cls:{class_id} ({cx:.2f},{cy:.2f})",
                (bx, by - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

  return labels, debug_img

def save_yolo_label(labels, image_path, label_dir="labels"):
  """
  라벨 리스트를 YOLO .txt 파일로 저장.

  [규칙] 이미지와 같은 이름, 확장자만 .txt
    예) images/train/001.jpg → labels/train/001.txt
  """
  os.makedirs(label_dir, exist_ok=True)

  # 이미지 파일명에서 확장자만 .txt 로 교체
  base_name = os.path.splitext(os.path.basename(image_path))[0]
  txt_path = os.path.join(label_dir, base_name + ".txt")

  # UTF-8 인코딩 강제 적용
  with open(txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(labels))
  
  return txt_path


# 실행 경로 독립성 확보 (절대경로 전환)
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, "anotated", "kkb_01.png")

# ── 단일 이미지 처리 ──────────────────────────────────────────────
labels, debug = red_boxes_to_yolo_labels(
    image_path=image_path,  # 포토샵으로 빨간 박스 그린 이미지
    class_id=0,             # 0 = person
)

# 라벨 확인 (출력 예시)
for line in labels:
    print(line)
# 0 0.270313 0.428125 0.140625 0.447917
# 0 0.664844 0.417708 0.132812 0.447917

# 디버그 이미지 저장 (초록 박스로 제대로 잡혔는지 눈으로 확인)
debug_path = os.path.join(current_dir, "debug_001.jpg")
cv2.imwrite(debug_path, debug)

# .txt 라벨 파일 저장
label_dir = os.path.join(current_dir, "labels", "train")
txt_path = save_yolo_label(labels, image_path, label_dir=label_dir)
print(f"라벨 저장: {txt_path}")
# 라벨 저장: labels/train/kkb_01.txt

import glob

# 폴더 안의 모든 이미지를 한 번에 처리 (절대경로 탐색)
search_patterns = [
    os.path.join(current_dir, "anotated", "*.png"),
    os.path.join(current_dir, "anotated", "*.jpg"),
    os.path.join(current_dir, "anotated", "*.jpeg")
]
image_files = []
for pattern in search_patterns:
    image_files.extend(glob.glob(pattern))

image_files = sorted(list(set(image_files)))

# 디버그 저장 폴더 구성 (절대경로)
debug_dir = os.path.join(current_dir, "debug")
os.makedirs(debug_dir, exist_ok=True)

# 라벨 저장 폴더 구성 (절대경로)
label_output_dir = os.path.join(current_dir, "labels", "train")

for img_path in image_files:
    labels, debug = red_boxes_to_yolo_labels(img_path, class_id=0)

    if not labels:
        print(f"[WARNING] 빨간 박스 없음: {img_path}")
        continue

    # 라벨 저장
    save_yolo_label(labels, img_path, label_dir=label_output_dir)

    # 디버그 이미지 저장
    base_name = os.path.basename(img_path)
    debug_img_path = os.path.join(debug_dir, base_name)
    cv2.imwrite(debug_img_path, debug)

    print(f"[OK] {img_path} -> 박스 {len(labels)}개")

   
