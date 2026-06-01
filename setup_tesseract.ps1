# 1. 한글 traineddata 복사
Copy-Item -Path "D:\korea_IT\2025_LangChain_\al-cctv-platform\tessdata\kor.traineddata" -Destination "C:\Program Files\Tesseract-OCR\tessdata\" -Force

# 2. 시스템 PATH 환경 변수에 Tesseract 경로 추가 (중복 방지 체크 포함)
$targetPath = "C:\Program Files\Tesseract-OCR"
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($machinePath -notlike "*$targetPath*") {
    [Environment]::SetEnvironmentVariable("Path", $machinePath + ";" + $targetPath, "Machine")
}
