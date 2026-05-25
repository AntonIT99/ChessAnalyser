# build.ps1
# Builds ChessAnalyser.exe from the current source code.

$ErrorActionPreference = "Stop"

# === Configuration ===
$ProjectName = "ChessAnalyser"
$EntryFile = "main.py"
$VenvPython = ".\.venv\Scripts\python.exe"

# Asset folders/files to bundle into the executable.
# Format: @{ Source = "local path"; Target = "path inside bundled app" }
$DataFiles = @(
    @{ Source = "assets"; Target = "assets" }
)

# Optional sanity checks for important runtime files.
$RequiredFiles = @(
    "assets\fonts\seguisym.ttf"
)

# Use $true for one-folder build, $false for single exe.
# onedir is usually more reliable/faster for pygame apps.
$UseOneDir = $false

# Use $true for GUI apps without console window.
# Keep $false while debugging runtime problems.
$Windowed = $true

Write-Host "=== Building $ProjectName ===" -ForegroundColor Cyan

# === Checks ===
if (!(Test-Path $VenvPython)) {
    Write-Host "Virtual environment not found: $VenvPython" -ForegroundColor Red
    Write-Host "Create it first, for example:" -ForegroundColor Yellow
    Write-Host "  py -3.13 -m venv .venv"
    exit 1
}

if (!(Test-Path $EntryFile)) {
    Write-Host "Entry file not found: $EntryFile" -ForegroundColor Red
    exit 1
}

foreach ($file in $RequiredFiles) {
    if (!(Test-Path $file)) {
        Write-Host "Required file not found: $file" -ForegroundColor Red
        Write-Host "The build may succeed, but the program will probably fail at runtime." -ForegroundColor Yellow
        exit 1
    }
}

foreach ($data in $DataFiles) {
    if (!(Test-Path $data.Source)) {
        Write-Host "Asset/data path not found: $($data.Source)" -ForegroundColor Yellow
        Write-Host "Skipping this data path."
    }
}

# === Ensure pip tooling is healthy ===
Write-Host "Upgrading build tooling..."
& $VenvPython -m pip install --upgrade pip setuptools wheel

# === Ensure PyInstaller is installed ===
Write-Host "Checking PyInstaller..."
& $VenvPython -m pip show pyinstaller *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    & $VenvPython -m pip install pyinstaller
}

# === Clean old build output ===
Write-Host "Cleaning old build output..."
Remove-Item -Recurse -Force ".\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\dist" -ErrorAction SilentlyContinue
Remove-Item -Force ".\$ProjectName.spec" -ErrorAction SilentlyContinue

# === Build args ===
$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--name", $ProjectName,
    "--clean"
)

if ($UseOneDir) {
    $pyInstallerArgs += "--onedir"
} else {
    $pyInstallerArgs += "--onefile"
}

if ($Windowed) {
    $pyInstallerArgs += "--windowed"
}

foreach ($data in $DataFiles) {
    if (Test-Path $data.Source) {
        $pyInstallerArgs += @("--add-data", "$($data.Source);$($data.Target)")
    }
}

$pyInstallerArgs += $EntryFile

# === Build ===
Write-Host "Running PyInstaller..."
Write-Host "$VenvPython $($pyInstallerArgs -join ' ')" -ForegroundColor DarkGray

& $VenvPython @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Build successful!" -ForegroundColor Green

if ($UseOneDir) {
    $ExePath = ".\dist\$ProjectName\$ProjectName.exe"
} else {
    $ExePath = ".\dist\$ProjectName.exe"
}

Write-Host "Executable:"
Write-Host "  $ExePath" -ForegroundColor Cyan

Write-Host ""
Write-Host "Run it with:"
Write-Host "  $ExePath" -ForegroundColor Cyan