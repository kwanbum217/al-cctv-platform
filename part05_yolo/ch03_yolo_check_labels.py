# 데이터 라벨링이 잘못되면 훈련 결과가 비참해진다.
# 훈련전에 라벨을 자동 체크하여 최악의 경우를 미리 예방한다.
import os
import glob
import sys

# 터미널 UTF-8 인코딩 설정 (Smart Quote 및 한글 출력 대비)
if hasattr(sys.stdout, "reconfigure"):
  getattr(sys.stdout, "reconfigure")(encoding="utf-8")

def check_labels(label_dir, num_classes):
  """
  YOLO 라벨 파일이 규칙에 맞는지 검사한다.

  [검사 항목]
    1) 한 줄은 정확히 5개 값이어야 한다 (클래스 + 좌표4개)
    2) 클래스 번호는 0 이상 num_classes 미만의 정수여야 한다
    3) 좌표 4개는 모두 0~1 사이여야 한다 (정규화 규칙)
  [반환] 문제점 문자열 리스트. 비어있으면 정상.
  """
  problems = []

  # glob.glob으로 해당 디렉토리의 모든 txt 파일 탐색
  for path in glob.glob(os.path.join(label_dir, "*.txt")):
    # 파일 안전하게 open (UTF-8 인코딩 및 컨텍스트 매니저 사용)
    with open(path, "r", encoding="utf-8") as f:
      for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
          continue  # 빈 줄 건너뜀
        
        parts = line.split()
        if len(parts) != 5:  # ① 값 개수 검사
          problems.append(f"{os.path.basename(path)}:{i} 값 개수 {len(parts)} (5개여야 함)")
          continue
        
        try:
          cls = int(parts[0])
          vals = [float(v) for v in parts[1:]]
        except ValueError:
          problems.append(f"{os.path.basename(path)}:{i} 숫자 변환 실패 (유효하지 않은 데이터)")
          continue
        
        if not (0 <= cls < num_classes):  # ② 클래스 범위 검사
          problems.append(f"{os.path.basename(path)}:{i} class {cls} 범위초과")
          continue
        
        if any(v < 0 or v > 1 for v in vals):  # ③ 좌표 범위 검사
          problems.append(f"{os.path.basename(path)}:{i} 좌표가 0~1 범위 밖")

  # [교정] 모든 파일의 루프가 끝난 뒤 반환해야 하므로 들여쓰기를 for 루프 밖으로 수정
  return problems

# ── 실행 검증 ──────────────────────────────────────────────────
if __name__ == "__main__":
  current_dir = os.path.dirname(os.path.abspath(__file__))
  # 실제 라벨 텍스트들이 모여있는 디렉토리 설정
  target_label_dir = os.path.join(current_dir, "labels", "train")

  bad = check_labels(target_label_dir, num_classes=1)
  
  if not bad:
    print("[OK] 모든 라벨 파일이 정상적입니다.")
  else:
    print(f"[WARNING] 문제 {len(bad)}건이 감지되었습니다:")
    for problem in bad:
      print(f"  -> {problem}")

