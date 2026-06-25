param(
    [switch]$Mirror,
    [string[]]$Targets
)

$ErrorActionPreference = "Stop"
$Source = (Resolve-Path -LiteralPath $PSScriptRoot).Path

if (-not $Targets -or $Targets.Count -eq 0) {
    $Targets = @(
        (Join-Path $env:USERPROFILE ".claude\skills\lby-shixi")
    )
    $desktopSkill = Join-Path $env:USERPROFILE "Desktop\lby-shixi"
    if (Test-Path -LiteralPath $desktopSkill) {
        $Targets += $desktopSkill
    }
    $dExample = "D:\document\大三下\地理大数据分析与应用\lby-shixi-example\lby-shixi"
    if (Test-Path -LiteralPath $dExample) {
        $Targets += $dExample
    }
}

$mode = if ($Mirror) { "/MIR" } else { "/E" }
$excludeDirs = @(".git", "__pycache__", ".pytest_cache", ".mypy_cache")
$excludeFiles = @("*.pyc", "*.pyo")

foreach ($target in $Targets) {
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    $args = @($Source, $target, $mode, "/R:2", "/W:1", "/XD") + $excludeDirs + @("/XF") + $excludeFiles
    Write-Host "Sync lby-shixi: $Source -> $target ($mode)"
    & robocopy @args | Out-Host
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed for $target with exit code $LASTEXITCODE"
    }
}

Write-Host "lby-shixi sync complete."
