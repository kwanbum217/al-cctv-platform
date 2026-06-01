import os
import cv2               # OpenCV 이미지 전처리 엔진
import numpy as np
import pytesseract       
from PIL import Image    

# ── [해결-1] 프로젝트 로컬 tessdata 폴더로 데이터 로딩 우회 선언 ─────────────
os.environ['TESSDATA_PREFIX'] = r'D:\korea_IT\2025_LangChain_\al-cctv-platform\tessdata'

# ── [해결-2] Windows 환경 Tesseract 실행 엔진 절대경로 지정 ─────────────────
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ── [해결-3] 실행 경로 독립성 확보 (절대경로 병합) ───────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'images', 'KakaoTalk_20260601_112954045.jpg')

# 1. OpenCV 이미지 로드 및 그레이스케일 변환
img_bgr = cv2.imread(image_path)
if img_bgr is None:
  print("[ERROR] 이미지를 불러올 수 없습니다. 경로를 확인해주세요.")
  exit()

gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

# 2. 3배 이미지 확대 (Tesseract 최소 요구 해상도 30px 이상 충족)
scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)

# 3. OTSU 이진화 (글자와 배경을 완벽히 흑백으로 분리)
_, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# [해결-4] NumPy 배열(OpenCV)을 PIL Image 객체로 명시적 형변환 (TypeError 예방)
img_pil = Image.fromarray(binary)

# 4. 한글('kor') 및 영어('eng') 동시 판독 실행
result = pytesseract.image_to_string(img_pil, lang='kor+eng')

print("=== OCR 분석 결과 ===")
print(result.strip())
print("=====================")
