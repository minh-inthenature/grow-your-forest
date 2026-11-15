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

# Non-blocking command + loop watchdog (MediaEnded does not fire without a WPF Dispatcher pump)
$running = $true
$isPlaying = $false
$lastPos = -1.0
$stallTicks = 0
$readTask = [Console]::In.ReadLineAsync()

while ($running) {
    if ($readTask.IsCompleted) {
        $line = $readTask.Result
        if ($null -eq $line) { break }
        $cmd = $line.Trim().ToUpperInvariant()

        if ($cmd -eq "PLAY") {
            $isPlaying = $true
            $stallTicks = 0
            $mediaPlayer.Play()
            Write-Output "OK_PLAYING"
            [Console]::Out.Flush()
        }
        elseif ($cmd -eq "STOP") {
            $isPlaying = $false
            $stallTicks = 0
            $lastPos = -1.0
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
            $isPlaying = $false
            $mediaPlayer.Stop()
            $mediaPlayer.Close()
            $running = $false
            Write-Output "OK_QUIT"
            [Console]::Out.Flush()
        }

        if ($running) {
            $readTask = [Console]::In.ReadLineAsync()
        }
    }

    if ($running -and $isPlaying -and $mediaPlayer.NaturalDuration.HasTimeSpan) {
        $dur = $mediaPlayer.NaturalDuration.TimeSpan.TotalSeconds
        $pos = $mediaPlayer.Position.TotalSeconds
        if ($dur -gt 0 -and $pos -ge ($dur - 0.35)) {
            $mediaPlayer.Position = [System.TimeSpan]::Zero
            $mediaPlayer.Play()
            $lastPos = 0.0
            $stallTicks = 0
        }
        elseif ($pos -gt 0 -and $pos -eq $lastPos) {
            $stallTicks++
            if ($stallTicks -ge 3) {
                $mediaPlayer.Position = [System.TimeSpan]::Zero
                $mediaPlayer.Play()
                $lastPos = 0.0
                $stallTicks = 0
            }
        }
        else {
            $lastPos = $pos
            $stallTicks = 0
        }
    }

    if ($running) {
        Start-Sleep -Milliseconds 150
    }
}
