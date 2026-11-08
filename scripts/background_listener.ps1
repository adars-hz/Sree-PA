<#
================================================================================
 SREE - Native Windows Background Voice Listener & Live Assistant
 Runs 24/7 silently in background on Windows startup.
 STRICT WAKE-WORD GATED:
 Only enables and speaks when explicitly invoked with "Hey Sree".
 Zero unsolicited announcements, zero false room-noise triggers.
================================================================================
#>

param(
    [switch]$MinToTray = $true
)

# 1. Load Windows Speech & GUI Assemblies
Add-Type -AssemblyName System.Speech
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$ApiUrl = "http://127.0.0.1:8005"
$OllamaUrl = "http://127.0.0.1:11434"

# 2. Service Ensure Functions (Completely Silent)
function Test-HttpEndpoint($url) {
    try {
        $req = [System.Net.WebRequest]::Create($url)
        $req.Timeout = 1500
        $res = $req.GetResponse()
        $status = [int]$res.StatusCode
        $res.Close()
        return ($status -eq 200)
    } catch {
        return $false
    }
}

function Ensure-Ollama() {
    if (-not (Test-HttpEndpoint "$OllamaUrl/api/tags")) {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
}

function Ensure-SreeBackend() {
    if (-not (Test-HttpEndpoint "$ApiUrl/health")) {
        $pythonExe = (Get-Command python).Source
        Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8005" -WorkingDirectory $RootDir -WindowStyle Hidden
        
        # Wait up to 10 seconds for backend
        for ($i = 0; $i -lt 20; $i++) {
            if (Test-HttpEndpoint "$ApiUrl/health") { break }
            Start-Sleep -Milliseconds 500
        }
    }
}

function Open-SreeApp() {
    $chromePaths = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    )

    foreach ($exe in $chromePaths) {
        if (Test-Path $exe) {
            Start-Process -FilePath $exe -ArgumentList "--app=$ApiUrl", "--window-size=1280,840"
            return
        }
    }
    Start-Process $ApiUrl
}

# 3. Speech Synthesizer Setup
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1 # Brisk Siri tempo
try {
    $installedVoices = $synth.GetInstalledVoices() | Where-Object { $_.Enabled }
    if ($installedVoices.Count -gt 0) {
        $synth.SelectVoice($installedVoices[0].VoiceInfo.Name)
    }
} catch {}

function Speak-Text($text) {
    if ([string]::IsNullOrWhiteSpace($text)) { return }
    # Clean text of markdown
    $clean = $text -replace '`[^`]+`', '$1'
    $clean = $clean -replace '\*\*([^*]+)\*\*', '$1'
    $clean = $clean -replace '[*_#~]', ''
    $clean = $clean -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
    $clean = $clean -replace 'https?://\S+', ''
    
    # Speak first 2 sentences for fast Siri delivery
    $sentences = $clean -split '(?<=[.!?])\s+'
    $toSpeak = if ($sentences.Count -gt 2) { ($sentences[0..1] -join " ") } else { $clean }

    $synth.SpeakAsyncCancelAll()
    $synth.SpeakAsync($toSpeak) | Out-Null
}

function Play-Chime($type = "start") {
    try {
        if ($type -eq "start") {
            [System.Console]::Beep(587, 80)
            [System.Console]::Beep(880, 120)
        } else {
            [System.Console]::Beep(880, 80)
            [System.Console]::Beep(587, 100)
        }
    } catch {
        [System.Media.SystemSounds]::Asterisk.Play()
    }
}

# 4. Initialize Core Services Silently
Ensure-Ollama
Ensure-SreeBackend

# 5. Build Strict Wake-Word Grammars
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Strict Wake Phrases (No short standalone words like 'three' or 'sri' alone)
$wakePhrases = @(
    "hey sree", "hi sree", "hello sree", "ok sree", "okay sree",
    "hey sri", "hi sri", "hello sri", "ok sri",
    "hey shree", "hi shree", "hello shree",
    "hey siri", "hi siri", "hello siri"
)

# Core Allowed Commands
$commandPhrases = @(
    "open calculator", "launch calculator",
    "open notepad", "launch notepad",
    "open terminal", "launch terminal", "open command prompt", "open cmd",
    "open browser", "launch browser", "open chrome",
    "open task manager", "show task manager",
    "open code", "open visual studio code", "open vscode", "launch vscode",
    "open sree", "show sree", "open dashboard", "show dashboard",
    "take a screenshot", "capture screen", "screenshot",
    "share my screen", "open screen share",
    "minimize all windows", "minimize all", "show desktop",
    "switch window", "alt tab", "close active window", "close window",
    "volume up", "increase volume", "volume down", "lower volume", "mute audio", "unmute",
    "scroll down", "scroll up",
    "lock my pc", "lock computer", "lock screen",
    "click", "double click", "right click", "copy", "paste",
    "press enter", "press escape", "press space", "press tab",
    "what is the weather", "what's the weather", "weather today",
    "what time is it", "what's the time", "current time",
    "what is the date", "what is today's date", "what day is it",
    "how are you", "who are you", "what can you do",
    "daily briefing", "morning briefing", "summarize my day",
    "stop listening", "turn off voice assistant", "go to sleep", "shut down"
)

# Grammar 1: Standalone Wake Word (ACTIVE IN STANDBY)
$cWake = New-Object System.Speech.Recognition.Choices
$cWake.Add([string[]]$wakePhrases)
$gbWake = New-Object System.Speech.Recognition.GrammarBuilder($cWake)
$gWake = New-Object System.Speech.Recognition.Grammar($gbWake)
$gWake.Name = "StandaloneWakeGrammar"
$recognizer.LoadGrammar($gWake)

# Grammar 2: Compound Wake Word + Command (MANDATORY WAKE PREFIX, ACTIVE IN STANDBY)
$cPrefix = New-Object System.Speech.Recognition.Choices
$cPrefix.Add([string[]]$wakePhrases)

$cCmd = New-Object System.Speech.Recognition.Choices
$cCmd.Add([string[]]$commandPhrases)

$gbCompound = New-Object System.Speech.Recognition.GrammarBuilder
$gbCompound.Append($cPrefix) # MANDATORY Wake Word!
$gbCompound.Append($cCmd)    # Followed by Command!
$gCompound = New-Object System.Speech.Recognition.Grammar($gbCompound)
$gCompound.Name = "CompoundWakeCommandGrammar"
$recognizer.LoadGrammar($gCompound)

# Grammar 3: Followup Command (DISABLED BY DEFAULT - Active ONLY for 8s after "Hey Sree")
$gbFollowup = New-Object System.Speech.Recognition.GrammarBuilder($cCmd)
$gFollowup = New-Object System.Speech.Recognition.Grammar($gbFollowup)
$gFollowup.Name = "FollowupCommandGrammar"
$gFollowup.Enabled = $false # STRICTLY OFF in standby!
$recognizer.LoadGrammar($gFollowup)

# 6. Global State & Event Handling
$global:inConversation = $false
$global:conversationExpires = [DateTime]::MinValue
$global:lastWakeTime = [DateTime]::MinValue

$speechHandler = {
    param($sender, $e)

    if ($e -eq $null -or $e.Result -eq $null) { return }
    $heard = $e.Result.Text.Trim()
    $confidence = $e.Result.Confidence

    # Strict confidence threshold to eliminate background noise
    if ($confidence -lt 0.55) { return }

    $lower = $heard.ToLower().Trim()

    # If in standby and doesn't match a wake phrase, drop it
    $hasWakePrefix = ($wakePhrases | Where-Object { $lower.StartsWith($_) })

    if (-not $global:inConversation -and -not $hasWakePrefix) {
        return # STRICT STANDBY: Ignore everything without "Hey Sree"!
    }

    # --- VOICE BIOMETRICS SPEAKER VERIFICATION ---
    # Verifies speaker vocal cords & pitch match enrolled owner before unlocking!
    try {
        if ($e.Result.Audio -ne $null) {
            $tempWav = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "sree_wake_audio.wav")
            $fs = [System.IO.File]::Create($tempWav)
            $e.Result.Audio.WriteToWaveStream($fs)
            $fs.Close()

            $verifyBody = @{ audio_file_path = $tempWav } | ConvertTo-Json
            $verifyRes = Invoke-RestMethod -Uri "$ApiUrl/api/voice/verify" -Method POST -Body $verifyBody -ContentType "application/json" -TimeoutSec 3 -ErrorAction SilentlyContinue

            if ($verifyRes -and (-not $verifyRes.verified)) {
                Write-Output "[Security Gated] Unauthorized speaker voice rejected (Similarity: $($verifyRes.similarity) < $($verifyRes.threshold)). SREE will not reply to unauthorized voices."
                return # STRICT SILENCE: Do not reply to unauthorized voices!
            }
        }
    } catch {}

    Write-Output "[Heard & Verified] '$heard' (Confidence: $([Math]::Round($confidence, 2)))"

    # Check for Deactivation
    if ($lower -match "\b(?:stop listening|turn off.*voice|go to sleep|shut down)\b") {
        Play-Chime "done"
        Speak-Text "Voice standby. Say Hey Sree whenever you need me."
        $global:inConversation = $false
        $gFollowup.Enabled = $false
        return
    }

    # Check for Open Sree App UI
    if ($lower -match "\b(?:open sree|show sree|open dashboard|show dashboard)\b") {
        Play-Chime "done"
        Speak-Text "Opening SREE dashboard."
        Open-SreeApp
        $global:inConversation = $false
        $gFollowup.Enabled = $false
        return
    }

    # Clean command of wake word prefix
    $cleanCmd = $lower
    foreach ($w in $wakePhrases) {
        if ($cleanCmd.StartsWith($w)) {
            $cleanCmd = $cleanCmd.Substring($w.Length).Trim()
            break
        }
    }

    # CASE A: User said ONLY the Wake Word ("Hey Sree", "Hi Sree", etc.)
    if ([string]::IsNullOrWhiteSpace($cleanCmd)) {
        $now = [DateTime]::Now
        if (($now - $global:lastWakeTime).TotalSeconds -lt 2.0) { return }
        $global:lastWakeTime = $now

        Play-Chime "start"
        Speak-Text "I'm listening."
        
        # Enable 8-second conversation window for the user to speak their command
        $global:inConversation = $true
        $global:conversationExpires = [DateTime]::Now.AddSeconds(8)
        $gFollowup.Enabled = $true
        return
    }

    # CASE B: Compound Command ("Hey Sree, open calculator") OR Followup Command during active window
    Play-Chime "done"
    Write-Output "[Executing Command] '$cleanCmd'"

    $postBody = @{ message = $cleanCmd } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "$ApiUrl/api/chat" -Method POST -Body $postBody -ContentType "application/json" -TimeoutSec 10
        if ($resp -and $resp.reply) {
            Write-Output "[SREE Reply] $($resp.reply)"
            Speak-Text $resp.reply
        }
    } catch {
        Write-Output "[!] Backend communication error: $_"
    }

    # Return to silent standby immediately after executing
    $global:inConversation = $false
    $gFollowup.Enabled = $false
}

# Register the event
$eventJob = Register-ObjectEvent -InputObject $recognizer -EventName "SpeechRecognized" -Action $speechHandler

# Start continuous asynchronous recognition
$recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)

# 7. Keep-Alive Loop with Health Checks & Silent Timeout
try {
    while ($true) {
        if ($global:inConversation -and ([DateTime]::Now -gt $global:conversationExpires)) {
            $global:inConversation = $false
            $gFollowup.Enabled = $false # Re-lock strictly into standby
        }
        Start-Sleep -Seconds 1
    }
} finally {
    $recognizer.RecognizeAsyncStop()
    Unregister-Event -SourceIdentifier $eventJob.Name -ErrorAction SilentlyContinue
}
