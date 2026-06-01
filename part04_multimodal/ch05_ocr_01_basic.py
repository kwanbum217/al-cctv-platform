import pytesseract              # OCR 라이브러리 (Tesseract 파이썬 래퍼)
from PIL import Image, ImageDraw  # 이미지 처리 (Pillow)

# [해결] Windows 환경에서 Tesseract 실행 엔진의 절대경로 명시 지정
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

result = pytesseract.image_to_string(img, lang="eng")

print(f"OCR 결과: {result.strip()}")
# 출력: OCR 결과: CAM-03  2025-04-04 02:13