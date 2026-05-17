param(
    [switch]$DryRun
)

Write-Host "Windows desktop integration is a v1.1.0 stub."
Write-Host "No shortcuts, startup tasks, registry keys, file actions, or protocol handlers were modified."
if ($DryRun) {
    Write-Host "Dry run complete."
}
