/**
 * Radio Agnostic frontend app.
 * Canonical runtime served from /frontend by the FastAPI backend.
 */

const runtimeMode = window.RADIO_AGNOSTIC_MODE || "backend";
const isLocalDev =
    ["localhost", "127.0.0.1"].includes(window.location.hostname) || window.location.protocol === "file:";
const API_BASE =
    runtimeMode === "backend"
        ? isLocalDev
            ? `http://${window.location.hostname === "127.0.0.1" ? "127.0.0.1" : "localhost"}:8000/api`
            : "/api"
        : null;
const PHP_PROXY_BASE = window.RADIO_AGNOSTIC_PHP_PROXY || "/proxy.php?url=";

let state = {
    stations: [],
    genres: [],
    nowPlaying: [],
    schedules: JSON.parse(localStorage.getItem("radio_agnostic_schedules") || "[]"),
    currentStation: null,
    isPlaying: false,
    isLoading: false,
    activeGenre: null,
    activeTab: "discover",
    playbackPlan: [],
    playbackPlanIndex: -1,
};

const elements = {
    tabs: document.querySelectorAll(".tab-btn"),
    tabContents: document.querySelectorAll(".tab-content"),
    nowPlayingFeed: document.getElementById("now-playing-feed"),
    stationsGrid: document.getElementById("stations-grid"),
    genreFilters: document.getElementById("genre-filters"),
    searchInput: document.getElementById("search-input"),
    playerBar: document.getElementById("player-bar"),
    playerStation: document.getElementById("player-station"),
    playerShow: document.getElementById("player-show"),
    playerLogo: document.getElementById("player-logo"),
    playPauseBtn: document.getElementById("play-pause-btn"),
    volumeSlider: document.getElementById("volume-slider"),
    audioPlayer: document.getElementById("audio-player"),
    schedulesList: document.getElementById("schedules-list"),
    createScheduleBtn: document.getElementById("create-schedule-btn"),
    scheduleModal: document.getElementById("schedule-modal"),
    scheduleForm: document.getElementById("schedule-form"),
    closeModalBtns: document.querySelectorAll(".close-modal, .close-btn"),
};

async function apiGet(path) {
    if (!API_BASE) {
        throw new Error("API is unavailable in static mode");
    }
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }
    return response.json();
}

async function fetchStations() {
    try {
        return await apiGet("/stations");
    } catch (error) {
        console.error("Error fetching stations:", error);
        return [];
    }
}

async function fetchGenres() {
    try {
        return await apiGet("/genres");
    } catch (error) {
        console.error("Error fetching genres:", error);
        return [];
    }
}

async function fetchNowPlaying(genre = null) {
    try {
        let url = "/now-playing";
        if (genre) url += `?genre=${encodeURIComponent(genre)}`;
        return await apiGet(url);
    } catch (error) {
        console.error("Error fetching now playing:", error);
        return [];
    }
}

function renderGenreFilters() {
    elements.genreFilters.innerHTML = `
        <button class="genre-pill ${!state.activeGenre ? "active" : ""}" data-genre="">
            All
        </button>
        ${state.genres
            .map(
                (genre) => `
            <button class="genre-pill ${state.activeGenre === genre ? "active" : ""}" data-genre="${genre}">
                ${genre.charAt(0).toUpperCase() + genre.slice(1)}
            </button>
        `
            )
            .join("")}
    `;

    elements.genreFilters.querySelectorAll(".genre-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
            state.activeGenre = pill.dataset.genre || null;
            renderGenreFilters();
            loadNowPlaying();
        });
    });
}

function renderStationCard(station, show = null) {
    const isCurrentStation = state.currentStation?.id === station.id;
    const isPlaying = isCurrentStation && state.isPlaying;
    const isLoading = isCurrentStation && state.isLoading;

    let buttonIcon = "▶️";
    if (isLoading) buttonIcon = "⏳";
    else if (isPlaying) buttonIcon = "⏸️";

    let showInfoHTML = "";
    if (show) {
        const scheduleBtnHTML =
            typeof openAddToScheduleModal === "function"
                ? `<button class="schedule-add-btn" data-station-id="${station.id}" data-show-name="${show.title || ""}">📅 Add to Schedule</button>`
                : "";

        const showGenres = show.genres || (show.genre ? [show.genre] : []);
        showInfoHTML = `
            <div class="show-info">
                <div class="show-title">${show.title || "Unknown Show"}</div>
                <div class="show-time">${formatTime(show.start_time)} - ${formatTime(show.end_time)}</div>
                ${
                    showGenres.length
                        ? `<div class="show-genres">${showGenres.map((g) => `<span class="genre-tag">${g}</span>`).join("")}</div>`
                        : ""
                }
                ${scheduleBtnHTML}
            </div>
        `;
    }

    return `
        <div class="station-card ${isPlaying ? "playing" : ""} ${isLoading ? "loading" : ""}" data-station-id="${station.id}">
            <div class="station-header">
                <div class="station-logo">📻</div>
                <div class="station-info">
                    <h3>${station.name}</h3>
                    <div class="location">${station.location.city}, ${station.location.state}</div>
                </div>
                <button class="play-btn ${isLoading ? "loading" : ""}" data-station-id="${station.id}" ${isLoading ? "disabled" : ""}>
                    ${buttonIcon}
                </button>
            </div>
            ${showInfoHTML}
        </div>
    `;
}

function renderNowPlaying() {
    if (state.nowPlaying.length === 0) {
        elements.nowPlayingFeed.innerHTML = `
            <div class="empty-state">
                <p>No stations currently playing${state.activeGenre ? ` ${state.activeGenre}` : ""}.</p>
            </div>
        `;
        return;
    }

    elements.nowPlayingFeed.innerHTML = state.nowPlaying.map((item) => renderStationCard(item.station, item.show)).join("");

    elements.nowPlayingFeed.querySelectorAll(".station-card").forEach((card) => {
        card.addEventListener("click", () => {
            const stationId = card.dataset.stationId;
            const station = state.stations.find((s) => s.id === stationId);
            if (station) playStation(station);
        });
    });

    elements.nowPlayingFeed.querySelectorAll(".play-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const stationId = btn.dataset.stationId;
            const station = state.stations.find((s) => s.id === stationId);
            if (station) togglePlay(station);
        });
    });

    elements.nowPlayingFeed.querySelectorAll(".schedule-add-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const stationId = btn.dataset.stationId;
            const showName = btn.dataset.showName;
            if (typeof openAddToScheduleModal === "function") {
                openAddToScheduleModal(stationId, showName);
            }
        });
    });
}

function renderStationsGrid() {
    elements.stationsGrid.innerHTML = state.stations.map((station) => renderStationCard(station)).join("");

    elements.stationsGrid.querySelectorAll(".station-card").forEach((card) => {
        card.addEventListener("click", () => {
            const stationId = card.dataset.stationId;
            const station = state.stations.find((s) => s.id === stationId);
            if (station) playStation(station);
        });
    });
}

function renderSchedules() {
    if (state.schedules.length === 0) {
        elements.schedulesList.innerHTML = `
            <div class="empty-state">
                <p>No schedules yet. Create one to get started.</p>
            </div>
        `;
        return;
    }

    elements.schedulesList.innerHTML = state.schedules
        .map((schedule) => {
            const slotCount = schedule.slots?.length || 0;
            const nextSlot = typeof getNextSlot === "function" ? getNextSlot(schedule) : null;

            return `
                <div class="station-card schedule-card" data-schedule-id="${schedule.id}">
                    <div class="station-header">
                        <div class="station-logo">📅</div>
                        <div class="station-info">
                            <h3>${schedule.name}</h3>
                            <div class="location">${slotCount} show${slotCount !== 1 ? "s" : ""} scheduled</div>
                        </div>
                    </div>
                    ${
                        nextSlot
                            ? `
                        <div class="show-info">
                            <div class="show-title">Next: ${nextSlot.showName || "Show"}</div>
                            <div class="show-time">${["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][nextSlot.dayOfWeek]} at ${formatTime12h(nextSlot.time)}</div>
                        </div>
                    `
                            : ""
                    }
                </div>
            `;
        })
        .join("");
}

function createSchedule(name) {
    state.schedules.push({
        id: Date.now().toString(),
        name: name,
        slots: [],
        created_at: new Date().toISOString(),
    });
    saveSchedules();
    renderSchedules();
}

function saveSchedules() {
    localStorage.setItem("radio_agnostic_schedules", JSON.stringify(state.schedules));
}

function openModal() {
    elements.scheduleModal.classList.remove("hidden");
}

function closeModal() {
    elements.scheduleModal.classList.add("hidden");
    elements.scheduleForm.reset();
}

function formatTime(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return dateStr;
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function formatTime12h(time24) {
    if (!time24) return "";
    const [hours, minutes] = time24.split(":");
    const h = parseInt(hours, 10);
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 || 12;
    return `${h12}:${minutes} ${ampm}`;
}

function buildPlaybackPlan(station) {
    const streams = [...(station.streams || [])];
    if (!streams.length) return [];

    streams.sort((a, b) => (a.priority ?? 9999) - (b.priority ?? 9999));
    const mode =
        station.playback_mode || (station.cors_status === "open" ? "direct_then_proxy" : "proxy_required");
    const plan = [];

    streams.forEach((stream, streamIndex) => {
        if (mode === "direct") {
            plan.push({ streamIndex, mode: "direct", url: stream.url });
        } else if (mode === "proxy_required") {
            plan.push({ streamIndex, mode: "proxy", url: getProxyUrl(station.id, streamIndex, stream.url) });
        } else {
            plan.push({ streamIndex, mode: "direct", url: stream.url });
            plan.push({ streamIndex, mode: "proxy", url: getProxyUrl(station.id, streamIndex, stream.url) });
        }
    });

    return plan;
}

function getProxyUrl(stationId, streamIndex, directUrl) {
    if (runtimeMode === "backend") {
        return `${API_BASE}/proxy/stream/${stationId}?stream_index=${streamIndex}`;
    }
    return `${PHP_PROXY_BASE}${encodeURIComponent(directUrl)}`;
}

function withAttemptListeners(timeoutMs = 12000) {
    return new Promise((resolve, reject) => {
        const onPlaying = () => cleanup(resolve);
        const onError = () => cleanup(() => reject(new Error("Audio element error")));
        const timeout = setTimeout(() => cleanup(() => reject(new Error("Playback timeout"))), timeoutMs);

        function cleanup(done) {
            clearTimeout(timeout);
            elements.audioPlayer.removeEventListener("playing", onPlaying);
            elements.audioPlayer.removeEventListener("error", onError);
            if (typeof done === "function") done();
        }

        elements.audioPlayer.addEventListener("playing", onPlaying, { once: true });
        elements.audioPlayer.addEventListener("error", onError, { once: true });
    });
}

async function playStation(station) {
    if (state.currentStation?.id === station.id && state.isPlaying) {
        togglePlay(station);
        return;
    }

    const plan = buildPlaybackPlan(station);
    if (!plan.length) {
        alert("No stream available for this station.");
        return;
    }

    state.currentStation = station;
    state.playbackPlan = plan;
    state.playbackPlanIndex = -1;
    state.isLoading = true;
    state.isPlaying = false;
    updatePlayerUI();

    for (let idx = 0; idx < plan.length; idx++) {
        const step = plan[idx];
        state.playbackPlanIndex = idx;
        const streamType = step.mode === "proxy" ? "proxied" : "direct";
        console.log(`Playback attempt ${idx + 1}/${plan.length}: ${station.name} via ${streamType}`);

        try {
            const waitForPlay = withAttemptListeners();
            elements.audioPlayer.src = step.url;
            elements.audioPlayer.volume = elements.volumeSlider.value / 100;
            const playPromise = elements.audioPlayer.play();
            if (playPromise !== undefined) {
                await playPromise;
            }
            await waitForPlay;

            state.isPlaying = true;
            state.isLoading = false;
            updatePlayerUI();
            renderNowPlaying();
            updateMediaSession(station);
            return;
        } catch (error) {
            console.warn(`Attempt failed (${streamType})`, error);
        }
    }

    state.isPlaying = false;
    state.isLoading = false;
    updatePlayerUI();
    alert(`Failed to play ${station.name}. The stream may be unavailable right now.`);
}

function togglePlay(station) {
    if (state.currentStation?.id !== station.id) {
        playStation(station);
        return;
    }

    if (state.isPlaying) {
        elements.audioPlayer.pause();
        state.isPlaying = false;
    } else {
        elements.audioPlayer
            .play()
            .then(() => {
                state.isPlaying = true;
                updatePlayerUI();
            })
            .catch((error) => {
                console.error("Resume playback failed:", error);
                playStation(station);
            });
    }

    updatePlayerUI();
    renderNowPlaying();
}

function updatePlayerUI() {
    if (!state.currentStation) {
        elements.playerBar.classList.add("hidden");
        return;
    }

    elements.playerBar.classList.remove("hidden");
    elements.playerStation.textContent = state.currentStation.name;
    elements.playerShow.textContent = state.currentStation.callsign || "";

    if (state.isLoading) {
        elements.playPauseBtn.textContent = "⏳";
        elements.playPauseBtn.disabled = true;
    } else if (state.isPlaying) {
        elements.playPauseBtn.textContent = "⏸️";
        elements.playPauseBtn.disabled = false;
    } else {
        elements.playPauseBtn.textContent = "▶️";
        elements.playPauseBtn.disabled = false;
    }

    const streamInfo = document.getElementById("player-stream-info");
    if (streamInfo && state.currentStation.streams) {
        const step = state.playbackPlan[state.playbackPlanIndex] || null;
        const currentStream = step ? state.currentStation.streams[step.streamIndex] : state.currentStation.streams[0];

        let infoText = "";
        if (currentStream) {
            const quality =
                currentStream.quality === "high"
                    ? "High Quality"
                    : currentStream.quality === "low"
                      ? "Low Bandwidth"
                      : currentStream.quality;
            const format = (currentStream.format || "unknown").toUpperCase();
            infoText = `${quality} • ${format}`;
        }
        if (step?.mode === "proxy") {
            infoText += " • Proxied";
        }
        streamInfo.textContent = infoText;
    }
}

function updateMediaSession(station) {
    if ("mediaSession" in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: station.name,
            artist: station.callsign || station.name,
            album: "Radio Agnostic",
            artwork: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }],
        });

        navigator.mediaSession.setActionHandler("play", () => {
            elements.audioPlayer.play();
            state.isPlaying = true;
            updatePlayerUI();
        });

        navigator.mediaSession.setActionHandler("pause", () => {
            elements.audioPlayer.pause();
            state.isPlaying = false;
            updatePlayerUI();
        });

        navigator.mediaSession.setActionHandler("stop", () => {
            elements.audioPlayer.pause();
            elements.audioPlayer.currentTime = 0;
            state.isPlaying = false;
            updatePlayerUI();
        });
    }
}

elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const tabName = tab.dataset.tab;
        state.activeTab = tabName;

        elements.tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        elements.tabContents.forEach((content) => content.classList.remove("active"));
        document.getElementById(`${tabName}-tab`).classList.add("active");
    });
});

elements.playPauseBtn.addEventListener("click", () => {
    if (state.currentStation) {
        togglePlay(state.currentStation);
    }
});

document.getElementById("add-current-to-schedule")?.addEventListener("click", () => {
    if (state.currentStation && typeof openAddToScheduleModal === "function") {
        openAddToScheduleModal(state.currentStation.id, "");
    }
});

elements.volumeSlider.addEventListener("input", (e) => {
    elements.audioPlayer.volume = e.target.value / 100;
});

elements.createScheduleBtn.addEventListener("click", openModal);
elements.closeModalBtns.forEach((btn) => {
    btn.addEventListener("click", closeModal);
});

elements.scheduleForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("schedule-name").value.trim();
    if (name) {
        createSchedule(name);
        closeModal();
    }
});

elements.searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase();
    const cards = elements.nowPlayingFeed.querySelectorAll(".station-card");
    cards.forEach((card) => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? "" : "none";
    });
});

elements.audioPlayer.addEventListener("loadstart", () => {
    state.isLoading = true;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener("canplay", () => {
    state.isLoading = false;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener("playing", () => {
    state.isPlaying = true;
    state.isLoading = false;
    updatePlayerUI();
    renderNowPlaying();
});

elements.audioPlayer.addEventListener("pause", () => {
    state.isPlaying = false;
    updatePlayerUI();
    renderNowPlaying();
});

elements.audioPlayer.addEventListener("waiting", () => {
    state.isLoading = true;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener("stalled", () => {
    console.warn("Audio stalled - buffering issue");
    state.isLoading = true;
    updatePlayerUI();
});

async function init() {
    const [stations, genres] = await Promise.all([fetchStations(), fetchGenres()]);
    state.stations = stations;
    state.genres = genres;

    renderGenreFilters();
    renderStationsGrid();
    renderSchedules();
    await loadNowPlaying();

    setInterval(loadNowPlaying, 60000);
}

async function loadNowPlaying() {
    const nowPlaying = await fetchNowPlaying(state.activeGenre);
    state.nowPlaying = nowPlaying;
    renderNowPlaying();
}

document.addEventListener("DOMContentLoaded", init);

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(console.error);
}
