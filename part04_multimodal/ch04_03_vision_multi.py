# 한번의 api호출로 이미지 여러장을 분석 시키기

import json, os, re, base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from ch04_04_01_visionModel_basic import image_to_base64
from ch04_02_vision_api_call import json_parse


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_multiple_images(image_paths:list[str], prompt:str) -> dict:
  """
    이미지 여러 장을 한 번의 API 호출로 비교 분석한다.

    핵심 아이디어:
        content 리스트에 이미지 블록을 여러 개 넣으면
        LLM이 모든 이미지를 동시에 보면서 비교·분석한다.

        [이미지1 블록, 이미지2 블록, 이미지3 블록, 텍스트 블록]

    Args:
        image_paths : 분석할 이미지 파일 경로 리스트
        prompt      : 분석 지시
  """

  # 이미지 블록들을 리스트로 조합
  content_blocks = []
  for i, path in enumerate(image_paths, start=1) : 
    b64, mt = image_to_base64(path)
    content_blocks.append(
      {
        "type": "image_url",
        "image_url":{
          "url":f"data:{mt};base64,{b64}", "detail":"low"
        }
      }
    )
    # 이미지 설명 텍스트 추가
    content_blocks.append(
      {"type":"text", "text":f"이미지 {i} :"}
    )

  # [중요] 루프가 종료된 뒤 모든 이미지 목록 뒤에 최종 지시 prompt를 텍스트 블록으로 추가합니다.
  content_blocks.append(
    {"type": "text", "text": prompt}
  )

  # [중요] 루프 외부에서 한 번만 API를 호출합니다.
  resp = client.chat.completions.create(
    model="gpt-4o",
    messages = [
      {
        "role":"user",
        "content":content_blocks
      }
    ],
    max_tokens=600
  )

  # [타입 안전성 가드] OpenAI 응답 content가 str | None 이므로 None 검증 분기를 넣어 Pylance 경고 밑줄을 완전히 해결합니다.
  content = resp.choices[0].message.content
  if content is None:
    raise ValueError("OpenAI API 응답 content가 비어 있습니다. [None]")

  return json_parse(content)

  

# ── 실행 ──────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

image_files = [
  os.path.join(_SCRIPT_DIR, "vision_sample", "hamster.jpeg"),
  os.path.join(_SCRIPT_DIR, "vision_sample", "cat.jpeg"),
  os.path.join(_SCRIPT_DIR, "vision_sample", "blue_parrot.jpeg")
]

prompt = """위 이미지들을 순서대로 분석해서 아래 JSON 형식으로만 응답하세요.
{
  "images": [
    {"index": 1, "subject": "피사체", "description": "설명"},
    {"index": 2, "subject": "피사체", "description": "설명"},
    {"index": 3, "subject": "피사체", "description": "설명"}
  ],
  "common_theme": "세 이미지의 공통 주제"
}"""

print("이미지 로딩 중...")
result = analyze_multiple_images(image_files, prompt)
print("\n=== 분석 결과 ===")
print(json.dumps(result, ensure_ascii=False, indent=2))