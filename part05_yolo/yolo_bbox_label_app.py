import base64
import re
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DATASET_DIR = APP_DIR / "manual_labels"
IMAGE_DIR = DATASET_DIR / "images"
LABEL_DIR = DATASET_DIR / "labels"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
LABEL_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="YOLO BBox Labeling App")


class BBox(BaseModel):
    class_id: int = Field(ge=0)
    x1: float
    y1: float
    x2: float
    y2: float


class SaveRequest(BaseModel):
    filename: str
    image_data: str
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    boxes: list[BBox]


class ImageUrlRequest(BaseModel):
    url: str


def safe_stem(filename):
    stem = Path(filename).stem
    stem = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", stem).strip("_")
    return stem or "image"


def bbox_to_yolo(box, image_width, image_height):
    x1, x2 = sorted((max(0, box.x1), min(image_width, box.x2)))
    y1, y2 = sorted((max(0, box.y1), min(image_height, box.y2)))

    box_width = x2 - x1
    box_height = y2 - y1
    if box_width <= 1 or box_height <= 1:
        return None

    center_x = ((x1 + x2) / 2) / image_width
    center_y = ((y1 + y2) / 2) / image_height
    normalized_width = box_width / image_width
    normalized_height = box_height / image_height

    return (
        f"{box.class_id} {center_x:.6f} {center_y:.6f} "
        f"{normalized_width:.6f} {normalized_height:.6f}"
    )


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.post("/load-image-url")
async def load_image_url(request: ImageUrlRequest):
    """웹 이미지 URL을 받아 브라우저에서 사용할 data URL로 변환한다."""
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="http 또는 https 이미지 URL만 지원합니다.")

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15,
            headers=headers,
        ) as client:
            response = await client.get(request.url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail="웹 이미지를 불러오지 못했습니다.") from exc

    content_type = response.headers.get("content-type", "").split(";")[0]
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="입력한 URL이 이미지가 아닙니다.")
    if len(response.content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="15MB 이하 이미지만 지원합니다.")

    encoded = base64.b64encode(response.content).decode("ascii")
    filename = Path(httpx.URL(str(response.url)).path).name or "web_image"
    return {
        "image_data": f"data:{content_type};base64,{encoded}",
        "filename": filename,
    }


@app.post("/save-labels")
def save_labels(request: SaveRequest):
    try:
        header, encoded = request.image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
    except (ValueError, base64.binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="올바르지 않은 이미지 데이터입니다.") from exc

    extension_match = re.search(r"image/(png|jpeg|jpg|webp)", header)
    extension = extension_match.group(1) if extension_match else "png"
    extension = "jpg" if extension == "jpeg" else extension

    stem = safe_stem(request.filename)
    image_path = IMAGE_DIR / f"{stem}.{extension}"
    label_path = LABEL_DIR / f"{stem}.txt"

    label_lines = []
    for box in request.boxes:
        label = bbox_to_yolo(box, request.image_width, request.image_height)
        if label is not None:
            label_lines.append(label)

    image_path.write_bytes(image_bytes)
    label_path.write_text("\n".join(label_lines), encoding="utf-8")

    return {
        "message": f"{len(label_lines)}개 bbox 저장 완료",
        "labels": label_lines,
        "image_path": str(image_path),
        "label_path": str(label_path),
        "download_url": f"/download/{label_path.name}",
    }


@app.get("/download/{filename}")
def download_label(filename: str):
    safe_name = Path(filename).name
    label_path = LABEL_DIR / safe_name
    if not label_path.exists():
        raise HTTPException(status_code=404, detail="라벨 파일을 찾을 수 없습니다.")
    return FileResponse(label_path, filename=safe_name, media_type="text/plain")


HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>YOLO BBox Labeling App</title>
  <!-- 구글 폰트 임포트 (Cormorant Garamond & Inter & JetBrains Mono) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    /* Claude Design System Tokens */
    :root {
      --color-canvas: #faf9f5;
      --color-surface-soft: #f5f0e8;
      --color-surface-card: #efe9de;
      --color-surface-dark: #181715;
      --color-surface-dark-elevated: #252320;
      --color-surface-dark-soft: #1f1e1b;
      --color-primary: #cc785c;
      --color-primary-active: #a9583e;
      --color-ink: #141413;
      --color-body: #3d3d3a;
      --color-muted: #6c6a64;
      --color-muted-soft: #8e8b82;
      --color-hairline: #e6dfd8;
      --color-on-primary: #ffffff;
      --color-on-dark: #faf9f5;
      --color-on-dark-soft: #a09d96;
      --color-error: #c64545;
      --color-success: #5db872;
    }

    * { box-sizing: border-box; }
    
    body {
      margin: 0;
      padding: 32px;
      color: var(--color-body);
      background-color: var(--color-canvas);
      font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
      -webkit-font-smoothing: antialiased;
    }

    h1 {
      font-family: "Cormorant Garamond", Georgia, serif;
      font-size: 38px;
      font-weight: 500;
      color: var(--color-ink);
      margin-top: 0;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }

    h3 {
      font-family: "Cormorant Garamond", Georgia, serif;
      font-size: 22px;
      font-weight: 500;
      color: var(--color-ink);
      margin-top: 0;
      margin-bottom: 12px;
    }

    .hint {
      font-size: 14px;
      color: var(--color-muted);
      line-height: 1.6;
      margin-bottom: 24px;
      max-width: 800px;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 24px;
    }

    .panel {
      padding: 24px;
      border: 1px solid var(--color-hairline);
      border-radius: 12px;
      background-color: var(--color-surface-card);
    }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 18px;
      align-items: center;
    }

    /* Inputs & Buttons Styling */
    input[type="text"], input[type="number"], input[type="url"], input[type="file"] {
      padding: 8px 12px;
      font-size: 14px;
      color: var(--color-ink);
      border: 1px solid var(--color-hairline);
      border-radius: 8px;
      background-color: var(--color-canvas);
      font-family: "Inter", sans-serif;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    input[type="text"]:focus, input[type="number"]:focus, input[type="url"]:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(204, 120, 92, 0.15);
    }

    /* Custom File Input styling */
    input[type="file"] {
      font-size: 13px;
      max-width: 200px;
    }

    button {
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 500;
      color: var(--color-ink);
      border: 1px solid var(--color-hairline);
      border-radius: 8px;
      background-color: var(--color-canvas);
      cursor: pointer;
      font-family: "Inter", sans-serif;
      transition: background-color 0.2s, border-color 0.2s, color 0.2s;
    }

    button:hover {
      background-color: var(--color-surface-soft);
      border-color: var(--color-muted-soft);
    }

    /* Primary Coral Button */
    #saveButton {
      background-color: var(--color-primary);
      color: var(--color-on-primary);
      border-color: var(--color-primary);
    }

    #saveButton:hover {
      background-color: var(--color-primary-active);
      border-color: var(--color-primary-active);
    }

    /* Green Clipboard Button */
    #pasteButton {
      background-color: #f5f0e8;
      border-color: var(--color-hairline);
    }

    #pasteButton:hover {
      background-color: var(--color-surface-card);
    }

    #pasteZone {
      margin-bottom: 18px;
      padding: 16px;
      text-align: center;
      border: 2px dashed var(--color-muted-soft);
      border-radius: 8px;
      color: var(--color-muted);
      font-size: 14px;
      background-color: var(--color-canvas);
      transition: border-color 0.2s, background-color 0.2s, color 0.2s;
      outline: none;
    }

    #pasteZone.active, #canvasWrap.active {
      border-color: var(--color-primary);
      color: var(--color-primary-active);
      background-color: #fdf5f2;
    }

    /* Product mockup dark canvas wrap */
    #canvasWrap {
      overflow: auto;
      min-height: 520px;
      border: 1px solid var(--color-hairline);
      border-radius: 8px;
      background-color: var(--color-surface-dark);
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 16px;
    }

    canvas {
      display: block;
      cursor: crosshair;
      border-radius: 4px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }

    /* Sidebar details */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .sidebar-section {
      padding: 20px;
      border: 1px solid var(--color-hairline);
      border-radius: 12px;
      background-color: var(--color-surface-card);
    }

    /* Preview monospace code panel */
    pre {
      min-height: 200px;
      padding: 16px;
      margin: 0;
      overflow-x: auto;
      background-color: var(--color-surface-dark-soft);
      color: var(--color-on-dark);
      border-radius: 8px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
      line-height: 1.6;
      border: 1px solid #2e2c29;
    }

    .box-list-wrap {
      max-height: 250px;
      overflow-y: auto;
    }

    .box-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin: 8px 0;
      padding: 8px 12px;
      background-color: var(--color-canvas);
      border: 1px solid var(--color-hairline);
      border-radius: 6px;
      font-size: 13px;
    }

    .box-item span {
      font-family: "JetBrains Mono", monospace;
      color: var(--color-ink);
    }

    .delete {
      padding: 4px 8px;
      font-size: 11px;
      color: var(--color-on-primary);
      background-color: var(--color-error);
      border: none;
      border-radius: 4px;
    }

    .delete:hover {
      background-color: #aa3535;
    }

    #status {
      font-size: 13px;
      line-height: 1.5;
      padding: 12px;
      border-radius: 8px;
      background-color: var(--color-canvas);
      border: 1px solid var(--color-hairline);
      color: var(--color-body);
    }

    #status a {
      color: var(--color-primary);
      font-weight: 500;
      text-decoration: underline;
    }

    #status a:hover {
      color: var(--color-primary-active);
    }

    label {
      font-size: 13px;
      font-weight: 500;
      color: var(--color-ink);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    @media (max-width: 1024px) {
      .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <h1>YOLO BBox Labeling Tool</h1>
  <p class="hint">포토샵 크림 아키텍처 기반의 고품질 라벨링 도구입니다. 파일을 선택하거나 웹 이미지를 드롭하고, 이미지 위에서 마우스를 드래그하여 BBox를 그리세요.</p>

  <div class="layout">
    <section class="panel">
      <div class="toolbar">
        <input id="imageInput" type="file" accept="image/*">
        <button id="pasteButton">클립보드 붙여넣기</button>
        <input id="imageUrlInput" type="url" placeholder="웹 이미지 URL 붙여넣기" style="width:200px">
        <button id="urlButton">URL 로드</button>
        <label>저장명 <input id="filenameInput" type="text" value="pasted_image" style="width:120px"></label>
        <label>클래스 <input id="classId" type="number" min="0" value="0" style="width:60px"></label>
        <button id="undoButton">실행 취소</button>
        <button id="clearButton">초기화</button>
        <button id="saveButton">YOLO 저장</button>
      </div>
      <div id="pasteZone" tabindex="0">웹 이미지나 파일을 이곳에 끌어다 놓거나, 복사(Ctrl+V)하여 붙여넣으세요.</div>
      <div id="canvasWrap">
        <canvas id="canvas"></canvas>
      </div>
    </section>

    <div class="sidebar">
      <section class="sidebar-section">
        <h3>BBox 리스트</h3>
        <div id="boxList" class="box-list-wrap hint">아직 생성된 BBox가 없습니다.</div>
      </section>

      <section class="sidebar-section">
        <h3>YOLO 라벨 미리보기</h3>
        <pre id="labelPreview"></pre>
      </section>

      <section class="sidebar-section">
        <h3>상태 메시지</h3>
        <div id="status" class="hint">대기 중...</div>
      </section>
    </div>
  </div>

  <script>
    const imageInput = document.getElementById("imageInput");
    const filenameInput = document.getElementById("filenameInput");
    const pasteButton = document.getElementById("pasteButton");
    const pasteZone = document.getElementById("pasteZone");
    const canvasWrap = document.getElementById("canvasWrap");
    const imageUrlInput = document.getElementById("imageUrlInput");
    const urlButton = document.getElementById("urlButton");
    const classIdInput = document.getElementById("classId");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const boxList = document.getElementById("boxList");
    const labelPreview = document.getElementById("labelPreview");
    const status = document.getElementById("status");

    const image = new Image();
    let imageData = "";
    let filename = "";
    let boxes = [];
    let drawing = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;

    function loadImageFile(file, suggestedFilename=file.name) {
      if (!file || !file.type.startsWith("image/")) {
        status.textContent = "[Error] 올바른 이미지 파일이 아닙니다.";
        return;
      }

      filename = suggestedFilename;
      filenameInput.value = suggestedFilename.replace(/\.[^.]+$/, "");
      const reader = new FileReader();
      reader.onload = loadEvent => {
        imageData = loadEvent.target.result;
        image.onload = () => {
          canvas.width = image.naturalWidth;
          canvas.height = image.naturalHeight;
          boxes = [];
          redraw();
          updatePanels();
          status.textContent = `[로드 완료] ${filename} (${canvas.width} x ${canvas.height})`;
          pasteZone.classList.remove("active");
        };
        image.src = imageData;
      };
      reader.readAsDataURL(file);
    }

    function loadImageData(dataUrl, suggestedFilename="web_image.png") {
      filename = suggestedFilename;
      filenameInput.value = suggestedFilename.replace(/\.[^.]+$/, "");
      imageData = dataUrl;
      image.onload = () => {
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        boxes = [];
        redraw();
        updatePanels();
        status.textContent = `[로드 완료] ${filename} (${canvas.width} x ${canvas.height})`;
        pasteZone.classList.remove("active");
      };
      image.onerror = () => {
        status.textContent = "[Error] 이미지를 불러올 수 없습니다.";
        pasteZone.classList.remove("active");
      };
      image.src = imageData;
    }

    async function loadImageFromUrl(url) {
      if (url.startsWith("data:image/")) {
        loadImageData(url, "pasted_image.png");
        return;
      }
      if (!url || !/^https?:\/\//i.test(url)) {
        status.textContent = "[WARNING] 올바른 http/https 이미지 URL을 입력하세요.";
        return;
      }

      status.textContent = "웹 이미지 불러오는 중...";
      try {
        const response = await fetch("/load-image-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "웹 이미지를 불러오지 못했습니다.");
        loadImageData(result.image_data, result.filename);
      } catch (error) {
        status.textContent = `[Error] ${error.message}`;
        pasteZone.classList.remove("active");
      }
    }

    function imageUrlFromClipboard(clipboardData) {
      const html = clipboardData.getData("text/html");
      if (html) {
        const documentFromClipboard = new DOMParser().parseFromString(html, "text/html");
        const imageElement = documentFromClipboard.querySelector("img");
        if (imageElement?.src) return imageElement.src;
      }

      const text = clipboardData.getData("text/plain").trim();
      return /^https?:\/\/\S+$/i.test(text) ? text : "";
    }

    function imageUrlFromTransfer(dataTransfer) {
      const html = dataTransfer.getData("text/html");
      if (html) {
        const transferDocument = new DOMParser().parseFromString(html, "text/html");
        const imageElement = transferDocument.querySelector("img");
        if (imageElement?.src) return imageElement.src;
      }

      for (const type of ["text/uri-list", "URL", "text/plain"]) {
        const value = dataTransfer.getData(type).trim();
        const url = value.split(/\r?\n/).find(line => (
          line && !line.startsWith("#") && /^https?:\/\/\S+$/i.test(line)
        ));
        if (url) return url;
      }
      return "";
    }

    function setDropActive(active) {
      pasteZone.classList.toggle("active", active);
      canvasWrap.classList.toggle("active", active);
    }

    async function loadDroppedImage(dataTransfer) {
      const imageFile = [...dataTransfer.files].find(file => file.type.startsWith("image/"));
      if (imageFile) {
        loadImageFile(imageFile);
        return;
      }

      const imageUrl = imageUrlFromTransfer(dataTransfer);
      if (imageUrl) {
        imageUrlInput.value = imageUrl;
        await loadImageFromUrl(imageUrl);
        return;
      }
      status.textContent = "[WARNING] 이미지 파일 또는 이미지 URL을 찾지 못했습니다.";
    }

    imageInput.addEventListener("change", event => {
      const file = event.target.files[0];
      if (!file) return;
      loadImageFile(file);
    });

    [pasteZone, canvasWrap].forEach(dropTarget => {
      dropTarget.addEventListener("dragenter", event => {
        event.preventDefault();
        setDropActive(true);
      });
      dropTarget.addEventListener("dragover", event => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
        setDropActive(true);
      });
      dropTarget.addEventListener("dragleave", event => {
        if (!dropTarget.contains(event.relatedTarget)) setDropActive(false);
      });
      dropTarget.addEventListener("drop", async event => {
        event.preventDefault();
        setDropActive(false);
        await loadDroppedImage(event.dataTransfer);
      });
    });

    document.addEventListener("paste", async event => {
      if (!event.clipboardData) return;
      const imageItem = [...event.clipboardData.items].find(item => item.type.startsWith("image/"));
      const imageUrl = imageUrlFromClipboard(event.clipboardData);
      if (!imageItem && !imageUrl) {
        status.textContent = "[WARNING] 클립보드에 이미지 데이터가 없습니다.";
        return;
      }
      event.preventDefault();
      pasteZone.classList.add("active");
      if (imageItem) {
        const extension = imageItem.type.split("/")[1].replace("jpeg", "jpg");
        loadImageFile(imageItem.getAsFile(), `pasted_image.${extension}`);
        return;
      }
      imageUrlInput.value = imageUrl;
      await loadImageFromUrl(imageUrl);
    });

    pasteButton.addEventListener("click", async () => {
      try {
        const clipboardItems = await navigator.clipboard.read();
        for (const clipboardItem of clipboardItems) {
          const imageType = clipboardItem.types.find(type => type.startsWith("image/"));
          if (!imageType) continue;

          pasteZone.classList.add("active");
          const blob = await clipboardItem.getType(imageType);
          const extension = imageType.split("/")[1].replace("jpeg", "jpg");
          loadImageFile(blob, `pasted_image.${extension}`);
          return;
        }
        status.textContent = "[WARNING] 클립보드에서 이미지를 찾지 못했습니다.";
      } catch (error) {
        status.textContent = "[WARNING] 권한이 차단되었습니다. 복사 후 단축키(Ctrl+V)를 사용하세요.";
      }
    });

    urlButton.addEventListener("click", () => loadImageFromUrl(imageUrlInput.value.trim()));

    function pointerPosition(event) {
      const rect = canvas.getBoundingClientRect();
      return {
        x: Math.max(0, Math.min(canvas.width, (event.clientX - rect.left) * canvas.width / rect.width)),
        y: Math.max(0, Math.min(canvas.height, (event.clientY - rect.top) * canvas.height / rect.height))
      };
    }

    canvas.addEventListener("pointerdown", event => {
      if (!image.src) return;
      const point = pointerPosition(event);
      drawing = true;
      startX = currentX = point.x;
      startY = currentY = point.y;
      canvas.setPointerCapture(event.pointerId);
    });

    canvas.addEventListener("pointermove", event => {
      if (!drawing) return;
      const point = pointerPosition(event);
      currentX = point.x;
      currentY = point.y;
      redraw(true);
    });

    canvas.addEventListener("pointerup", event => {
      if (!drawing) return;
      drawing = false;
      const point = pointerPosition(event);
      currentX = point.x;
      currentY = point.y;

      if (Math.abs(currentX - startX) > 3 && Math.abs(currentY - startY) > 3) {
        boxes.push({
          class_id: Number(classIdInput.value),
          x1: Math.min(startX, currentX),
          y1: Math.min(startY, currentY),
          x2: Math.max(startX, currentX),
          y2: Math.max(startY, currentY)
        });
      }
      redraw();
      updatePanels();
    });

    function drawBox(box, index, temporary=false) {
      const x = Math.min(box.x1, box.x2);
      const y = Math.min(box.y1, box.y2);
      const width = Math.abs(box.x2 - box.x1);
      const height = Math.abs(box.y2 - box.y1);

      ctx.strokeStyle = temporary ? "#e8a55a" : "#cc785c"; // Amber vs Coral
      ctx.lineWidth = Math.max(2, canvas.width / 500);
      ctx.strokeRect(x, y, width, height);
      ctx.fillStyle = temporary ? "#e8a55a" : "#cc785c";
      ctx.font = `${Math.max(14, canvas.width / 55)}px Inter`;
      ctx.fillText(temporary ? "drawing" : `#${index + 1} cls:${box.class_id}`, x + 4, Math.max(18, y - 5));
    }

    function redraw(showTemporary=false) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (image.src) ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      boxes.forEach((box, index) => drawBox(box, index));
      if (showTemporary) {
        drawBox({ class_id: Number(classIdInput.value), x1:startX, y1:startY, x2:currentX, y2:currentY }, boxes.length, true);
      }
    }

    function toYolo(box) {
      const centerX = ((box.x1 + box.x2) / 2) / canvas.width;
      const centerY = ((box.y1 + box.y2) / 2) / canvas.height;
      const width = (box.x2 - box.x1) / canvas.width;
      const height = (box.y2 - box.y1) / canvas.height;
      return `${box.class_id} ${centerX.toFixed(6)} ${centerY.toFixed(6)} ${width.toFixed(6)} ${height.toFixed(6)}`;
    }

    function updatePanels() {
      labelPreview.textContent = boxes.map(toYolo).join("\n");
      if (!boxes.length) {
        boxList.textContent = "아직 생성된 BBox가 없습니다.";
        return;
      }
      boxList.innerHTML = boxes.map((box, index) => `
        <div class="box-item">
          <span>#${index + 1} class ${box.class_id}: (${Math.round(box.x1)}, ${Math.round(box.y1)}) ~ (${Math.round(box.x2)}, ${Math.round(box.y2)})</span>
          <button class="delete" onclick="deleteBox(${index})">삭제</button>
        </div>
      `).join("");
    }

    window.deleteBox = index => {
      boxes.splice(index, 1);
      redraw();
      updatePanels();
    };

    document.getElementById("undoButton").addEventListener("click", () => {
      boxes.pop();
      redraw();
      updatePanels();
    });

    document.getElementById("clearButton").addEventListener("click", () => {
      boxes = [];
      redraw();
      updatePanels();
    });

    document.getElementById("saveButton").addEventListener("click", async () => {
      if (!imageData) {
        status.textContent = "[WARNING] 먼저 이미지를 로드하세요.";
        return;
      }

      status.textContent = "저장 중...";
      const requestedName = filenameInput.value.trim() || "pasted_image";
      const originalExtension = filename.includes(".") ? filename.split(".").pop() : "png";
      filename = `${requestedName.replace(/\.[^.]+$/, "")}.${originalExtension}`;

      const response = await fetch("/save-labels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename,
          image_data: imageData,
          image_width: canvas.width,
          image_height: canvas.height,
          boxes
        })
      });

      const result = await response.json();
      if (!response.ok) {
        status.textContent = `[Error] ${result.detail || "저장에 실패했습니다."}`;
        return;
      }
      status.innerHTML = `[OK] ${result.message}<br>이미지: ${result.image_path}<br>라벨: ${result.label_path}<br><a href="${result.download_url}" target="_blank">라벨 txt 다운로드</a>`;
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7861)
