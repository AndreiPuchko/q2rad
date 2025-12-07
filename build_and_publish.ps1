# --- 1. Bump version ---
$versionFile = "pyproject.toml"
$content = Get-Content $versionFile -Raw

# Remove BOM if present
if ($content.Length -gt 0 -and $content[0] -eq [char]0xFEFF) {
    Write-Host "BOM detected in pyproject.toml - removing..."
    $content = $content.Substring(1)
}

# Extract current version
$versionMatch = [regex]::Match($content, "version\s*=\s*""([\d\.]+)""")
if (-not $versionMatch.Success) {
    Write-Host "ERROR: version not found in pyproject.toml"
    exit 1
}

$version = $versionMatch.Groups[1].Value

$parts = $version.Split(".")
$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2]

# PATCH bump
$patch++
$newVersion = "$major.$minor.$patch"

# Update version in pyproject.toml (BOM-safe)
$content = $content -replace "version\s*=\s*""[\d\.]+""", "version = ""$newVersion"""

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($versionFile, $content, $utf8NoBom)

Write-Host "Version bumped: $version -> $newVersion"

# --- Generate version.py inside package folder ---
$currentDir = Get-Location
$parentFolderName = Split-Path $currentDir -Leaf
$versionPyPath = Join-Path $parentFolderName "version.py"

$versionPyContent = "__version__ = ""$newVersion"""
[System.IO.File]::WriteAllText($versionPyPath, $versionPyContent, $utf8NoBom)

Write-Host "version.py generated: $versionPyPath"

# --- 2. Build & Publish to PyPI ---
poetry build
poetry publish

# --- 3. Read version from version.py ---
$currentDir = Get-Location
$parentFolderName = Split-Path $currentDir -Leaf

$versionFile = Join-Path $parentFolderName "version.py"
$version = Get-Content $versionFile

$version = ($version | Select-String "__version__\s*=\s*""(.+)""").Matches[0].Groups[1].Value

Write-Host "Package name: $parentFolderName"
Write-Host "Version: $version"



$tag = "v$newVersion"

git tag $tag
git push
git push origin $tag

# -----------------------------
# 10. make Release Notes из git log
# -----------------------------

$prevTag = git tag --sort=-v:refname | Select-Object -Skip 1 -First 1

if ($prevTag) {
    $releaseNotes = git log "$prevTag..$tag" --pretty=format:"- %s"
} else {
    $releaseNotes = git log $tag --pretty=format:"- %s"
}

if (-not $releaseNotes) {
    $releaseNotes = "- Initial release"
}

$releaseFile = "release_notes.txt"
Set-Content $releaseFile $releaseNotes -Encoding UTF8

Write-Host "✅ Release notes generated"

# -----------------------------
# 11. GitHub Release
# -----------------------------

gh release create $tag `
    dist/* `
    --title "Release $tag" `
    --notes-file $releaseFile

Remove-Item $releaseFile

Write-Host "✅✅✅ Release $tag created and uploaded for $ProjectName!" -ForegroundColor Green
