<#
================================================================================
 SREE - Native Windows Background Voice Listener & Live Assistant
 Runs 24/7 in background on Windows startup, listening for "Hey Sree".
 Connects directly to local Ollama and SREE backend on port 8005.
================================================================================
#>

param(
    [switch]$MinToTray = $true
)

# 1. Assemblies
Add-Type -AssemblyName System.Speech
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$ApiUrl = "http://127.0.0.1:8005"
$OllamaUrl = "http://127.0.0.1:11434"

# 2. Service Ensure Functions
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
        Write-Output "[*] Starting Ollama daemon in background..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
}

function Ensure-SreeBackend() {
    if (-not (Test-HttpEndpoint "$ApiUrl/health")) {
        Write-Output "[*] Starting SREE backend server in background..."
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
$synth.Rate = 1 # Brisk, confident Siri tempo
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
    
    # Speak first 2-3 sentences for fast Siri delivery
    $sentences = $clean -split '(?<=[.!?])\s+'
    $toSpeak = if ($sentences.Count -gt 3) { ($sentences[0..2] -join " ") } else { $clean }

    $synth.SpeakAsyncCancelAll()
    $synth.Speak($toSpeak)
}

function Play-Chime($type = "start") {
    try {
        if ($type -eq "start") {
            # Ascending two-tone chime
            [System.Console]::Beep(587, 80)
            [System.Console]::Beep(880, 120)
        } else {
            # Descending confirmation
            [System.Console]::Beep(880, 80)
            [System.Console]::Beep(587, 100)
        }
    } catch {
        [System.Media.SystemSounds]::Asterisk.Play()
    }
}

# 4. Initialize Core Services
Write-Output "================================================="
Write-Output "    SREE BACKGROUND SYSTEM-WIDE VOICE LISTENER   "
Write-Output "================================================="
Ensure-Ollama
Ensure-SreeBackend

# 5. Speech Recognizer Setup
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Grammar Choices
$wakeChoices = New-Object System.Speech.Recognition.Choices
$wakeChoices.Add([string[]]@(
    "hey sree", "hi sree", "sree", "hey sri", "hi sri", "sri",
    "hey siri", "hi siri", "siri", "hello sree", "good morning sree"
))

$commandChoices = New-Object System.Speech.Recognition.Choices
$commandChoices.Add([string[]]@(
    "open calculator", "launch calculator",
    "open notepad", "launch notepad",
    "open terminal", "launch terminal", "open command prompt",
    "open browser", "launch browser",
    "open task manager", "show task manager",
    "open code", "open visual studio code", "open vscode",
    "open sree", "show sree", "open dashboard", "show dashboard",
    "what is the weather", "what's the weather", "weather today",
    "what time is it", "what's the time",
    "what is the date", "what is today's date", "what day is it",
    "how are you", "who are you", "what can you do",
    "daily briefing", "morning briefing",
    "stop listening", "turn off voice assistant", "go to sleep", "shut down"
))

$gbWake = New-Object System.Speech.Recognition.GrammarBuilder
$gbWake.Append($wakeChoices)
$grammarWake = New-Object System.Speech.Recognition.Grammar($gbWake)
$grammarWake.Name = "WakeGrammar"
$recognizer.LoadGrammar($grammarWake)

$gbCmd = New-Object System.Speech.Recognition.GrammarBuilder
$gbCmd.Append($commandChoices)
$grammarCmd = New-Object System.Speech.Recognition.Grammar($gbCmd)
$grammarCmd.Name = "CommandGrammar"
$recognizer.LoadGrammar($grammarCmd)

# Dictation Grammar for general questions
$dictationGrammar = New-Object System.Speech.Recognition.DictationGrammar
$dictationGrammar.Name = "DictationGrammar"
$recognizer.LoadGrammar($dictationGrammar)

Write-Output "[+] SREE background listener is online and listening for 'Hey Sree'..."

# Startup announcement chime
Play-Chime "start"
Speak-Text "SREE is online in the background."

# 6. Main Background Listening Loop
$isConversationalMode = $false
$conversationalTimeout = [DateTime]::MinValue

while ($true) {
    try {
        # Check if conversation mode expired
        if ($isConversationalMode -and ([DateTime]::Now -gt $conversationalTimeout)) {
            $isConversationalMode = $false
            Write-Output "[*] Conversation timeout. Returning to standby."
        }

        # Listen for speech with a 2-second slice
        $recognitionResult = $recognizer.Recognize([TimeSpan]::FromSeconds(2))
        
        if ($recognitionResult -ne $null -and $recognitionResult.Confidence -ge 0.5) {
            $heardText = $recognitionResult.Text.Trim()
            Write-Output "[Heard] '$heardText' (Confidence: $($recognitionResult.Confidence))"

            $lower = $heardText.ToLower()

            # Check for deactivation
            if ($lower -match "stop listening|turn off.*voice|go to sleep|shut down") {
                Play-Chime "done"
                Speak-Text "Voice standby. Call me anytime."
                $isConversationalMode = $false
                continue
            }

            # Check for wake word
            $isWake = ($lower -match "^(?:hey|hi|hello)?\s*(?:sree|sri|siri)$")
            if ($isWake) {
                Play-Chime "start"
                Speak-Text "Hey Boss! I'm listening."
                $isConversationalMode = $true
                $conversationalTimeout = [DateTime]::Now.AddSeconds(15)
                continue
            }

            # Check if user wants to open the app UI
            if ($lower -match "open sree|show sree|open dashboard|show dashboard") {
                Play-Chime "done"
                Speak-Text "Opening SREE dashboard."
                Open-SreeApp
                $isConversationalMode = $false
                continue
            }

            # If in conversational mode OR heard a direct command:
            if ($isConversationalMode -or ($recognitionResult.Grammar.Name -eq "CommandGrammar")) {
                # Strip leading wake words if any
                $cleanCmd = $heardText -replace '^(?i)(?:hey|hi|hello)\s+(?:sree|sri|siri)[,\s]*', ''
                if ([string]::IsNullOrWhiteSpace($cleanCmd)) { $cleanCmd = $heardText }

                Play-Chime "done"
                Write-Output "[Processing Command] '$cleanCmd'"

                # Query SREE backend
                $postBody = @{ message = $cleanCmd } | ConvertTo-Json
                try {
                    $resp = Invoke-RestMethod -Uri "$ApiUrl/api/chat" -Method POST -Body $postBody -ContentType "application/json" -TimeoutSec 10
                    if ($resp -and $resp.reply) {
                        Write-Output "[SREE Reply] $($resp.reply)"
                        Speak-Text $resp.reply

                        # Refresh conversation mode for follow-ups
                        $isConversationalMode = $true
                        $conversationalTimeout = [DateTime]::Now.AddSeconds(12)
                    }
                } catch {
                    Write-Output "[!] Backend communication error: $_"
                }
            }
        }
    } catch {
        Start-Sleep -Milliseconds 300
    }
}

