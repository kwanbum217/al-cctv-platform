import os
import cv2               # OpenCV 이미지 전처리 엔진 (리사이징용)
import easyocr

# gpu=False 지정 시 CPU 연산 모드 구동 (안정성 보장)
reader = easyocr.Reader(['ko','en'], gpu=False)

# 실행 경로 독립성 확보 (절대경로 병합)
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'images', 'KakaoTalk_20260601_112954045.jpg')

# 1. OpenCV 이미지 로드
img_bgr = cv2.imread(image_path)
if img_bgr is None:
    print("[ERROR] 이미지를 불러올 수 없습니다. 경로를 확인해주세요.")
    exit()

# 2. [해결] 딥러닝 텐서 폭발에 의한 CPU 메모리 OOM(Out of Memory) 방지용 리사이징
h, w = img_bgr.shape[:2]
max_dim = 1000  # CPU 환경에서 딥러닝 CRAFT 탐지가 원활하게 동작하는 최적 타겟 해상도
if max(h, w) > max_dim:
    scale = max_dim / max(h, w)
    img_easy = cv2.resize(img_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    print(f"-> [OOM 예방] 이미지 크기 축소: {w}x{h} -> {img_easy.shape[1]}x{img_easy.shape[0]}px")
else:
    img_easy = img_bgr

# 3. OOM 예방 처리된 경량화 이미지를 딥러닝 모델에 전달
result = reader.readtext(img_easy)

for (bbox, text, confidence) in result:
    # bbox       : 글자를 감싼 네모의 네 꼭짓점 좌표 [좌상, 우상, 우하, 좌하]
    # text       : 인식된 글자
    # confidence : 얼마나 확신하는지 (0~1)
    print(f"인식: {text}  (신뢰도 {confidence:.2f})")
