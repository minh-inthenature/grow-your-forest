param(
    [string]$AudioPath = ""
)

Add-Type -AssemblyName PresentationCore

if (-not $AudioPath -or -not (Test-Path $AudioPath)) {
    Write-Error "Audio file not found: $AudioPath"
    exit 1
}

$mediaPlayer = New-Object System.Windows.Media.MediaPlayer
$mediaPlayer.Open([System.Uri]$AudioPath)
$mediaPlayer.Volume = 0.7

# Infinite loop handler
$mediaPlayer.add_MediaEnded({
    $mediaPlayer.Position = [System.TimeSpan]::Zero
    $mediaPlayer.Play()
})

Write-Output "READY"
[Console]::Out.Flush()

# Command loop from stdin
$running = $true
while ($running) {
    $line = [Console]::ReadLine()
    if ($null -eq $line) { break }
    $cmd = $line.Trim().ToUpperInvariant()

    if ($cmd -eq "PLAY") {
        $mediaPlayer.Play()
        Write-Output "OK_PLAYING"
        [Console]::Out.Flush()
    }
    elseif ($cmd -eq "STOP") {
        $mediaPlayer.Pause()
        $mediaPlayer.Position = [System.TimeSpan]::Zero
        Write-Output "OK_STOPPED"
        [Console]::Out.Flush()
    }
    elseif ($cmd.StartsWith("VOLUME ")) {
        $parts = $cmd.Split(' ')
        if ($parts.Length -ge 2) {
            $volInt = [int]$parts[1]
            $volVal = [Math]::Max(0.0, [Math]::Min(1.0, ($volInt / 100.0)))
            $mediaPlayer.Volume = $volVal
            Write-Output "OK_VOLUME $volInt"
            [Console]::Out.Flush()
        }
    }
    elseif ($cmd -eq "QUIT") {
        $mediaPlayer.Stop()
        $mediaPlayer.Close()
        $running = $false
        Write-Output "OK_QUIT"
        [Console]::Out.Flush()
    }
}
