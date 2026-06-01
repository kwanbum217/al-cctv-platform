import cv2               # OpenCV: 이미지 처리
import numpy as np       # NumPy: 이미지 = numpy 배열
import pytesseract

# [해결] Windows 환경에서 Tesseract 실행 엔진의 절대경로 명시 지정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image, ImageDraw

# ─────────────────────────────────────────────────────────────
# 저화질 CCTV 이미지 시뮬레이션
# ★ 실제 수업에서는:
#     img_bgr = cv2.imread("cctv_night_frame.jpg")
# ─────────────────────────────────────────────────────────────
def create_degraded_image(text: str) -> np.ndarray:
    """야간 CCTV처럼 낮은 대비, 회색 배경의 이미지 생성"""
    img = Image.new("RGB", (200, 40), color=(180, 180, 180))  # 회색 배경
    ImageDraw.Draw(img).text((5, 10), text, fill=(60, 60, 60))  # 낮은 대비 글씨
    return np.array(img)  # PIL → numpy 배열 변환 (OpenCV 형식)

test_text = "CAM05 01:14"
img_rgb = create_degraded_image(test_text)

#  ── 1단계: 그레이스케일 변환 ─────────────────────────
# 이유: OCR은 색상 정보가 불필요.
#       흑백으로 바꾸면 데이터 1/3로 감소 → 속도↑, 노이즈↓
gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

# ── 2단계: 이미지 확대 (업스케일) ───────────────────
# 이유: CCTV 오버레이 글씨는 보통 20~25px 높이
#       Tesseract 최소 권장 크기: 30px 이상
#       3배 확대 → 60~75px → 인식률 크게 향상
#
# fx=3.0, fy=3.0 : 가로·세로 각각 3배
# cv2.INTER_LINEAR : 픽셀 보간 방식 (속도와 품질의 균형)
scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)

# 3단계 이진화 : 글자와 배경을 환전히 흑/백으로 분리 (OCR이 글자를 명확하게 인식 할 수 있또록)
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU )

# 4단계 이진화 이후 노이즈 제거 -> 모폴로지 연산
# OPEN: 침식(Erode) -> 팽창 (Dilate)
kernel = np.ones((2, 2), np.uint8)
cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel=kernel)

def ocr_with_conf(image) -> tuple[str, float] :
  """
    이미지 OCR 후 (텍스트, 평균 신뢰도) 반환  
  """
  if isinstance(image, np.ndarray) :
    image = Image.fromarray(image) 

  # --psm 7 : 이미지 전체 = 하나의 텍스트 줄 (타임스탬프·ID에 최적)
  # --oem 3 : LSTM 딥러닝 엔진 사용 (가장 정확)
  result_dict = pytesseract.image_to_data(
    image, lang='eng', config='--psm 7 --oem 3',
    output_type=pytesseract.Output.DICT
  )

  words, confs = [], []
  for w, c in zip(result_dict['text'], result_dict['conf']):
      if w.strip() and str(c) != '-1':
          words.append(w); confs.append(int(c))
  
  return ' '.join(words).strip(), (sum(confs) / len(confs) if confs else 0)

print(f"원본 텍스트: '{test_text}'\n")
print(f"{'단계':<15} {'OCR 결과':<20} {'신뢰도'}")
print("-" * 50)

stages = [
    ("①전처리 없음",    img_rgb),
    ("②그레이스케일",   gray),
    ("③+3배 확대",      scaled),
    ("④+이진화(OTSU)", binary),
    ("⑤+노이즈 제거",  cleaned),
]
for name, img in stages:
    text, conf = ocr_with_conf(img)
    print(f"{name:<15} '{text:<18}' {conf:.0f}%")


  