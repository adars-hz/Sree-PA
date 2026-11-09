<#
================================================================================
 SREE - Native Windows Background Voice Listener & Live Assistant
 Runs 24/7 silently in background on Windows startup.
 STRICT WAKE-WORD GATED:
 Only enables and speaks when explicitly invoked with "Hey Sree".
 Zero unsolicited announcements, zero false room-noise triggers.
 Listens for followup commands and executes them seamlessly hands-free.
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
if ([string]::IsNullOrWhiteSpace($ScriptDir)) {
    $ScriptDir = "D:\sri\scripts"
}
$RootDir = Split-Path -Parent $ScriptDir
if ([string]::IsNullOrWhiteSpace($RootDir) -or -not (Test-Path "$RootDir\backend")) {
    $RootDir = "D:\sri"
}
$ApiUrl = "http://127.0.0.1:8005"
$OllamaUrl = "http://127.0.0.1:11434"

# 2. Service Ensure Functions (Completely Silent)
function Test-HttpEndpoint($url, $timeoutMs = 1200) {
    try {
        $req = [System.Net.WebRequest]::Create($url)
        $req.Timeout = $timeoutMs
        $res = $req.GetResponse()
        $status = [int]$res.StatusCode
        $res.Close()
        return ($status -eq 200)
    } catch {
        return $false
    }
}

function Ensure-Ollama() {
    if (-not (Test-HttpEndpoint "$OllamaUrl/api/tags", 1000)) {
        try {
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 1500
        } catch {}
    }
}

function Ensure-SreeBackend() {
    if (-not (Test-HttpEndpoint "$ApiUrl/health", 1000)) {
        try {
            $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
            $pythonExe = if ($pythonCmd) { $pythonCmd.Source } else { "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe" }
            Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8005" -WorkingDirectory $RootDir -WindowStyle Hidden
            
            # Wait up to 10 seconds for backend to become ready
            for ($i = 0; $i -lt 20; $i++) {
                if (Test-HttpEndpoint "$ApiUrl/health", 1000) { break }
                Start-Sleep -Milliseconds 500
            }
        } catch {
            Write-Output "[!] Failed to launch backend: $_"
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
$synth.Rate = 1 # Brisk, natural tempo
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
    
    # Speak first 2 sentences for fast concise delivery
    $sentences = $clean -split '(?<=[.!?])\s+'
    $toSpeak = if ($sentences.Count -gt 2) { ($sentences[0..1] -join " ") } else { $clean }

    $synth.SpeakAsyncCancelAll()
    $synth.SpeakAsync($toSpeak) | Out-Null
}

function Play-Chime($type = "start") {
    try {
        if ($type -eq "start") {
            [System.Console]::Beep(659, 90)
            [System.Console]::Beep(880, 140)
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

# 5. Build Strict Wake-Word & Followup Grammars
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Strict Wake Phrases
$wakePhrases = @(
    "hey sree", "hi sree", "hello sree", "ok sree", "okay sree",
    "hey sri", "hi sri", "hello sri", "ok sri",
    "hey shree", "hi shree", "hello shree",
    "hey siri", "hi siri", "hello siri",
    "sree", "sri", "jarvis"
)

# Core Allowed Commands
$commandPhrases = @(
    "open calculator", "launch calculator", "calculator",
    "open notepad", "launch notepad", "notepad",
    "open terminal", "launch terminal", "open command prompt", "open cmd", "open powershell",
    "open browser", "launch browser", "open chrome", "open edge", "chrome", "edge",
    "open task manager", "show task manager", "task manager",
    "open code", "open visual studio code", "open vscode", "launch vscode",
    "open sree", "show sree", "open dashboard", "show dashboard",
    "take a screenshot", "capture screen", "screenshot", "take screenshot",
    "share my screen", "open screen share", "screen share",
    "minimize all windows", "minimize all", "show desktop", "desktop",
    "switch window", "alt tab", "close active window", "close window",
    "volume up", "increase volume", "volume down", "lower volume", "mute audio", "mute", "unmute",
    "scroll down", "scroll up",
    "lock my pc", "lock computer", "lock screen",
    "click", "double click", "right click", "copy", "paste",
    "press enter", "press escape", "press space", "press tab",
    "what is the weather", "what's the weather", "weather today", "how is the weather",
    "what time is it", "what's the time", "current time", "what time is now", "time",
    "what is the date", "what is today's date", "what day is it", "date today", "date",
    "how are you", "who are you", "what can you do", "introduce yourself",
    "daily briefing", "morning briefing", "summarize my day", "briefing",
    "stop listening", "turn off voice assistant", "go to sleep", "shut down", "exit"
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

# Grammar 3: Followup Command Choices (Active ONLY during conversation window after "Hey Sree")
$gbFollowup = New-Object System.Speech.Recognition.GrammarBuilder($cCmd)
$gFollowup = New-Object System.Speech.Recognition.Grammar($gbFollowup)
$gFollowup.Name = "FollowupCommandGrammar"
$gFollowup.Enabled = $false # STRICTLY OFF in standby!
$recognizer.LoadGrammar($gFollowup)

# Grammar 4: Followup Free-Form Dictation (Active ONLY during conversation window after "Hey Sree")
$gDictation = New-Object System.Speech.Recognition.DictationGrammar
$gDictation.Name = "FollowupDictationGrammar"
$gDictation.Enabled = $false # STRICTLY OFF in standby!
$recognizer.LoadGrammar($gDictation)

# 6. Global State & Event Handling
$global:inConversation = $false
$global:conversationExpires = [DateTime]::MinValue
$global:lastWakeTime = [DateTime]::MinValue

$speechHandler = {
    param($sender, $e)

    if ($e -eq $null -or $e.Result -eq $null) { return }
    $heard = $e.Result.Text.Trim()
    $confidence = $e.Result.Confidence

    # Confidence threshold: wake word requires 0.55 to prevent false triggers;
    # active conversation accepts 0.40 so speech is not dropped.
    $minConfidence = if ($global:inConversation) { 0.40 } else { 0.55 }
    if ($confidence -lt $minConfidence) { return }

    # Drop audio if SREE is currently speaking through the speakers (prevent self-echo)
    if ($synth.State -eq [System.Speech.Synthesis.SynthesizerState]::Speaking) {
        return
    }

    $lower = $heard.ToLower().Trim()

    # If in standby and doesn't match a wake phrase, drop it
    $hasWakePrefix = ($wakePhrases | Where-Object { $lower.StartsWith($_) })

    if (-not $global:inConversation -and -not $hasWakePrefix) {
        return # STRICT STANDBY: Ignore everything without "Hey Sree"!
    }

    # Clean command of wake word prefix if present
    $cleanCmd = $lower
    foreach ($w in $wakePhrases) {
        if ($cleanCmd.StartsWith($w)) {
            $cleanCmd = $cleanCmd.Substring($w.Length).Trim()
            break
        }
    }

    # CASE A: User said ONLY the Wake Word ("Hey Sree", "Hi Sree", etc.)
    if ([string]::IsNullOrWhiteSpace($cleanCmd)) {
        # Optional Speaker Verification check (only runs on initial wake word)
        try {
            if ($e.Result.Audio -ne $null) {
                $tempWav = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "sree_wake_audio.wav")
                $fs = [System.IO.File]::Create($tempWav)
                $e.Result.Audio.WriteToWaveStream($fs)
                $fs.Close()

                $verifyBody = @{ audio_file_path = $tempWav } | ConvertTo-Json
                $verifyRes = Invoke-RestMethod -Uri "$ApiUrl/api/voice/verify" -Method POST -Body $verifyBody -ContentType "application/json" -TimeoutSec 2 -ErrorAction SilentlyContinue

                if ($verifyRes -and (-not $verifyRes.verified)) {
                    Write-Output "[Security Gated] Unauthorized speaker voice rejected. SREE will not reply to unauthorized voices."
                    return # STRICT SILENCE: Do not reply to unauthorized voices!
                }
            }
        } catch {}

        $now = [DateTime]::Now
        if (($now - $global:lastWakeTime).TotalSeconds -lt 1.5) { return }
        $global:lastWakeTime = $now

        Write-Output "[Heard Wake Word] '$heard' -> Acknowledging and listening..."
        Play-Chime "start"
        Speak-Text "I'm listening."

        # Activate conversation window: 5.5 seconds provides comfortable time to speak command
        $global:inConversation = $true
        $global:conversationExpires = [DateTime]::Now.AddSeconds(5.5)
        $gFollowup.Enabled = $true
        $gDictation.Enabled = $true
        return
    }

    # Check for Deactivation Intent
    if ($lower -match "\b(?:stop listening|turn off.*voice|go to sleep|shut down)\b") {
        Play-Chime "done"
        Speak-Text "Voice standby. Say Hey Sree whenever you need me."
        $global:inConversation = $false
        $gFollowup.Enabled = $false
        $gDictation.Enabled = $false
        return
    }

    # Check for Open Sree App UI
    if ($lower -match "\b(?:open sree|show sree|open dashboard|show dashboard)\b") {
        Play-Chime "done"
        Speak-Text "Opening SREE dashboard."
        Open-SreeApp
        $global:inConversation = $false
        $gFollowup.Enabled = $false
        $gDictation.Enabled = $false
        return
    }

    # CASE B: Compound Command ("Hey Sree, open calculator") OR Followup Command during active window
    Write-Output "[Executing Command] '$cleanCmd' (Confidence: $([Math]::Round($confidence, 2)))"
    Play-Chime "done"

    # Immediately lock back into standby while executing to avoid double-triggers
    $global:inConversation = $false
    $gFollowup.Enabled = $false
    $gDictation.Enabled = $false

    # Auto-heal backend if needed
    Ensure-SreeBackend

    $postBody = @{ message = $cleanCmd } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "$ApiUrl/api/chat" -Method POST -Body $postBody -ContentType "application/json" -TimeoutSec 15
        if ($resp -and $resp.reply) {
            Write-Output "[SREE Reply] $($resp.reply)"
            Speak-Text $resp.reply
        } else {
            Speak-Text "Command received."
        }
    } catch {
        Write-Output "[!] Backend communication error: $_"
        Speak-Text "I'm sorry, I couldn't connect to the SREE backend server. Please make sure SREE is running."
    }
}

# Register the event
$eventJob = Register-ObjectEvent -InputObject $recognizer -EventName "SpeechRecognized" -Action $speechHandler

# Start continuous asynchronous recognition
$recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
Write-Output "[+] SREE Native Background Listener Active. Listening strictly for 'Hey Sree'..."

# 7. Keep-Alive Loop with Health Checks & Silent Timeout
try {
    while ($true) {
        if ($global:inConversation -and ([DateTime]::Now -gt $global:conversationExpires)) {
            $global:inConversation = $false
            $gFollowup.Enabled = $false
            $gDictation.Enabled = $false
            Play-Chime "done"
            Write-Output "[Standby] Listening window timed out. Returning to silent standby."
        }
        Start-Sleep -Milliseconds 150
    }
} finally {
    $recognizer.RecognizeAsyncStop()
    Unregister-Event -SourceIdentifier $eventJob.Name -ErrorAction SilentlyContinue
}
