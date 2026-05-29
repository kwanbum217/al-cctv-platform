import os
import sys
import io
from supertonic import TTS

# Windows 터미널에서 한글 및 이모지 출력 시 인코딩 오류(UnicodeEncodeError) 방지
if isinstance(sys.stdout, io.TextIOWrapper):
  sys.stdout.reconfigure(encoding="utf-8")

def main():
  print("=" * 60)
  print("[INFO] Supertonic 온디바이스 TTS 실습을 시작합니다.")
  print("=" * 60)

  # 1. TTS 객체 초기화 (온디바이스 ONNX 기반 모델 자동 다운로드 및 적재)
  print("[1/4] Supertonic TTS 파이프라인 초기화 중...")
  tts = TTS()

  # 2. 내장 보이스 스타일 로딩 (M1: 남성, F1: 여성)
  print("[2/4] 내장 보이스 스타일 로드 중...")
  voice_male = tts.get_voice_style("M1")      # 남성 1번 목소리
  voice_female = tts.get_voice_style("F1")    # 여성 1번 목소리

  # 3. 합성할 기본 텍스트 및 설정 구성
  sample_text = "안녕하세요. 인공지능 CCTV 보안 분석 플랫폼의 안내 방송 시스템입니다. 본 구역은 안전하게 감시되고 있습니다."
  
  # 출력 경로 설정 (waves 디렉토리)
  script_dir = os.path.dirname(os.path.abspath(__file__))
  output_dir = os.path.join(script_dir, "waves")
  os.makedirs(output_dir, exist_ok=True)
  
  output_file = os.path.join(output_dir, "supertonic_announcement.wav")

  # 4. 음성 합성 및 파일 저장
  print("[3/4] TTS 음성 합성 수행 중...")
  print(f"   - 입력 텍스트: \"{sample_text}\"")
  print("   - 목소리 캐릭터: F1 (여성)")
  
  try:
    # synthesize는 (wav_ndarray, duration_list) 튜플을 반환합니다.
    wav, duration = tts.synthesize(
      text=sample_text,
      voice_style=voice_female,
      lang="ko"  # 한국어 합성 설정
    )
    
    print("[4/4] 생성된 음성을 오디오 파일로 저장 중...")
    tts.save_audio(wav, output_file)
    
    print("\n" + "=" * 60)
    print("[성공] Supertonic TTS 음성 합성 및 저장이 완료되었습니다!")
    print(f"   - 음성 길이: {float(duration[0]):.2f}초")
    print(f"   - 저장 위치: {output_file}")
    print("=" * 60)

  except Exception as e:
    print(f"\n[오류] 음성 합성 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
  main()
