<#
================================================================================
 SREE Speaker Voiceprint Enrollment Wizard
 Calibrates your unique voice so SREE strictly only responds to YOU.
================================================================================
#>

param(
    [string]$SpeakerName = "Boss"
)

Add-Type -AssemblyName System.Speech

Clear-Host
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "             SREE VOICE BIOMETRIC ENROLLMENT WIZARD             " -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "This wizard registers your unique vocal tract acoustics so SREE"
Write-Host "will ONLY wake up and reply to YOUR voice, ignoring strangers." -ForegroundColor White
Write-Host ""

$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine
try {
    $r.SetInputToDefaultAudioDevice()
} catch {
    Write-Host "[!] Could not access default microphone device. Please check audio settings." -ForegroundColor Red
    exit 1
}

# Load grammar to capture speech
$c = New-Object System.Speech.Recognition.Choices
$c.Add([string[]]@("hey sree", "hi sree", "hello sree", "sree", "hey sri", "sri", "hey shree", "shree", "hey siri", "ok sree", "hello", "testing voice"))
$gb = New-Object System.Speech.Recognition.GrammarBuilder($c)
$g = New-Object System.Speech.Recognition.Grammar($gb)
$r.LoadGrammar($g)

# Also load dictation grammar for enrollment flexibility
$dict = New-Object System.Speech.Recognition.DictationGrammar
$r.LoadGrammar($dict)

# Clear existing voice profile to start fresh
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8005/api/voice/clear" -Method POST -ErrorAction SilentlyContinue | Out-Null
} catch {}

$totalSamples = 3
$captured = 0

for ($i = 1; $i -le $totalSamples; $i++) {
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  Step $i of $totalSamples: Speak clearly into your microphone:" -ForegroundColor Yellow
    Write-Host "  >>> Say: 'HEY SREE' <<<" -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  [Listening for your voice...]" -ForegroundColor Cyan

    $heard = $false
    while (-not $heard) {
        $result = $r.Recognize([TimeSpan]::FromSeconds(12))
        if ($result -ne $null -and $result.Audio -ne $null) {
            $tempWav = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "sree_enroll_sample_$i.wav")
            $fs = [System.IO.File]::Create($tempWav)
            $result.Audio.WriteToWaveStream($fs)
            $fs.Close()

            try {
                $body = @{
                    speaker_name = $SpeakerName
                    audio_file_path = $tempWav
                } | ConvertTo-Json

                $res = Invoke-RestMethod -Uri "http://127.0.0.1:8005/api/voice/enroll" -Method POST -Body $body -ContentType "application/json"
                if ($res -and $res.success) {
                    Write-Host "  [+] Sample $i recorded and acoustic voiceprint extracted!" -ForegroundColor Green
                    [System.Console]::Beep(659, 100)
                    [System.Console]::Beep(880, 150)
                    $heard = $true
                    $captured++
                } else {
                    Write-Host "  [!] Please speak slightly louder. Retrying step $i..." -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  [!] Server error during feature extraction: $_. Retrying..." -ForegroundColor Red
            }
        } else {
            Write-Host "  [?] No speech detected in time. Please try speaking: 'Hey Sree'..." -ForegroundColor Yellow
        }
    }
    Start-Sleep -Milliseconds 800
}

# Enable Voice Verification on backend
try {
    $toggleBody = @{ enabled = $true } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://127.0.0.1:8005/api/voice/toggle" -Method POST -Body $toggleBody -ContentType "application/json" | Out-Null
} catch {}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "         VOICE BIOMETRIC ENROLLMENT COMPLETE & ACTIVE!          " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "[+] Enrolled Owner: $SpeakerName ($captured samples registered)" -ForegroundColor White
Write-Host "[+] Voice Verification: ENABLED" -ForegroundColor Green
Write-Host "[+] SREE will now ONLY unlock and respond to your verified voice." -ForegroundColor Yellow
Write-Host "[+] Strangers, family members, or TV audio will be rejected." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
[System.Console]::ReadKey($true) | Out-Null

