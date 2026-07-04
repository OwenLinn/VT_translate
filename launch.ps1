# YouTube Live Translator Overlay - Launch Script
# Double-click launch.bat to run this script

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDir

chcp 65001 | Out-Null
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  YouTube Live Translator Overlay" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------- prerequisites ----------
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[ERROR] .venv not found. Please create a virtual environment first." -ForegroundColor Red
    exit 1
}

# ---------- API Key ----------
Write-Host "[1/6] DeepSeek API Key" -ForegroundColor Yellow
Write-Host "  Press Enter to skip; echo mode will be used (no translation)" -ForegroundColor DarkGray
$apiKey = Read-Host "  API Key"
if ($apiKey) {
    $env:DEEPSEEK_API_KEY = $apiKey
    $translationMode = "deepseek"
} else {
    Write-Host "  -> Skipped. Using echo mode." -ForegroundColor DarkGray
    $translationMode = "echo"
}
Write-Host ""

# ---------- Source Language ----------
Write-Host "[2/6] Source Language" -ForegroundColor Yellow
Write-Host "  [1] ja - Japanese" -ForegroundColor White
Write-Host "  [2] en - English" -ForegroundColor White
Write-Host "  [3] auto - Auto detect" -ForegroundColor White
$srcChoice = Read-Host "  Choose [1]"
switch ($srcChoice) {
    "2" { $sourceLang = "en" }
    "3" { $sourceLang = "auto" }
    default { $sourceLang = "ja" }
}
Write-Host ""

# ---------- Target Language ----------
Write-Host "[3/6] Target Language" -ForegroundColor Yellow
Write-Host "  [1] zh-TW - Traditional Chinese" -ForegroundColor White
Write-Host "  [2] zh-CN - Simplified Chinese" -ForegroundColor White
$tgtChoice = Read-Host "  Choose [1]"
if ($tgtChoice -eq "2") { $targetLang = "zh-CN" } else { $targetLang = "zh-TW" }
Write-Host ""

# ---------- ASR Model & Device ----------
Write-Host "[4/6] ASR Model & Device" -ForegroundColor Yellow
Write-Host "  [1] large-v3 + CUDA (best quality, requires GPU)" -ForegroundColor White
Write-Host "  [2] large-v3 + CPU (good quality, slower)" -ForegroundColor White
Write-Host "  [3] tiny + CUDA (fast smoke test, low quality)" -ForegroundColor White
Write-Host "  [4] tiny + CPU (fast smoke test, no GPU needed)" -ForegroundColor White
$asrChoice = Read-Host "  Choose [1]"
switch ($asrChoice) {
    "2" { $model = "models\faster-whisper-large-v3"; $device = "cpu"; $computeType = "int8" }
    "3" { $model = "tiny"; $device = "cuda"; $computeType = "float16" }
    "4" { $model = "tiny"; $device = "cpu"; $computeType = "int8" }
    default { $model = "models\faster-whisper-large-v3"; $device = "cuda"; $computeType = "float16" }
}
Write-Host ""

# ---------- Overlay Type ----------
Write-Host "[5/6] Overlay Frontend" -ForegroundColor Yellow
Write-Host "  [1] Electron (multi-window, recommended)" -ForegroundColor White
Write-Host "  [2] Widgets (PySide6, built-in)" -ForegroundColor White
$uiChoice = Read-Host "  Choose [1]"
$useElectron = ($uiChoice -ne "2")
Write-Host ""

# ---------- Audio Source ----------
Write-Host "[6/6] Audio Source" -ForegroundColor Yellow
Write-Host "  [1] Live loopback (capture system audio)" -ForegroundColor White
Write-Host "  [2] Local audio file" -ForegroundColor White
$audioChoice = Read-Host "  Choose [1]"
if ($audioChoice -eq "2") {
    $audioFile = Read-Host "  Audio file path"
    $audioArgs = @("--audio-file", $audioFile, "--max-audio-seconds", "60", "--close-on-finish", "--auto-close-seconds", "30")
} else {
    $audioArgs = @("--continuous-loopback")
}
Write-Host ""

# ---------- CUDA PATH ----------
if ($device -eq "cuda") {
    $cudaBin = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin"
    if (Test-Path $cudaBin) {
        $env:PATH = "$cudaBin;$env:PATH"
        Write-Host "[INFO] CUDA Toolkit bin added to PATH" -ForegroundColor DarkGray
    } else {
        Write-Host "[WARN] CUDA Toolkit v12.0 bin not found at: $cudaBin" -ForegroundColor DarkYellow
        Write-Host "       If CUDA fails, try --device cpu instead." -ForegroundColor DarkYellow
    }
}

# ---------- Build Command ----------
$pythonExe = ".venv\Scripts\python.exe"
$pythonArgs = @("-m", "yt_live_translator.main")

if ($useElectron) {
    $pythonArgs += "--electron-overlay-live"
} else {
    $pythonArgs += "--overlay-pipeline-test"
}

$pythonArgs += @(
    "--source-lang", $sourceLang,
    "--target", $targetLang,
    "--translation", $translationMode,
    "--model", $model,
    "--device", $device,
    "--compute-type", $computeType,
    "--streaming-strategy", "local_agreement"
)

if ($translationMode -eq "deepseek") {
    $pythonArgs += @("--deepseek-timeout", "60")
}

$pythonArgs += $audioArgs
$displayCommand = (@($pythonExe) + $pythonArgs) -join " "

# ---------- Summary ----------
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Launch Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  API Key      : " -NoNewline
if ($apiKey) { Write-Host "**** (set)" -ForegroundColor Green } else { Write-Host "not set (echo mode)" -ForegroundColor DarkYellow }
Write-Host "  Source       : $sourceLang" -ForegroundColor White
Write-Host "  Target       : $targetLang" -ForegroundColor White
Write-Host "  Translation  : $translationMode" -ForegroundColor White
Write-Host "  Model        : $model" -ForegroundColor White
Write-Host "  Device       : $device / $computeType" -ForegroundColor White
Write-Host "  Overlay      : " -NoNewline
if ($useElectron) { Write-Host "Electron" -ForegroundColor White } else { Write-Host "Widgets (PySide6)" -ForegroundColor White }
Write-Host "  Audio        : " -NoNewline
if ($audioChoice -eq "2") { Write-Host "Local file" -ForegroundColor White } else { Write-Host "Live loopback" -ForegroundColor White }
Write-Host ""

if ($useElectron) {
    Write-Host "[INFO] Electron frontend will be started automatically by Python." -ForegroundColor DarkGray
    Write-Host ""
}

$confirm = Read-Host "Press Enter to launch (or type q to quit)"
if ($confirm -eq "q") {
    Write-Host "Cancelled." -ForegroundColor DarkGray
    exit 0
}

Write-Host "`nLaunching..." -ForegroundColor Green
Write-Host $displayCommand -ForegroundColor DarkGray
Write-Host ""

& $pythonExe @pythonArgs
