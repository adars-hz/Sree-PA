/**
 * SREE Personal AI Assistant - Comprehensive Frontend Engine
 * Powers JARVIS animations, real-time streaming, lively voice synthesis,
 * continuous 2-way speech interaction, allowlisted laptop automation, and cross-device sync.
 */

class SreeApp {
    constructor() {
        this.apiBase = window.location.origin;
        this.activeTab = "home";
        this.conversationHistory = [];
        this.isGenerating = false;
        this.isRecording = false;
        this.liveConversationActive = false;
        this.voiceResponseEnabled = true; // Auto-speak enabled by default for a lively JARVIS feel!
        this.isSpeaking = false;
        this.activeModel = "llama3.2:3b";
        this.deferredPrompt = null;
        
        // Voice & Audio Configuration
        this.speechRate = 1.1; // Siri brisk and natural tempo
        this.selectedVoice = null;
        this.recognition = null;
        this.synthesis = window.speechSynthesis || null;
        this.audioCtx = null;
        this.speechDebounceTimer = null;
        this.wakeSilenceTimer = null;
        this.speechKeepAliveTimer = null;
        this.ttsWatchdogTimer = null;
        this.isProcessingCommand = false;
        this.ignoreSpeechResults = false;
        this.lastCommittedText = "";
        this.lastCommittedTime = 0;

        this.initDOMElements();
        this.initPwaInstallFlow();
        this.initNavigation();
        this.initChatHandlers();
        this.initVoiceEngine();
        this.initMemoryHandlers();
        this.initNotesHandlers();
        this.initRemindersHandlers();
        this.initAutomationHandlers();
        this.initSettingsHandlers();
        this.initQrModal();
        this.initScreenHandlers();
        this.initTelemetryPoller();
        this.loadAIProviders();
        this.updateDynamicGreeting();
    }

    initDOMElements() {
        // Navigation & Views
        this.navButtons = document.querySelectorAll('.nav-item, .mob-nav-item');
        this.views = document.querySelectorAll('.view');
        
        // Chat Elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.micBtn = document.getElementById('micBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Header Controls
        this.speakerToggleBtn = document.getElementById('speakerToggleBtn');
        this.speakerIcon = document.getElementById('speakerIcon');
        this.voiceToggleBtn = document.getElementById('voiceToggleBtn');
        this.liveConversationHeroBtn = document.getElementById('liveConversationHeroBtn');

        // Telemetry & Pills
        this.networkPill = document.getElementById('networkPillText');
        this.ollamaPill = document.getElementById('ollamaPillText');
        this.activeModelLabel = document.getElementById('activeModelLabel');
        this.ramUsageLabel = document.getElementById('ramUsageLabel');
        this.mobileUrlDisplay = document.getElementById('mobileUrlDisplay');
        this.modalMobileUrlDisplay = document.getElementById('modalMobileUrlDisplay');
        
        // JARVIS Orb
        this.orbCore = document.getElementById('orbCore');
        this.voiceBanner = document.getElementById('voiceBanner');
        this.voiceStatusText = document.getElementById('voiceStatusText');

        // Dynamic Time
        const initTime = document.getElementById('initTime');
        if (initTime) {
            initTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }

    // ==========================================
    // AUDIO & HAPTIC SYSTEM
    // ==========================================
    triggerHaptic(pattern = [20]) {
        if (navigator.vibrate) {
            try { navigator.vibrate(pattern); } catch (e) {}
        }
    }

    playChime(type = 'listen') {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!this.audioCtx) this.audioCtx = new AudioContext();
            if (this.audioCtx.state === 'suspended') this.audioCtx.resume();

            const now = this.audioCtx.currentTime;

            if (type === 'siri_start' || type === 'wake') {
                // Signature iOS Siri dual ascending harmonic chime
                const osc1 = this.audioCtx.createOscillator();
                const osc2 = this.audioCtx.createOscillator();
                const gain = this.audioCtx.createGain();

                osc1.type = 'sine';
                osc2.type = 'sine';
                osc1.frequency.setValueAtTime(587.33, now); // D5
                osc2.frequency.setValueAtTime(880.00, now + 0.08); // A5

                gain.gain.setValueAtTime(0.08, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

                osc1.connect(gain);
                osc2.connect(gain);
                gain.connect(this.audioCtx.destination);

                osc1.start(now);
                osc1.stop(now + 0.08);
                osc2.start(now + 0.08);
                osc2.stop(now + 0.22);
                return;
            }

            if (type === 'siri_end' || type === 'done') {
                // Subtle Siri confirmation tone
                const osc = this.audioCtx.createOscillator();
                const gain = this.audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880.00, now);
                osc.frequency.exponentialRampToValueAtTime(587.33, now + 0.12);
                gain.gain.setValueAtTime(0.06, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                osc.connect(gain);
                gain.connect(this.audioCtx.destination);
                osc.start(now);
                osc.stop(now + 0.15);
                return;
            }

            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.type = 'sine';
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            if (type === 'listen') {
                // Ascending chirp
                osc.frequency.setValueAtTime(520, now);
                osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
                osc.start(now);
                osc.stop(now + 0.18);
            } else if (type === 'reply') {
                // Subtle confirmation tone
                osc.frequency.setValueAtTime(880, now);
                osc.frequency.exponentialRampToValueAtTime(660, now + 0.15);
                gain.gain.setValueAtTime(0.06, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
                osc.start(now);
                osc.stop(now + 0.2);
            }
        } catch (e) {}
    }

    // ==========================================
    // PWA INSTALL FLOW (ANDROID & DESKTOP)
    // ==========================================
    initPwaInstallFlow() {
        const installBanner = document.getElementById('pwaInstallBanner');
        const installBtn = document.getElementById('installPwaBtn');
        const dismissBtn = document.getElementById('dismissPwaBtn');

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            if (installBanner) installBanner.style.display = 'flex';
        });

        if (installBtn) {
            installBtn.addEventListener('click', async () => {
                this.triggerHaptic([30]);
                if (this.deferredPrompt) {
                    this.deferredPrompt.prompt();
                    const { outcome } = await this.deferredPrompt.userChoice;
                    if (outcome === 'accepted') {
                        if (installBanner) installBanner.style.display = 'none';
                    }
                    this.deferredPrompt = null;
                }
            });
        }

        if (dismissBtn && installBanner) {
            dismissBtn.addEventListener('click', () => {
                installBanner.style.display = 'none';
            });
        }
    }

    // ==========================================
    // QR CODE PHONE PAIRING POPUP
    // ==========================================
    initQrModal() {
        const qrModal = document.getElementById('qrModal');
        const qrPairHeaderBtn = document.getElementById('qrPairHeaderBtn');
        const quickPairChip = document.getElementById('quickPairChip');
        const closeQrModalBtn = document.getElementById('closeQrModalBtn');

        const openQr = () => {
            this.triggerHaptic([20]);
            if (qrModal) qrModal.classList.add('active');
        };

        if (qrPairHeaderBtn) qrPairHeaderBtn.addEventListener('click', openQr);
        if (quickPairChip) quickPairChip.addEventListener('click', openQr);
        if (closeQrModalBtn && qrModal) {
            closeQrModalBtn.addEventListener('click', () => qrModal.classList.remove('active'));
        }
    }

    updateDynamicGreeting() {
        const greetingHeading = document.getElementById('greetingText');
        if (!greetingHeading) return;
        const hour = new Date().getHours();
        let greeting = "Good morning, Boss";
        if (hour >= 12 && hour < 17) greeting = "Good afternoon, Boss";
        else if (hour >= 17) greeting = "Good evening, Boss";
        greetingHeading.textContent = greeting;
    }

    initNavigation() {
        this.navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.triggerHaptic([15]);
                const tab = btn.getAttribute('data-tab');
                if (tab) this.switchTab(tab);
            });
        });

        document.querySelectorAll('.chip').forEach(chip => {
            if (chip.id === 'quickPairChip') return;
            chip.addEventListener('click', () => {
                this.triggerHaptic([20]);
                const prompt = chip.getAttribute('data-prompt');
                if (prompt) {
                    this.switchTab('chat');
                    this.sendUserMessage(prompt);
                }
            });
        });

        const orbContainer = document.querySelector('.orb-container');
        if (orbContainer) {
            orbContainer.addEventListener('click', () => {
                this.triggerHaptic([25]);
                this.toggleLiveConversation();
            });
        }

        if (this.liveConversationHeroBtn) {
            this.liveConversationHeroBtn.addEventListener('click', () => {
                this.triggerHaptic([25]);
                this.toggleLiveConversation();
            });
        }
    }

    switchTab(tabName) {
        this.activeTab = tabName;
        
        this.navButtons.forEach(b => {
            if (b.getAttribute('data-tab') === tabName) b.classList.add('active');
            else b.classList.remove('active');
        });

        this.views.forEach(v => {
            if (v.id === `view-${tabName}`) v.classList.add('active');
            else v.classList.remove('active');
        });

        if (tabName === 'chat') {
            this.scrollChatToBottom();
        } else if (tabName === 'memory') {
            this.loadMemories();
        } else if (tabName === 'notes') {
            this.loadNotes();
        } else if (tabName === 'tasks') {
            this.loadReminders();
        } else if (tabName === 'devices') {
            this.loadDeviceTelemetry();
        } else if (tabName === 'screen') {
            this.loadScreenStatus();
        } else if (tabName === 'settings') {
            this.loadOllamaChips();
            this.loadAIProviders();
        }
    }

    // ==========================================
    // CHAT & STREAMING LOGIC
    // ==========================================
    initChatHandlers() {
        this.sendBtn.addEventListener('click', () => {
            this.triggerHaptic([25]);
            const text = this.chatInput.value.trim();
            if (text) {
                this.switchTab('chat');
                this.sendUserMessage(text);
                this.chatInput.value = '';
                this.autoResizeInput();
            }
        });

        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendBtn.click();
            }
        });

        this.chatInput.addEventListener('input', () => this.autoResizeInput());

        if (this.clearChatBtn) {
            this.clearChatBtn.addEventListener('click', async () => {
                this.triggerHaptic([30]);
                if (confirm("Clear active conversation history?")) {
                    this.chatMessages.innerHTML = '';
                    this.conversationHistory = [];
                    try {
                        await fetch(`${this.apiBase}/api/chat/history`, { method: 'DELETE' });
                    } catch (e) {}
                }
            });
        }
    }

    autoResizeInput() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = `${Math.min(this.chatInput.scrollHeight, 100)}px`;
    }

    scrollChatToBottom() {
        requestAnimationFrame(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        });
    }

    appendMessage(role, content, timestamp = null) {
        const timeStr = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const isUser = role === 'user';
        
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${isUser ? 'user' : 'assistant'}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? '👤' : '◈';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        const sender = document.createElement('div');
        sender.className = 'message-sender';
        sender.textContent = isUser ? 'You' : 'SREE AI Core';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = this.formatMarkdown(content);

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = timeStr;

        bubble.appendChild(sender);
        bubble.appendChild(textDiv);
        bubble.appendChild(timeDiv);

        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);

        this.chatMessages.appendChild(wrapper);
        this.scrollChatToBottom();

        return textDiv;
    }

    formatMarkdown(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Code blocks
        escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Inline code
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        // Bold
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Italic
        escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        // Newlines
        escaped = escaped.replace(/\n/g, '<br>');

        return escaped;
    }

    async sendUserMessage(text) {
        if (this.isGenerating || !text.trim()) return;

        // If SREE is currently speaking, cut off speech to listen to user immediately
        if (this.isSpeaking && this.synthesis) {
            this.synthesis.cancel();
            this.isSpeaking = false;
        }

        this.appendMessage('user', text);
        this.conversationHistory.push({ role: 'user', content: text });

        this.isGenerating = true;
        this.showTyping(true);
        this.setOrbState('thinking');

        try {
            const response = await fetch(`${this.apiBase}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    model: this.activeModel,
                    session_id: "default",
                    history: this.conversationHistory.slice(-8)
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.showTyping(false);
            const streamTextElem = this.appendMessage('assistant', '');
            let fullReply = '';

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullReply += chunk;
                streamTextElem.innerHTML = this.formatMarkdown(fullReply);
                this.scrollChatToBottom();
            }

            this.conversationHistory.push({ role: 'assistant', content: fullReply });
            this.setOrbState('idle');
            this.playChime('reply');

            // CRITICAL: Speak response out loud automatically if voice response is enabled!
            if (this.voiceResponseEnabled) {
                this.speak(fullReply);
            }

        } catch (error) {
            console.error("Chat error:", error);
            this.showTyping(false);
            const errMsg = `Operational Alert: Unable to process request. ${error.message}`;
            this.appendMessage('assistant', `⚠️ **${errMsg}**`);
            this.setOrbState('idle');
            if (this.voiceResponseEnabled) {
                this.speak("I encountered an issue processing that command.");
            }
        } finally {
            this.isGenerating = false;
        }
    }

    showTyping(visible) {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = visible ? 'flex' : 'none';
            if (visible) this.scrollChatToBottom();
        }
    }

    setOrbState(state) {
        if (!this.orbCore) return;
        if (state === 'thinking') {
            this.orbCore.style.boxShadow = '0 0 55px rgba(0, 242, 254, 0.95)';
            if (this.voiceStatusText) this.voiceStatusText.textContent = "SREE is thinking...";
        } else if (state === 'speaking') {
            this.orbCore.style.boxShadow = '0 0 70px rgba(0, 255, 135, 0.95)';
            if (this.voiceStatusText) this.voiceStatusText.textContent = "SREE is speaking...";
        } else if (state === 'listening') {
            this.orbCore.style.boxShadow = '0 0 65px rgba(255, 51, 102, 0.95)';
            if (this.voiceStatusText) this.voiceStatusText.textContent = "Listening... Say 'Hi Sree' or speak a command";
        } else {
            this.orbCore.style.boxShadow = '0 0 40px rgba(0, 242, 254, 0.6)';
            if (this.voiceStatusText) {
                this.voiceStatusText.textContent = this.liveConversationActive ? 
                    "Live Listening Active (\"Hi Sree\")" : "Voice standby (Click to talk)";
            }
        }
    }

    // ==========================================
    // SIRI-STYLE ULTRA-FAST VOICE ENGINE
    // ==========================================
    initVoiceEngine() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = navigator.language || 'en-US';

            this.recognition.onstart = () => {
                this.isRecording = true;
                this.micBtn.classList.add('recording');
                if (this.liveConversationHeroBtn) {
                    this.liveConversationHeroBtn.classList.add('listening');
                    const label = this.liveConversationHeroBtn.querySelector('span:last-child');
                    if (label) label.textContent = "🔴 LISTENING... (Say 'Hi Sree' or a command)";
                }
                this.setOrbState('listening');
            };

            this.recognition.onresult = (event) => {
                if (this.ignoreSpeechResults || this.isProcessingCommand || this.isSpeaking) return;

                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const trans = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += trans;
                    } else {
                        interimTranscript += trans;
                    }
                }

                const currentText = (finalTranscript || interimTranscript).trim();
                if (!currentText) return;

                // 1. Live transcription HUD: show words in real time as they are spoken
                const transcriptDisplay = document.getElementById('liveVoiceTranscript');
                if (transcriptDisplay) {
                    transcriptDisplay.textContent = currentText;
                }

                const subtitleCard = document.getElementById('floatingSubtitle');
                const subtitleText = document.getElementById('siriSubtitleText');
                if (subtitleCard && subtitleText) {
                    subtitleCard.style.display = 'inline-flex';
                    subtitleText.textContent = `"${currentText}"`;
                }

                // 2. Local Deactivation Intent ("turn off the voice assistant", "stop listening", "go to sleep")
                const lower = currentText.toLowerCase().replace(/[.,!]/g, "").trim();
                if (/turn\s+off.*voice|stop\s+listening|deactivate.*voice|stop\s+talking|be\s+quiet|shut\s+down|go\s+to\s+sleep/i.test(lower)) {
                    clearTimeout(this.speechDebounceTimer);
                    this.speechDebounceTimer = null;
                    this.liveConversationActive = false;
                    this.ignoreSpeechResults = true;
                    try { this.recognition.abort(); } catch (e) {}
                    this.playChime('siri_end');
                    this.setOrbState('idle');
                    if (this.liveConversationHeroBtn) {
                        this.liveConversationHeroBtn.classList.remove('listening');
                        const label = this.liveConversationHeroBtn.querySelector('span:last-child');
                        if (label) label.textContent = "🎙️ START LIVE CONVERSATION (\"Hi Sree\")";
                    }
                    this.speak("Voice assistant deactivated. Click the Orb whenever you're ready to talk.");
                    return;
                }

                // 3. Instant Wake-Word detection ("hi sree", "hey sree", "sree", "hey sri", "hey shree", "siri", etc.)
                const isWakeOnly = /^(?:hi|hey|hello|ok|okay)?\s*(?:sree|sri|shree|shri|siri|three|tree|see)$/i.test(lower);
                if (isWakeOnly) {
                    clearTimeout(this.speechDebounceTimer);
                    this.speechDebounceTimer = null;
                    const now = Date.now();
                    if ((now - this.lastCommittedTime) < 2000) return; // Prevent double wake
                    this.lastCommittedTime = now;
                    this.playChime('siri_start');
                    this.triggerHaptic([30, 40]);
                    this.setOrbState('listening');

                    // Fast visual feedback without talking over the user!
                    if (this.voiceStatusText) {
                        this.voiceStatusText.textContent = "🟢 SREE: I'm listening... Speak your command!";
                    }
                    if (subtitleCard && subtitleText) {
                        subtitleCard.style.display = 'inline-flex';
                        subtitleText.textContent = "⚡ SREE: I'm listening... What can I do for you?";
                    }

                    // Snappy silence timeout: if user does not speak within 2.6s, exit listening
                    clearTimeout(this.wakeSilenceTimer);
                    this.wakeSilenceTimer = setTimeout(() => {
                        if (this.isRecording && !this.isProcessingCommand && !this.isSpeaking) {
                            this.playChime('siri_end');
                            this.setOrbState('idle');
                            if (this.voiceStatusText) this.voiceStatusText.textContent = "SREE is ready.";
                            if (subtitleCard) subtitleCard.style.display = 'none';
                        }
                    }, 2600);
                    return;
                }

                // 4. Strip prepended wake word if user said "hey sree open calculator" -> "open calculator"
                let cleanedCommand = currentText.replace(/^(?:hi|hey|hello|ok|okay)\s*(?:sree|sri|shree|shri|siri|three|tree|see)[,\s]*/i, "").trim();
                if (!cleanedCommand) cleanedCommand = currentText;

                // 5. Siri-Speed Silence Debounce (420ms):
                // Snappy cutoff as soon as speech finishes!
                clearTimeout(this.wakeSilenceTimer);
                this.wakeSilenceTimer = null;
                clearTimeout(this.speechDebounceTimer);
                if (cleanedCommand.length >= 2) {
                    this.speechDebounceTimer = setTimeout(() => {
                        this.commitSpokenCommand(cleanedCommand);
                    }, 420);
                }
            };

            this.recognition.onerror = (event) => {
                console.warn("Speech recognition notice:", event.error);
                if (event.error === 'not-allowed') {
                    alert("Microphone permission was denied. Please allow microphone access in your browser address bar.");
                    this.liveConversationActive = false;
                }
            };

            this.recognition.onend = () => {
                this.isRecording = false;
                this.micBtn.classList.remove('recording');

                // If live conversation is active and SREE is NOT currently speaking, resume listening immediately!
                if (this.liveConversationActive && !this.isSpeaking && !this.isGenerating) {
                    setTimeout(() => {
                        this.startVoiceInputSilent();
                    }, 200);
                } else if (!this.isSpeaking) {
                    this.setOrbState('idle');
                }
            };
        }

        // Voice Control Buttons
        this.micBtn.addEventListener('click', () => this.toggleLiveConversation());
        
        if (this.voiceToggleBtn) {
            this.voiceToggleBtn.addEventListener('click', () => this.toggleLiveConversation());
        }

        const startVoiceListenBtn = document.getElementById('startVoiceListenBtn');
        if (startVoiceListenBtn) {
            startVoiceListenBtn.addEventListener('click', () => this.toggleLiveConversation());
        }

        const stopVoiceSpeechBtn = document.getElementById('stopVoiceSpeechBtn');
        if (stopVoiceSpeechBtn) {
            stopVoiceSpeechBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                if (this.synthesis) this.synthesis.cancel();
                this.isSpeaking = false;
                this.setOrbState('idle');
            });
        }

        // Speaker Mute/Unmute Toggle Button
        if (this.speakerToggleBtn) {
            this.speakerToggleBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                this.voiceResponseEnabled = !this.voiceResponseEnabled;
                if (this.voiceResponseEnabled) {
                    this.speakerToggleBtn.classList.add('active');
                    this.speakerToggleBtn.classList.remove('muted');
                    if (this.speakerIcon) this.speakerIcon.textContent = "🔊";
                    this.speak("Voice output enabled.");
                } else {
                    this.speakerToggleBtn.classList.remove('active');
                    this.speakerToggleBtn.classList.add('muted');
                    if (this.speakerIcon) this.speakerIcon.textContent = "🔇";
                    if (this.synthesis) this.synthesis.cancel();
                    this.isSpeaking = false;
                }
            });
        }

        // Voice Selector Population & Natural Voice Auto-Selection
        if (this.synthesis) {
            const populateVoices = () => {
                const voices = this.synthesis.getVoices();
                const voiceSelect = document.getElementById('voiceSelect');
                if (voiceSelect && voices.length > 0) {
                    voiceSelect.innerHTML = '';
                    let bestIdx = 0;

                    voices.forEach((v, idx) => {
                        const opt = document.createElement('option');
                        opt.value = idx;
                        opt.textContent = `${v.name} (${v.lang})`;

                        // Auto-prioritize natural human-like English voices
                        const nameLower = v.name.toLowerCase();
                        if (
                            nameLower.includes("natural") || 
                            nameLower.includes("online") || 
                            nameLower.includes("google us") ||
                            nameLower.includes("jenny") ||
                            nameLower.includes("neural")
                        ) {
                            bestIdx = idx;
                        } else if (bestIdx === 0 && (v.lang.startsWith('en_US') || v.lang.startsWith('en-US'))) {
                            bestIdx = idx;
                        }

                        voiceSelect.appendChild(opt);
                    });

                    voiceSelect.value = bestIdx;
                    this.selectedVoice = voices[bestIdx];
                }
            };

            populateVoices();
            if (speechSynthesis.onvoiceschanged !== undefined) {
                speechSynthesis.onvoiceschanged = populateVoices;
            }
        }

        // Speed Slider
        const rateSlider = document.getElementById('voiceRateSlider');
        const rateVal = document.getElementById('rateVal');
        if (rateSlider && rateVal) {
            rateSlider.addEventListener('input', (e) => {
                this.speechRate = parseFloat(e.target.value);
                rateVal.textContent = `${this.speechRate}x`;
            });
        }
    }

    commitSpokenCommand(commandText) {
        if (!commandText || commandText.length < 2) return;
        if (this.isProcessingCommand || this.isGenerating) return;

        // Deduplication guard: reject identical text within 3.5 seconds
        const now = Date.now();
        if (this.lastCommittedText.toLowerCase() === commandText.toLowerCase() && (now - this.lastCommittedTime) < 3500) {
            console.warn("Duplicate speech command suppressed:", commandText);
            return;
        }

        this.lastCommittedText = commandText;
        this.lastCommittedTime = now;
        this.isProcessingCommand = true;
        this.ignoreSpeechResults = true;

        clearTimeout(this.speechDebounceTimer);
        this.speechDebounceTimer = null;
        clearTimeout(this.wakeSilenceTimer);
        this.wakeSilenceTimer = null;
        
        // Use abort() so Chrome immediately drops pending buffers and doesn't emit duplicate onresult
        try { this.recognition.abort(); } catch (e) {}

        const subtitleText = document.getElementById('siriSubtitleText');
        if (subtitleText) subtitleText.textContent = `⚡ Processing: "${commandText}"...`;

        this.playChime('siri_end');
        this.triggerHaptic([20]);
        this.switchTab('chat');
        this.sendUserMessage(commandText);
    }

    toggleLiveConversation() {
        if (!this.recognition) {
            alert("Speech recognition requires Google Chrome or Microsoft Edge. Please launch via the SREE desktop shortcut or open in Chrome.");
            return;
        }

        this.liveConversationActive = !this.liveConversationActive;
        this.triggerHaptic([30]);

        if (this.liveConversationActive) {
            this.playChime('siri_start');
            this.startVoiceInputSilent();
            if (this.voiceToggleBtn) this.voiceToggleBtn.classList.add('active');
            if (this.liveConversationHeroBtn) {
                this.liveConversationHeroBtn.classList.add('listening');
                const label = this.liveConversationHeroBtn.querySelector('span:last-child');
                if (label) label.textContent = "🔴 LIVE LISTENING ACTIVE (\"Hi Sree\")";
            }
        } else {
            this.liveConversationActive = false;
            clearTimeout(this.speechDebounceTimer);
            try { this.recognition.stop(); } catch (e) {}
            if (this.synthesis) this.synthesis.cancel();
            this.isSpeaking = false;
            if (this.voiceToggleBtn) this.voiceToggleBtn.classList.remove('active');
            if (this.liveConversationHeroBtn) {
                this.liveConversationHeroBtn.classList.remove('listening');
                const label = this.liveConversationHeroBtn.querySelector('span:last-child');
                if (label) label.textContent = "🎙️ START LIVE CONVERSATION (\"Hi Sree\")";
            }
            this.setOrbState('idle');
        }
    }

    startVoiceInputSilent() {
        if (!this.recognition || this.isRecording || this.isSpeaking || this.isProcessingCommand) return;
        this.ignoreSpeechResults = false;
        try {
            this.recognition.start();
        } catch (e) {}
    }

    speak(text) {
        if (!this.synthesis || !this.voiceResponseEnabled) return;
        this.synthesis.cancel(); // Stop prior speech
        clearTimeout(this.ttsWatchdogTimer);

        // Strip markdown code blocks, URLs, and punctuation clutter so it speaks naturally
        let cleanText = text
            .replace(/```[\s\S]*?```/g, 'Code block omitted.')
            .replace(/`([^`]+)`/g, '$1')
            .replace(/\*\*([^*]+)\*\*/g, '$1')
            .replace(/[*_#~]/g, '')
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Markdown links -> title only
            .replace(/https?:\/\/\S+/g, '') // Remove raw urls from speech
            .trim();

        if (!cleanText) return;

        // Siri-Style Voice Chunking: Speak the first 2 concise sentences for voice speed
        const sentences = cleanText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [cleanText];
        const voiceText = sentences.slice(0, 3).join(' ').trim();

        const utterance = new SpeechSynthesisUtterance(voiceText);
        utterance.rate = this.speechRate;
        utterance.pitch = 1.0;

        const voiceSelect = document.getElementById('voiceSelect');
        const voices = this.synthesis.getVoices();
        if (voiceSelect && voices.length > 0) {
            const idx = parseInt(voiceSelect.value);
            if (!isNaN(idx) && voices[idx]) {
                utterance.voice = voices[idx];
            }
        }

        utterance.onstart = () => {
            this.isSpeaking = true;
            this.setOrbState('speaking');
        };

        const finishSpeaking = () => {
            if (!this.isSpeaking) return;
            this.isSpeaking = false;
            this.isProcessingCommand = false;
            this.ignoreSpeechResults = false;
            this.setOrbState('idle');
            clearTimeout(this.ttsWatchdogTimer);

            const subtitleCard = document.getElementById('floatingSubtitle');
            if (subtitleCard) {
                setTimeout(() => { subtitleCard.style.display = 'none'; }, 1500);
            }

            // CRITICAL: If Live Conversation is active, automatically resume Siri listening loop!
            if (this.liveConversationActive) {
                setTimeout(() => {
                    this.startVoiceInputSilent();
                }, 250);
            }
        };

        utterance.onend = finishSpeaking;

        utterance.onerror = (e) => {
            console.warn("Speech synthesis notice:", e);
            finishSpeaking();
        };

        // TTS Watchdog: calculated duration + 2.5 second buffer to prevent Chrome hanging
        const wordCount = voiceText.split(/\s+/).length;
        const estimatedMs = (wordCount / 2.8) * 1000 + 2500;
        this.ttsWatchdogTimer = setTimeout(finishSpeaking, estimatedMs);

        // Chrome keep-alive heartbeat while speaking
        if (this.speechKeepAliveTimer) clearInterval(this.speechKeepAliveTimer);
        this.speechKeepAliveTimer = setInterval(() => {
            if (this.synthesis && this.isSpeaking) {
                this.synthesis.pause();
                this.synthesis.resume();
            } else {
                clearInterval(this.speechKeepAliveTimer);
            }
        }, 5000);

        this.synthesis.speak(utterance);
    }

    // ==========================================
    // MEMORY MODULE
    // ==========================================
    initMemoryHandlers() {
        const addMemoryBtn = document.getElementById('addMemoryBtn');
        const memoryModal = document.getElementById('memoryModal');
        const cancelMemBtn = document.getElementById('cancelMemBtn');
        const saveMemBtn = document.getElementById('saveMemBtn');

        if (addMemoryBtn && memoryModal) {
            addMemoryBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                memoryModal.classList.add('active');
            });
            cancelMemBtn.addEventListener('click', () => memoryModal.classList.remove('active'));
            
            saveMemBtn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                const key = document.getElementById('memKeyInput').value.trim();
                const val = document.getElementById('memValInput').value.trim();
                const cat = document.getElementById('memCategoryInput').value;

                if (!key || !val) {
                    alert("Please provide both a key and a value.");
                    return;
                }

                try {
                    await fetch(`${this.apiBase}/api/memory`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ key, value: val, category: cat })
                    });
                    memoryModal.classList.remove('active');
                    document.getElementById('memKeyInput').value = '';
                    document.getElementById('memValInput').value = '';
                    this.loadMemories();
                } catch (e) {
                    alert("Failed to save memory: " + e.message);
                }
            });
        }
    }

    async loadMemories() {
        const memoryList = document.getElementById('memoryList');
        if (!memoryList) return;

        try {
            const res = await fetch(`${this.apiBase}/api/memory`);
            if (!res.ok) throw new Error("Could not fetch memories");
            const data = await res.json();
            const list = data.memories || [];

            if (list.length === 0) {
                memoryList.innerHTML = '<div class="empty-state">No long-term memories recorded. Memories will appear here when added.</div>';
                return;
            }

            memoryList.innerHTML = '';
            list.forEach(m => {
                const card = document.createElement('div');
                card.className = 'memory-item-card';
                card.innerHTML = `
                    <div class="memory-info">
                        <span class="memory-cat-badge">${m.category}</span>
                        <span class="memory-key">${m.key}</span>
                        <span class="memory-val">${m.value}</span>
                    </div>
                    <button class="btn btn-sm btn-outline del-mem-btn" data-id="${m.id}">Delete</button>
                `;
                memoryList.appendChild(card);
            });

            document.querySelectorAll('.del-mem-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    this.triggerHaptic([20]);
                    const id = btn.getAttribute('data-id');
                    if (confirm("Delete this memory?")) {
                        await fetch(`${this.apiBase}/api/memory/${id}`, { method: 'DELETE' });
                        this.loadMemories();
                    }
                });
            });
        } catch (e) {
            memoryList.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    }

    // ==========================================
    // NOTES MODULE
    // ==========================================
    initNotesHandlers() {
        const newNoteBtn = document.getElementById('newNoteBtn');
        const noteModal = document.getElementById('noteModal');
        const cancelNoteBtn = document.getElementById('cancelNoteBtn');
        const saveNoteBtn = document.getElementById('saveNoteBtn');
        const noteSearchInput = document.getElementById('noteSearchInput');

        if (newNoteBtn && noteModal) {
            newNoteBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                noteModal.classList.add('active');
            });
            cancelNoteBtn.addEventListener('click', () => noteModal.classList.remove('active'));

            saveNoteBtn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                const title = document.getElementById('noteTitleInput').value.trim();
                const tags = document.getElementById('noteTagsInput').value.trim();
                const content = document.getElementById('noteContentInput').value.trim();

                if (!title || !content) {
                    alert("Please provide both a title and content.");
                    return;
                }

                try {
                    await fetch(`${this.apiBase}/api/notes`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, tags, content })
                    });
                    noteModal.classList.remove('active');
                    document.getElementById('noteTitleInput').value = '';
                    document.getElementById('noteTagsInput').value = '';
                    document.getElementById('noteContentInput').value = '';
                    this.loadNotes();
                } catch (e) {
                    alert("Failed to save note: " + e.message);
                }
            });
        }

        if (noteSearchInput) {
            noteSearchInput.addEventListener('input', (e) => {
                this.loadNotes(e.target.value.trim());
            });
        }
    }

    async loadNotes(searchQuery = "") {
        const notesGrid = document.getElementById('notesGrid');
        if (!notesGrid) return;

        try {
            const url = searchQuery ? `${this.apiBase}/api/notes?search=${encodeURIComponent(searchQuery)}` : `${this.apiBase}/api/notes`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("Could not fetch notes");
            const data = await res.json();
            const notes = data.notes || [];

            if (notes.length === 0) {
                notesGrid.innerHTML = '<div class="empty-state">No notes found. Create a new note or ask SREE to take a note.</div>';
                return;
            }

            notesGrid.innerHTML = '';
            notes.forEach(n => {
                const card = document.createElement('div');
                card.className = 'note-card';
                card.innerHTML = `
                    <div class="note-title">${n.title}</div>
                    <div class="note-content-preview">${n.content}</div>
                    <div class="note-footer">
                        <span class="note-tags">${n.tags || 'note'}</span>
                        <button class="btn btn-sm btn-outline del-note-btn" data-id="${n.id}">Delete</button>
                    </div>
                `;
                notesGrid.appendChild(card);
            });

            document.querySelectorAll('.del-note-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    this.triggerHaptic([20]);
                    const id = btn.getAttribute('data-id');
                    if (confirm("Delete this note?")) {
                        await fetch(`${this.apiBase}/api/notes/${id}`, { method: 'DELETE' });
                        this.loadNotes();
                    }
                });
            });
        } catch (e) {
            notesGrid.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    }

    // ==========================================
    // REMINDERS & TASKS MODULE
    // ==========================================
    initRemindersHandlers() {
        const newTaskBtn = document.getElementById('newTaskBtn');
        const reminderModal = document.getElementById('reminderModal');
        const cancelRemindBtn = document.getElementById('cancelRemindBtn');
        const saveRemindBtn = document.getElementById('saveRemindBtn');

        if (newTaskBtn && reminderModal) {
            newTaskBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                reminderModal.classList.add('active');
            });
            cancelRemindBtn.addEventListener('click', () => reminderModal.classList.remove('active'));

            saveRemindBtn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                const title = document.getElementById('remindTitleInput').value.trim();
                const due_time = document.getElementById('remindTimeInput').value.trim();

                if (!title) {
                    alert("Please provide a reminder title.");
                    return;
                }

                try {
                    await fetch(`${this.apiBase}/api/reminders`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, due_time, priority: 'normal' })
                    });
                    reminderModal.classList.remove('active');
                    document.getElementById('remindTitleInput').value = '';
                    document.getElementById('remindTimeInput').value = '';
                    this.loadReminders();
                } catch (e) {
                    alert("Failed to save reminder: " + e.message);
                }
            });
        }
    }

    async loadReminders() {
        const tasksList = document.getElementById('tasksList');
        if (!tasksList) return;

        try {
            const res = await fetch(`${this.apiBase}/api/reminders`);
            if (!res.ok) throw new Error("Could not fetch reminders");
            const data = await res.json();
            const list = data.reminders || [];

            if (list.length === 0) {
                tasksList.innerHTML = '<div class="empty-state">No reminders scheduled. Tell SREE "Remind me to..." to add one.</div>';
                return;
            }

            tasksList.innerHTML = '';
            list.forEach(r => {
                const item = document.createElement('div');
                item.className = 'task-item';
                item.innerHTML = `
                    <input type="checkbox" class="task-checkbox toggle-task-cb" data-id="${r.id}" ${r.completed ? 'checked' : ''}>
                    <div class="task-details">
                        <span class="task-title ${r.completed ? 'completed' : ''}">${r.title}</span>
                        <span class="task-time">${r.due_time || 'No due time'}</span>
                    </div>
                    <button class="btn btn-sm btn-outline del-task-btn" data-id="${r.id}">Delete</button>
                `;
                tasksList.appendChild(item);
            });

            document.querySelectorAll('.toggle-task-cb').forEach(cb => {
                cb.addEventListener('change', async (e) => {
                    this.triggerHaptic([20]);
                    const id = cb.getAttribute('data-id');
                    await fetch(`${this.apiBase}/api/reminders/${id}/toggle`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ completed: e.target.checked })
                    });
                    this.loadReminders();
                });
            });

            document.querySelectorAll('.del-task-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    this.triggerHaptic([20]);
                    const id = btn.getAttribute('data-id');
                    await fetch(`${this.apiBase}/api/reminders/${id}`, { method: 'DELETE' });
                    this.loadReminders();
                });
            });
        } catch (e) {
            tasksList.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    }

    // ==========================================
    // LAPTOP AUTOMATION & TELEMETRY MODULE
    // ==========================================
    initAutomationHandlers() {
        document.querySelectorAll('.app-launch-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                const appId = btn.getAttribute('data-app');
                try {
                    const res = await fetch(`${this.apiBase}/api/automation/launch`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ app_id: appId })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        alert(data.message || `Launched ${appId}`);
                    } else {
                        alert(data.detail || "Launch failed");
                    }
                } catch (e) {
                    alert("Execution error: " + e.message);
                }
            });
        });

        const fileSearchBtn = document.getElementById('fileSearchBtn');
        const fileSearchInput = document.getElementById('fileSearchInput');
        const fileResultsBox = document.getElementById('fileResultsBox');

        if (fileSearchBtn && fileSearchInput && fileResultsBox) {
            fileSearchBtn.addEventListener('click', async () => {
                this.triggerHaptic([20]);
                const query = fileSearchInput.value.trim();
                if (!query) return;

                fileResultsBox.style.display = 'block';
                fileResultsBox.innerHTML = 'Searching approved directories...';

                try {
                    const res = await fetch(`${this.apiBase}/api/automation/files/search`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query })
                    });
                    const data = await res.json();
                    const results = data.results || [];

                    if (results.length === 0) {
                        fileResultsBox.innerHTML = 'No matching documents found in approved directories.';
                        return;
                    }

                    fileResultsBox.innerHTML = '';
                    results.forEach(f => {
                        const row = document.createElement('div');
                        row.className = 'file-item';
                        row.innerHTML = `
                            <span><strong>${f.name}</strong> (${f.size_kb} KB)</span>
                            <span style="color: var(--text-secondary);">${f.modified}</span>
                        `;
                        fileResultsBox.appendChild(row);
                    });
                } catch (e) {
                    fileResultsBox.innerHTML = 'Search error: ' + e.message;
                }
            });
        }
    }

    async loadDeviceTelemetry() {
        const uptimeVal = document.getElementById('uptimeVal');
        const batteryVal = document.getElementById('batteryVal');
        const cpuLoadVal = document.getElementById('cpuLoadVal');

        try {
            const res = await fetch(`${this.apiBase}/api/automation/telemetry`);
            if (res.ok) {
                const data = await res.json();
                if (uptimeVal) uptimeVal.textContent = `${data.uptime_hours} hrs`;
                if (cpuLoadVal) cpuLoadVal.textContent = `${data.cpu_percent}%`;
                if (batteryVal) {
                    const b = data.battery;
                    if (b.percent !== undefined) {
                        batteryVal.textContent = `${b.percent}% ${b.power_plugged ? '(Plugged In)' : ''}`;
                    } else {
                        batteryVal.textContent = 'AC Power';
                    }
                }
            }
        } catch (e) {}
    }

    // ==========================================
    // SETTINGS, UNIVERSAL AI BRAIN & MODEL CHIPS
    // ==========================================
    initSettingsHandlers() {
        const providerSelect = document.getElementById('providerSelect');
        const providerCredsBox = document.getElementById('providerCredsBox');
        const apiKeyLabel = document.getElementById('apiKeyLabel');
        const customUrlGroup = document.getElementById('customUrlGroup');
        const customModelGroup = document.getElementById('customModelGroup');
        const saveProviderBtn = document.getElementById('saveProviderBtn');
        const testProviderBtn = document.getElementById('testProviderBtn');
        const providerTestResult = document.getElementById('providerTestResult');
        const toggleApiKeyVisibilityBtn = document.getElementById('toggleApiKeyVisibilityBtn');
        const providerApiKeyInput = document.getElementById('providerApiKeyInput');

        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                const val = e.target.value;
                this.triggerHaptic([15]);
                if (val === 'ollama') {
                    if (providerCredsBox) providerCredsBox.style.display = 'none';
                    this.switchActiveProvider('ollama');
                } else {
                    if (providerCredsBox) providerCredsBox.style.display = 'block';
                    if (val === 'custom') {
                        if (apiKeyLabel) apiKeyLabel.textContent = "API Key (Optional / 'not-needed')";
                        if (customUrlGroup) customUrlGroup.style.display = 'block';
                        if (customModelGroup) customModelGroup.style.display = 'block';
                    } else {
                        if (apiKeyLabel) apiKeyLabel.textContent = `${val.toUpperCase()} API Key`;
                        if (customUrlGroup) customUrlGroup.style.display = 'none';
                        if (customModelGroup) customModelGroup.style.display = 'none';
                    }
                }
            });
        }

        if (toggleApiKeyVisibilityBtn && providerApiKeyInput) {
            toggleApiKeyVisibilityBtn.addEventListener('click', () => {
                providerApiKeyInput.type = providerApiKeyInput.type === 'password' ? 'text' : 'password';
            });
        }

        if (saveProviderBtn && providerSelect) {
            saveProviderBtn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                const provider = providerSelect.value;
                const apiKey = providerApiKeyInput ? providerApiKeyInput.value.trim() : "";
                const customUrl = document.getElementById('customBaseUrlInput')?.value.trim();
                const customModel = document.getElementById('customModelInput')?.value.trim();

                try {
                    const res = await fetch(`${this.apiBase}/api/system/ai/select`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            provider: provider,
                            api_key: apiKey || null,
                            base_url: customUrl || null,
                            model: customModel || null
                        })
                    });
                    const data = await res.json();
                    if (providerTestResult) {
                        providerTestResult.style.display = 'block';
                        providerTestResult.style.color = 'var(--neon-green)';
                        providerTestResult.textContent = `Active Provider: ${data.active_provider.toUpperCase()} (Model: ${data.active_model})`;
                    }
                    this.loadAIProviders();
                } catch (e) {
                    if (providerTestResult) {
                        providerTestResult.style.display = 'block';
                        providerTestResult.style.color = 'var(--danger-red)';
                        providerTestResult.textContent = `Error: ${e.message}`;
                    }
                }
            });
        }

        if (testProviderBtn) {
            testProviderBtn.addEventListener('click', async () => {
                this.triggerHaptic([20]);
                if (providerTestResult) {
                    providerTestResult.style.display = 'block';
                    providerTestResult.style.color = 'var(--cyan-primary)';
                    providerTestResult.textContent = "Testing connection...";
                }
                try {
                    const res = await fetch(`${this.apiBase}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: "Ping SREE connection test" })
                    });
                    const data = await res.json();
                    if (providerTestResult) {
                        providerTestResult.style.color = 'var(--neon-green)';
                        providerTestResult.textContent = `Operational: Received response from ${data.model}`;
                    }
                } catch (e) {
                    if (providerTestResult) {
                        providerTestResult.style.color = 'var(--danger-red)';
                        providerTestResult.textContent = `Connection failed: ${e.message}`;
                    }
                }
            });
        }

        const wakeWordToggle = document.getElementById('wakeWordToggle');
        const wakeWordDesc = document.getElementById('wakeWordDesc');
        if (wakeWordToggle) {
            wakeWordToggle.addEventListener('change', (e) => {
                this.triggerHaptic([20]);
                if (e.target.checked) {
                    this.liveConversationActive = true;
                    if (wakeWordDesc) wakeWordDesc.textContent = "ACTIVE: Continuously listening for 'Hey Sree'";
                    this.startVoiceInputSilent();
                } else {
                    this.liveConversationActive = false;
                    if (wakeWordDesc) wakeWordDesc.textContent = "Disabled (Requires explicit activation)";
                    try { this.recognition.stop(); } catch (err) {}
                }
            });
        }

        // Voice Verification Biometrics Handlers
        const voiceVerificationToggle = document.getElementById('voiceVerificationToggle');
        const voiceEnrollStatusDesc = document.getElementById('voiceEnrollStatusDesc');
        const voiceSpeakerBadge = document.getElementById('voiceSpeakerBadge');
        const startVoiceEnrollWizardBtn = document.getElementById('startVoiceEnrollWizardBtn');
        const clearVoiceProfileBtn = document.getElementById('clearVoiceProfileBtn');

        const loadVoiceStatus = async () => {
            try {
                const res = await fetch(`${this.apiBase}/api/voice/status`);
                if (res.ok) {
                    const data = await res.json();
                    if (voiceVerificationToggle) voiceVerificationToggle.checked = !!data.enabled;
                    if (voiceEnrollStatusDesc) {
                        voiceEnrollStatusDesc.textContent = data.is_enrolled
                            ? `Status: Enrolled (${data.samples_count} voiceprints) - Accuracy Threshold: ${Math.round(data.similarity_threshold * 100)}%`
                            : "Status: Not enrolled. Run 'Enroll_My_Voice.bat' to calibrate your voice.";
                    }
                    if (voiceSpeakerBadge) {
                        voiceSpeakerBadge.textContent = data.is_enrolled ? `Owner: ${data.speaker_name}` : "Owner: Not Enrolled";
                        voiceSpeakerBadge.className = data.is_enrolled ? "pill pill-cyan" : "pill pill-red";
                    }
                }
            } catch (err) {}
        };

        if (voiceVerificationToggle) {
            voiceVerificationToggle.addEventListener('change', async (e) => {
                this.triggerHaptic([20]);
                try {
                    await fetch(`${this.apiBase}/api/voice/toggle`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ enabled: e.target.checked })
                    });
                    loadVoiceStatus();
                } catch (err) {}
            });
        }

        if (startVoiceEnrollWizardBtn) {
            startVoiceEnrollWizardBtn.addEventListener('click', () => {
                this.triggerHaptic([25]);
                alert("Voice Enrollment Wizard:\n\nDouble-click 'Enroll_My_Voice.bat' in your SREE folder (D:\\sri) to calibrate your voice so SREE responds strictly to you!");
            });
        }

        if (clearVoiceProfileBtn) {
            clearVoiceProfileBtn.addEventListener('click', async () => {
                this.triggerHaptic([30]);
                if (confirm("Reset your enrolled voiceprint? SREE will no longer verify speaker voice until re-enrolled.")) {
                    try {
                        await fetch(`${this.apiBase}/api/voice/clear`, { method: 'POST' });
                        loadVoiceStatus();
                    } catch (err) {}
                }
            });
        }

        loadVoiceStatus();

        const copyUrlBtn = document.getElementById('copyUrlBtn');
        if (copyUrlBtn) {
            copyUrlBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                const url = this.mobileUrlDisplay ? this.mobileUrlDisplay.textContent : window.location.origin;
                navigator.clipboard.writeText(url).then(() => {
                    copyUrlBtn.textContent = "Copied!";
                    setTimeout(() => copyUrlBtn.textContent = "Copy URL", 2000);
                });
            });
        }

        const wipeDataBtn = document.getElementById('wipeDataBtn');
        if (wipeDataBtn) {
            wipeDataBtn.addEventListener('click', async () => {
                this.triggerHaptic([35]);
                const confirmed = confirm("CAUTION: This will permanently erase ALL conversations, personal memories, notes, and reminders from your local SQLite database. Are you sure?");
                if (confirmed) {
                    try {
                        const res = await fetch(`${this.apiBase}/api/data/wipe`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ confirm: true })
                        });
                        const data = await res.json();
                        alert(data.message || "Data wiped");
                        this.chatMessages.innerHTML = '';
                        this.conversationHistory = [];
                        this.loadMemories();
                        this.loadNotes();
                        this.loadReminders();
                    } catch (e) {
                        alert("Wipe error: " + e.message);
                    }
                }
            });
        }
    }

    async loadOllamaChips() {
        const chipsContainer = document.getElementById('ollamaChipsContainer');
        if (!chipsContainer) return;

        try {
            const res = await fetch(`${this.apiBase}/api/system/ai/ollama-chips`);
            if (!res.ok) return;
            const data = await res.json();
            const chips = data.chips || [];

            if (chips.length === 0) {
                chipsContainer.innerHTML = '<span class="empty-state">No local Ollama models installed.</span>';
                return;
            }

            chipsContainer.innerHTML = '';
            chips.forEach(c => {
                const chip = document.createElement('span');
                chip.className = `chip ${c.is_active ? 'active' : ''}`;
                chip.textContent = `${c.name} (${c.size_gb}GB)`;
                chip.title = `Click to activate ${c.name}`;
                chip.addEventListener('click', () => {
                    this.triggerHaptic([20]);
                    this.switchActiveProvider('ollama', c.name);
                });
                chipsContainer.appendChild(chip);
            });
        } catch (e) {}
    }

    async loadAIProviders() {
        const providerSelect = document.getElementById('providerSelect');
        const providerPillText = document.getElementById('providerPillText');

        try {
            const res = await fetch(`${this.apiBase}/api/system/ai/status`);
            if (!res.ok) return;
            const data = await res.json();
            this.activeProvider = data.active_provider;
            this.activeModel = data.active_model;

            if (providerSelect) providerSelect.value = data.active_provider;
            if (providerPillText) {
                providerPillText.textContent = `${data.active_provider.toUpperCase()} (${data.active_model.split(':')[0]})`;
            }
            if (this.activeModelLabel) {
                this.activeModelLabel.textContent = `${data.active_provider}:${data.active_model}`;
            }

            this.loadOllamaChips();
        } catch (e) {}
    }

    async switchActiveProvider(provider, model = null) {
        try {
            const res = await fetch(`${this.apiBase}/api/system/ai/select`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, model })
            });
            const data = await res.json();
            this.activeProvider = data.active_provider;
            this.activeModel = data.active_model;
            this.loadAIProviders();
        } catch (e) {}
    }

    // ==========================================
    // DESKTOP SCREEN SHARE & REMOTE COMPUTER ACCESS
    // ==========================================
    initScreenHandlers() {
        this.screenDimensions = { width: 1920, height: 1080 };
        this.isStreamingMjpeg = false;
        this.screenBroadcastStream = null;
        this.screenBroadcastInterval = null;

        const broadcastBtn = document.getElementById('startScreenBroadcastBtn');
        const refreshBtn = document.getElementById('refreshScreenSnapshotBtn');
        const screenshotBtn = document.getElementById('takeScreenshotDiskBtn');
        const liveStreamBtn = document.getElementById('toggleLiveStreamModeBtn');
        const feedImg = document.getElementById('desktopScreenFeed');
        const feedback = document.getElementById('screenActionFeedback');
        const broadcastBadge = document.getElementById('screenBroadcastBadge');
        const cursorPos = document.getElementById('streamCursorPos');
        const remoteTextInput = document.getElementById('remoteTextInput');
        const sendRemoteTextBtn = document.getElementById('sendRemoteTextBtn');

        const showFeedback = (msg, isError = false) => {
            if (!feedback) return;
            feedback.textContent = msg;
            feedback.style.color = isError ? 'var(--danger-red)' : 'var(--cyan-primary)';
            setTimeout(() => {
                if (feedback.textContent === msg) feedback.textContent = '';
            }, 3500);
        };

        // 1. Host Screen Capture & Broadcasting (Native Web Media Stream)
        if (broadcastBtn) {
            broadcastBtn.addEventListener('click', async () => {
                this.triggerHaptic([25]);
                if (this.screenBroadcastStream) {
                    // Stop active broadcast
                    this.stopScreenBroadcast();
                    broadcastBtn.textContent = '📡 Broadcast Desktop Screen';
                    broadcastBtn.classList.remove('btn-danger');
                    broadcastBtn.classList.add('btn-primary');
                    if (broadcastBadge) {
                        broadcastBadge.textContent = 'Stream Ready';
                        broadcastBadge.className = 'pill pill-green';
                    }
                    showFeedback('Desktop broadcast stopped.');
                    return;
                }

                try {
                    const stream = await navigator.mediaDevices.getDisplayMedia({
                        video: { cursor: 'always', displaySurface: 'monitor' },
                        audio: false
                    });

                    this.screenBroadcastStream = stream;
                    broadcastBtn.textContent = '⏹️ Stop Broadcasting';
                    broadcastBtn.classList.remove('btn-primary');
                    broadcastBtn.classList.add('btn-danger');
                    if (broadcastBadge) {
                        broadcastBadge.textContent = 'Broadcasting (Live)';
                        broadcastBadge.className = 'pill pill-cyan';
                    }
                    showFeedback('Desktop screen broadcasting live!');

                    // Setup offscreen canvas and video element
                    const hiddenVideo = document.createElement('video');
                    hiddenVideo.srcObject = stream;
                    hiddenVideo.play();

                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');

                    this.screenBroadcastInterval = setInterval(async () => {
                        if (!this.screenBroadcastStream || hiddenVideo.readyState < 2) return;
                        canvas.width = hiddenVideo.videoWidth || 1280;
                        canvas.height = hiddenVideo.videoHeight || 720;
                        ctx.drawImage(hiddenVideo, 0, 0, canvas.width, canvas.height);

                        const b64 = canvas.toDataURL('image/jpeg', 0.65);
                        try {
                            await fetch(`${this.apiBase}/api/desktop/frame`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ frame_base64: b64 })
                            });
                        } catch (e) {}
                    }, 100);

                    // When user clicks the browser's native "Stop Sharing" floating button
                    stream.getVideoTracks()[0].onended = () => {
                        this.stopScreenBroadcast();
                        broadcastBtn.textContent = '📡 Broadcast Desktop Screen';
                        broadcastBtn.classList.remove('btn-danger');
                        broadcastBtn.classList.add('btn-primary');
                        if (broadcastBadge) {
                            broadcastBadge.textContent = 'Stream Ready';
                            broadcastBadge.className = 'pill pill-green';
                        }
                    };
                } catch (err) {
                    showFeedback(`Broadcast failed: ${err.message}`, true);
                }
            });
        }

        // 2. Refresh Snapshot Button
        if (refreshBtn && feedImg) {
            refreshBtn.addEventListener('click', () => {
                this.triggerHaptic([15]);
                feedImg.src = `${this.apiBase}/api/desktop/snapshot?t=${Date.now()}`;
                showFeedback('Snapshot updated.');
            });
        }

        // 3. Toggle Live Stream Mode Button (MJPEG 15-20 FPS)
        if (liveStreamBtn && feedImg) {
            liveStreamBtn.addEventListener('click', () => {
                this.triggerHaptic([20]);
                this.isStreamingMjpeg = !this.isStreamingMjpeg;
                if (this.isStreamingMjpeg) {
                    feedImg.src = `${this.apiBase}/api/desktop/stream?t=${Date.now()}`;
                    liveStreamBtn.textContent = '⏸️ Pause Stream';
                    liveStreamBtn.classList.add('btn-primary');
                    liveStreamBtn.classList.remove('btn-outline');
                    showFeedback('Live MJPEG stream active.');
                } else {
                    feedImg.src = `${this.apiBase}/api/desktop/snapshot?t=${Date.now()}`;
                    liveStreamBtn.textContent = '▶️ Live Stream (MJPEG)';
                    liveStreamBtn.classList.remove('btn-primary');
                    liveStreamBtn.classList.add('btn-outline');
                    showFeedback('Stream paused on snapshot.');
                }
            });
        }

        // 4. Save Screenshot to Disk
        if (screenshotBtn) {
            screenshotBtn.addEventListener('click', async () => {
                this.triggerHaptic([20]);
                try {
                    const res = await fetch(`${this.apiBase}/api/desktop/screenshot/save`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) {
                        showFeedback(`Screenshot saved to ${data.filename}!`);
                    } else {
                        showFeedback(`Save failed: ${data.error || 'Unknown error'}`, true);
                    }
                } catch (e) {
                    showFeedback('Failed to save screenshot.', true);
                }
            });
        }

        // 5. Interactive Mouse & Touch Control on Stream Image
        if (feedImg) {
            const calculateCoords = (e) => {
                const rect = feedImg.getBoundingClientRect();
                const relX = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                const relY = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
                const hostX = Math.round(relX * this.screenDimensions.width);
                const hostY = Math.round(relY * this.screenDimensions.height);
                return { hostX, hostY };
            };

            feedImg.addEventListener('mousemove', (e) => {
                const { hostX, hostY } = calculateCoords(e);
                if (cursorPos) cursorPos.textContent = `X: ${hostX}, Y: ${hostY}`;
            });

            feedImg.addEventListener('click', async (e) => {
                this.triggerHaptic([15]);
                const { hostX, hostY } = calculateCoords(e);
                try {
                    await fetch(`${this.apiBase}/api/desktop/mouse`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'click', x: hostX, y: hostY, button: 'left' })
                    });
                    showFeedback(`Clicked at (${hostX}, ${hostY})`);
                } catch (e) {}
            });

            feedImg.addEventListener('contextmenu', async (e) => {
                e.preventDefault();
                this.triggerHaptic([20]);
                const { hostX, hostY } = calculateCoords(e);
                try {
                    await fetch(`${this.apiBase}/api/desktop/mouse`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'right_click', x: hostX, y: hostY })
                    });
                    showFeedback(`Right-clicked at (${hostX}, ${hostY})`);
                } catch (e) {}
            });

            feedImg.addEventListener('dblclick', async (e) => {
                this.triggerHaptic([20]);
                const { hostX, hostY } = calculateCoords(e);
                try {
                    await fetch(`${this.apiBase}/api/desktop/mouse`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'double_click', x: hostX, y: hostY })
                    });
                    showFeedback(`Double-clicked at (${hostX}, ${hostY})`);
                } catch (e) {}
            });
        }

        // 6. Remote Keyboard Controls
        const sendRemoteText = async () => {
            if (!remoteTextInput) return;
            const text = remoteTextInput.value;
            if (!text) return;
            this.triggerHaptic([15]);
            try {
                const res = await fetch(`${this.apiBase}/api/desktop/keyboard`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'type', text: text })
                });
                const data = await res.json();
                if (data.success) {
                    showFeedback(`Sent text to PC: "${text}"`);
                    remoteTextInput.value = '';
                } else {
                    showFeedback(`Typing error: ${data.error}`, true);
                }
            } catch (e) {
                showFeedback('Failed to send text.', true);
            }
        };

        if (sendRemoteTextBtn) {
            sendRemoteTextBtn.addEventListener('click', sendRemoteText);
        }
        if (remoteTextInput) {
            remoteTextInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    sendRemoteText();
                }
            });
        }

        document.querySelectorAll('.remote-key-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                this.triggerHaptic([15]);
                const key = btn.getAttribute('data-key');
                if (!key) return;
                try {
                    await fetch(`${this.apiBase}/api/desktop/keyboard`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'press', key: key })
                    });
                    showFeedback(`Pressed key: ${key}`);
                } catch (e) {}
            });
        });

        // 7. Desktop OS Quick Action Buttons
        document.querySelectorAll('.os-action-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                this.triggerHaptic([20]);
                const action = btn.getAttribute('data-action');
                if (!action) return;
                try {
                    const res = await fetch(`${this.apiBase}/api/desktop/action`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: action })
                    });
                    const data = await res.json();
                    if (data.success) {
                        showFeedback(data.message || `Executed ${action}`);
                    } else {
                        showFeedback(`Action failed: ${data.error}`, true);
                    }
                } catch (e) {
                    showFeedback('Failed to execute OS command.', true);
                }
            });
        });
    }

    stopScreenBroadcast() {
        if (this.screenBroadcastInterval) {
            clearInterval(this.screenBroadcastInterval);
            this.screenBroadcastInterval = null;
        }
        if (this.screenBroadcastStream) {
            this.screenBroadcastStream.getTracks().forEach(t => t.stop());
            this.screenBroadcastStream = null;
        }
    }

    async loadScreenStatus() {
        try {
            const res = await fetch(`${this.apiBase}/api/desktop/status`);
            if (res.ok) {
                const data = await res.json();
                if (data.screen) {
                    this.screenDimensions = data.screen;
                    const resBadge = document.getElementById('screenResolutionBadge');
                    if (resBadge) resBadge.textContent = `${data.screen.width} x ${data.screen.height}`;
                }
                const cursorPos = document.getElementById('streamCursorPos');
                if (cursorPos && data.cursor) {
                    cursorPos.textContent = `X: ${data.cursor.x}, Y: ${data.cursor.y}`;
                }
            }
        } catch (e) {}
    }

    initTelemetryPoller() {
        const updateTelemetry = async () => {
            try {
                const res = await fetch(`${this.apiBase}/api/system/status`);
                if (res.ok) {
                    const data = await res.json();
                    
                    const ram = data.hardware;
                    if (this.ramUsageLabel && ram) {
                        this.ramUsageLabel.textContent = `${ram.ram_used_gb} / ${ram.ram_total_gb} GB`;
                    }

                    const ai = data.ai_engine;
                    if (this.ollamaPill) {
                        if (ai.ollama_online) {
                            this.ollamaPill.textContent = "Ollama Active";
                            this.ollamaPill.style.color = "var(--neon-green)";
                        } else {
                            this.ollamaPill.textContent = "Ollama Offline";
                            this.ollamaPill.style.color = "var(--danger-red)";
                        }
                    }

                    if (ai.installed_models && ai.installed_models.length > 0) {
                        if (this.activeModelLabel) {
                            this.activeModelLabel.textContent = ai.installed_models[0];
                        }
                    }

                    const ass = data.assistant;
                    if (ass && ass.mobile_url) {
                        if (this.mobileUrlDisplay) this.mobileUrlDisplay.textContent = ass.mobile_url;
                        if (this.modalMobileUrlDisplay) this.modalMobileUrlDisplay.textContent = ass.mobile_url;
                    }
                }
            } catch (e) {}
        };

        updateTelemetry();
        setInterval(updateTelemetry, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.sree = new SreeApp();
});
