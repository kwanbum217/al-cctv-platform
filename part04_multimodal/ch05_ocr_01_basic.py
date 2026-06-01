import pytesseract              # OCR 라이브러리 (Tesseract 파이썬 래퍼)
from PIL import Image, ImageDraw  # 이미지 처리 (Pillow)

# [해결] Windows 환경에서 Tesseract 실행 엔진의 절대경로 명시 지정
# Tesseract 언어팩을 찾지 못하는 경우
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ─────────────────────────────────────────────────────────────
# 테스트 이미지 생성 함수
# ★ 실제 수업에서는 이 함수 대신:
#     img = Image.open("cctv_frame.jpg")
# ─────────────────────────────────────────────────────────────
def create_sample_image(text: str) -> Image.Image:
    """흰 배경에 검은 글씨 테스트 이미지 생성"""
    img = Image.new("RGB", (420, 80), color=(255, 255, 255))  # 흰 배경
    ImageDraw.Draw(img).text((10, 25), text, fill=(0, 0, 0))  # 검은 글씨
    return img

# 예 : image_to_string() : 텍스트만 추출
img = create_sample_image("CAM-03 2026-06-01 02:13")

# 예 : image_to_data() : 텍스트 + 위치 + 신뢰도 추출
data = pytesseract.image_to_data(
  img, lang='eng', output_type=pytesseract.Output.DICT
)


result = pytesseract.image_to_string(img, lang="eng")

print(f"OCR 결과: {result.strip()}")
# 출력: OCR 결과: CAM-03  2025-04-04 02:13

print("\n[단어별 상세 결과]")
for word, conf in zip(data['text'], data['conf']):
    # conf == -1 은 빈칸/줄바꿈 → 의미 없으므로 건너뜀
    if word.strip() and str(conf) != '-1':
        print(f"  단어: '{word}' | 신뢰도: {conf}%")

# data = {
#     'text':   ['CAM-03', '2025-04-04', '02:13'],  # 인식된 단어
#     'conf':   [87, 84, 78],                        # 신뢰도 0~100%
#     'left':   [10, 95, 210],   # 단어 시작 X좌표 (px)
#     'top':    [25, 25, 25],    # 단어 시작 Y좌표 (px)
#     'width':  [55, 80, 35],    # 단어 너비 (px)
#     'height': [20, 20, 20],    # 단어 높이 (px)
# }
# left, top, width, height → OpenCV로 사각형 그릴 때 활용 가능!

