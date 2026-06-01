import os
import pytesseract       # OCR 라이브러리
from PIL import Image    # 이미지 파일 열기

# [우회] 윈도우 쓰기 권한 차단을 피하기 위해 프로젝트 내부 로컬 tessdata 경로 강제 지정
os.environ['TESSDATA_PREFIX'] = r'D:\korea_IT\2025_LangChain_\al-cctv-platform\tessdata'

# ── Windows 전용 설정 ─────────────────────────────────────────
# Linux/macOS는 이 줄 없어도 됩니다.
# tesseract.exe가 설치된 경로를 정확히 적어야 합니다.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# [해결] 실행 경로 독립성 확보 (절대경로 자동 맵핑)
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'images', 'capture1.png')
img = Image.open(image_path)

result = pytesseract.image_to_string(img, lang='kor')

print(result.strip())