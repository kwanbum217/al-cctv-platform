import os
import sys
import time
import cv2

# [해결-1] Windows CP949 터미널 환경에서 유니코드 진행바 문자 출력 시 인코딩 크래시 방지
if hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
import pytesseract
import easyocr
from PIL import Image

# 1. Tesseract 훈련 데이터 및 실행 경로 지정 (우회/전역 동시 커버)
os.environ['TESSDATA_PREFIX'] = r'D:\korea_IT\2025_LangChain_\al-cctv-platform\tessdata'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. 이미지 경로 지정 (절대경로 독립성 확보)
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'images', 'KakaoTalk_20260601_112954045.jpg')

print(f"[알림] 분석 대상 이미지: {os.path.basename(image_path)}")
print("=" * 60)

# ────────── [테스트 1] Tesseract OCR (OpenCV 전처리 결합) ──────────
print("\n[테스트 1] Tesseract OCR (OpenCV 3x 확대 + OTSU 이진화 전처리) 기동 중...")
t_start = time.time()

# 이미지 로드 및 전처리
img_bgr = cv2.imread(image_path)
if img_bgr is None:
  print("[ERROR] 이미지를 로드할 수 없습니다. 경로를 확인해주세요.")
  exit()

gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)
_, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
img_pil = Image.fromarray(binary)

# OCR 실행
tess_result = pytesseract.image_to_string(img_pil, lang='kor+eng')
tess_time = time.time() - t_start

print(f"-> Tesseract 소요 시간: {tess_time:.2f}초")

# ────────── [테스트 2] EasyOCR (순수 딥러닝 기반) ──────────
print("\n[테스트 2] EasyOCR (순수 딥러닝 기반 - CRAFT 텍스트 탐지) 기동 중...")
easy_start = time.time()

# Reader 인스턴스 초기화 (한글 ko, 영어 en 로드)
# ※ 최초 기동 시 인터넷을 통해 딥러닝 가중치 모델 파일(CRAFT, ResNet 등)을 자동 다운로드받습니다.
# GPU 가속이 불가능한 일반 연산 환경에서도 안전하게 크래시 없이 구동되도록 gpu=False(CPU 모드)로 초기화합니다.
# [해결-2] verbose=False 선언을 통해 특수 유니코드 진행 바 출력을 차단하여 인코딩 오류 원천 방지
reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False) 

# [해결] 딥러닝 텐서 폭발에 의한 CPU 메모리 OOM(Out of Memory) 방지용 리사이징
h, w = img_bgr.shape[:2]
max_dim = 1000  # 딥러닝 텍스트 검출 최적 타겟 해상도
if max(h, w) > max_dim:
  scale = max_dim / max(h, w)
  img_easy = cv2.resize(img_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
  print(f"-> [OOM 예방] 이미지 크기 축소: {w}x{h} -> {img_easy.shape[1]}x{img_easy.shape[0]}px")
else:
  img_easy = img_bgr

# EasyOCR 호출 시 다운샘플링된 이미지 전달
easy_results = reader.readtext(img_easy, detail=0) 
easy_result = "\n".join(easy_results)
easy_time = time.time() - easy_start

print(f"-> EasyOCR 소요 시간 (가중치 로딩 포함): {easy_time:.2f}초")

# ────────── [최종 결과 비교 레포트] ──────────
print("\n" + "=" * 60)
print("              Tesseract vs EasyOCR 성능 비교 레포트")
print("=" * 60)
print(f"▶ 1. 소요 시간 비교:")
print(f"   - Tesseract: {tess_time:.2f}초 (OpenCV 3x 전처리 포함)")
print(f"   - EasyOCR  : {easy_time:.2f}초 (가중치 파일 수신 및 CPU 딥러닝 연산 포함)")

print(f"\n▶ 2. Tesseract 인식 결과 (상위 15줄):")
print("-" * 40)
print("\n".join(tess_result.strip().split("\n")[:15]))
print("-" * 40)

print(f"\n▶ 3. EasyOCR 인식 결과 (상위 15줄):")
print("-" * 40)
print("\n".join(easy_result.strip().split("\n")[:15]))
print("-" * 40)
print("=" * 60)
