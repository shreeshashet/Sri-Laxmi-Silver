(() => {
    const languageButton = document.querySelector(".language-toggle");
    const menuButton = document.querySelector(".menu-toggle");
    const navigation = document.querySelector(".main-nav");
    const filterButtons = document.querySelectorAll(".filter-button");
    const productCards = document.querySelectorAll(".product-card");
    const musicButton = document.querySelector(".music-toggle");
    const musicLabel = musicButton?.querySelector(".music-toggle-label");
    let audioContext;
    let musicGain;
    let chordTimer;
    let chordIndex = 0;
    let musicIsPlaying = false;

    const chords = [
        { pad: [50, 54, 57, 62], melody: [74, 69, 66, 69] },
        { pad: [47, 50, 54, 59], melody: [71, 66, 62, 66] },
        { pad: [43, 47, 50, 55], melody: [67, 74, 71, 74] },
        { pad: [45, 49, 52, 57], melody: [69, 76, 73, 76] },
    ];

    const midiToFrequency = (note) => 440 * (2 ** ((note - 69) / 12));

    const updateMusicButton = () => {
        const language = document.documentElement.lang;
        const label = language === "kn"
            ? (musicIsPlaying ? "ಸಂಗೀತ ಆನ್" : "ಸಂಗೀತ ಆಫ್")
            : (musicIsPlaying ? "Music on" : "Music off");
        musicLabel.textContent = label;
        musicButton.setAttribute("aria-pressed", String(musicIsPlaying));
        musicButton.setAttribute(
            "aria-label",
            language === "kn"
                ? (musicIsPlaying ? "ಸಂಗೀತವನ್ನು ಆಫ್ ಮಾಡಿ" : "ಸಂಗೀತವನ್ನು ಆನ್ ಮಾಡಿ")
                : (musicIsPlaying ? "Turn music off" : "Turn music on")
        );
    };

    const playChord = () => {
        if (!musicIsPlaying) return;

        const chord = chords[chordIndex % chords.length];
        const startTime = audioContext.currentTime + 0.03;
        chord.pad.forEach((note) => {
            const oscillator = audioContext.createOscillator();
            const voiceGain = audioContext.createGain();
            oscillator.type = "sine";
            oscillator.frequency.value = midiToFrequency(note);
            voiceGain.gain.setValueAtTime(0.0001, startTime);
            voiceGain.gain.linearRampToValueAtTime(0.025, startTime + 0.8);
            voiceGain.gain.setValueAtTime(0.025, startTime + 2.6);
            voiceGain.gain.exponentialRampToValueAtTime(0.0001, startTime + 3.8);
            oscillator.connect(voiceGain);
            voiceGain.connect(musicGain);
            oscillator.start(startTime);
            oscillator.stop(startTime + 3.85);
        });

        chord.melody.forEach((note, index) => {
            const noteStart = startTime + index * 0.8;
            const oscillator = audioContext.createOscillator();
            const voiceGain = audioContext.createGain();
            oscillator.type = "sine";
            oscillator.frequency.value = midiToFrequency(note);
            voiceGain.gain.setValueAtTime(0.0001, noteStart);
            voiceGain.gain.linearRampToValueAtTime(0.035, noteStart + 0.025);
            voiceGain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.65);
            oscillator.connect(voiceGain);
            voiceGain.connect(musicGain);
            oscillator.start(noteStart);
            oscillator.stop(noteStart + 0.7);
        });

        chordIndex += 1;
    };

    if (musicButton && musicLabel) {
        musicButton.addEventListener("click", async () => {
            try {
                if (!audioContext) {
                    if (!window.AudioContext) {
                        musicLabel.textContent = "Audio unavailable";
                        musicButton.setAttribute("aria-label", "Audio playback is unavailable");
                        return;
                    }
                    audioContext = new AudioContext();
                    musicGain = audioContext.createGain();
                    musicGain.gain.value = 0;
                    musicGain.connect(audioContext.destination);
                }

                if (musicIsPlaying) {
                    musicIsPlaying = false;
                    clearInterval(chordTimer);
                    musicGain.gain.setTargetAtTime(0, audioContext.currentTime, 0.2);
                } else {
                    await audioContext.resume();
                    musicIsPlaying = true;
                    musicGain.gain.setTargetAtTime(0.35, audioContext.currentTime, 0.7);
                    playChord();
                    chordTimer = setInterval(playChord, 4000);
                }
                updateMusicButton();
            } catch (error) {
                musicIsPlaying = false;
                clearInterval(chordTimer);
                musicLabel.textContent = "Music unavailable";
                musicButton.setAttribute("aria-pressed", "false");
                musicButton.setAttribute("aria-label", "Audio playback is unavailable");
                console.error("Could not start the SLJW music player.", error);
            }
        });
    }

    languageButton.addEventListener("click", () => {
        const nextLanguage = document.documentElement.lang === "en" ? "kn" : "en";
        document.documentElement.lang = nextLanguage;
        document.querySelectorAll("[data-en][data-kn]").forEach((element) => {
            element.textContent = element.dataset[nextLanguage];
        });
        languageButton.textContent = nextLanguage === "en" ? "ಕನ್ನಡ" : "English";
        languageButton.setAttribute(
            "aria-label",
            nextLanguage === "en" ? "Switch language to Kannada" : "Switch language to English"
        );
        if (musicButton && musicLabel) updateMusicButton();
    });

    menuButton.addEventListener("click", () => {
        const isOpen = menuButton.getAttribute("aria-expanded") === "true";
        menuButton.setAttribute("aria-expanded", String(!isOpen));
        menuButton.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
        navigation.classList.toggle("is-open", !isOpen);
    });

    navigation.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener("click", () => {
            navigation.classList.remove("is-open");
            menuButton.setAttribute("aria-expanded", "false");
            menuButton.setAttribute("aria-label", "Open navigation");
        });
    });

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const selectedFilter = button.dataset.filter;
            filterButtons.forEach((filterButton) => {
                const isActive = filterButton === button;
                filterButton.classList.toggle("active", isActive);
                filterButton.setAttribute("aria-pressed", String(isActive));
            });
            productCards.forEach((card) => {
                card.hidden = selectedFilter !== "all" && card.dataset.category !== selectedFilter;
            });
        });
        button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    });
})();
