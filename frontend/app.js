/**
 * Radio Agnostic - Vanilla JS App
 * No frameworks, just clean code
 */

// API Configuration
const isLocalDev =
    ['localhost', '127.0.0.1'].includes(window.location.hostname) ||
    window.location.protocol === 'file:';
const API_BASE = isLocalDev
    ? `http://${window.location.hostname === '127.0.0.1' ? '127.0.0.1' : 'localhost'}:8000/api`
    : '/api';

// State
let state = {
    stations: [],
    genres: [],
    nowPlaying: [],
    schedules: JSON.parse(localStorage.getItem('radio_agnostic_schedules') || '[]'),
    currentStation: null,
    isPlaying: false,
    isLoading: false,
    currentStreamIndex: 0,
    activeGenre: null,
    activeTab: 'discover'
};

// DOM Elements
const elements = {
    tabs: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    nowPlayingFeed: document.getElementById('now-playing-feed'),
    stationsGrid: document.getElementById('stations-grid'),
    genreFilters: document.getElementById('genre-filters'),
    searchInput: document.getElementById('search-input'),
    playerBar: document.getElementById('player-bar'),
    playerStation: document.getElementById('player-station'),
    playerShow: document.getElementById('player-show'),
    playerLogo: document.getElementById('player-logo'),
    playPauseBtn: document.getElementById('play-pause-btn'),
    volumeSlider: document.getElementById('volume-slider'),
    audioPlayer: document.getElementById('audio-player'),
    schedulesList: document.getElementById('schedules-list'),
    createScheduleBtn: document.getElementById('create-schedule-btn'),
    scheduleModal: document.getElementById('schedule-modal'),
    scheduleForm: document.getElementById('schedule-form'),
    closeModalBtns: document.querySelectorAll('.close-modal, .close-btn')
};

// API Functions
async function fetchStations() {
    try {
        const response = await fetch(`${API_BASE}/stations`);
        if (!response.ok) throw new Error('Failed to fetch stations');
        return await response.json();
    } catch (error) {
        console.error('Error fetching stations:', error);
        return [];
    }
}

async function fetchGenres() {
    try {
        const response = await fetch(`${API_BASE}/genres`);
        if (!response.ok) throw new Error('Failed to fetch genres');
        return await response.json();
    } catch (error) {
        console.error('Error fetching genres:', error);
        return [];
    }
}

async function fetchNowPlaying(genre = null) {
    try {
        let url = `${API_BASE}/now-playing`;
        if (genre) url += `?genre=${encodeURIComponent(genre)}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch now playing');
        return await response.json();
    } catch (error) {
        console.error('Error fetching now playing:', error);
        return [];
    }
}

// UI Functions
function renderGenreFilters() {
    elements.genreFilters.innerHTML = `
        <button class="genre-pill ${!state.activeGenre ? 'active' : ''}" data-genre="">
            All
        </button>
        ${state.genres.map(genre => `
            <button class="genre-pill ${state.activeGenre === genre ? 'active' : ''}" data-genre="${genre}">
                ${genre.charAt(0).toUpperCase() + genre.slice(1)}
            </button>
        `).join('')}
    `;

    // Add click handlers
    elements.genreFilters.querySelectorAll('.genre-pill').forEach(pill => {
        pill.addEventListener('click', () => {
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
    
    let buttonIcon = '▶️';
    if (isLoading) buttonIcon = '⏳';
    else if (isPlaying) buttonIcon = '⏸️';
    
    // Generate show info HTML if available
    let showInfoHTML = '';
    if (show) {
        const scheduleBtnHTML = typeof openAddToScheduleModal === 'function' 
            ? `<button class="schedule-add-btn" data-station-id="${station.id}" data-show-name="${show.title || ''}">📅 Add to Schedule</button>`
            : '';
            
        showInfoHTML = `
            <div class="show-info">
                <div class="show-title">${show.title || 'Unknown Show'}</div>
                <div class="show-time">${formatTime(show.start_time)} - ${formatTime(show.end_time)}</div>
                ${show.genres ? `
                    <div class="show-genres">
                        ${show.genres.map(g => `<span class="genre-tag">${g}</span>`).join('')}
                    </div>
                ` : ''}
                ${scheduleBtnHTML}
            </div>
        `;
    }
    
    return `
        <div class="station-card ${isPlaying ? 'playing' : ''} ${isLoading ? 'loading' : ''}" data-station-id="${station.id}">
            <div class="station-header">
                <div class="station-logo">📻</div>
                <div class="station-info">
                    <h3>${station.name}</h3>
                    <div class="location">${station.location.city}, ${station.location.state}</div>
                </div>
                <button class="play-btn ${isLoading ? 'loading' : ''}" data-station-id="${station.id}" ${isLoading ? 'disabled' : ''}>
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
                <p>No stations currently playing${state.activeGenre ? ` ${state.activeGenre}` : ''}.</p>
            </div>
        `;
        return;
    }

    elements.nowPlayingFeed.innerHTML = state.nowPlaying.map(item => 
        renderStationCard(item.station, item.show)
    ).join('');

    // Add click handlers
    elements.nowPlayingFeed.querySelectorAll('.station-card').forEach(card => {
        card.addEventListener('click', (e) => {
            const stationId = card.dataset.stationId;
            const station = state.stations.find(s => s.id === stationId);
            if (station) playStation(station);
        });
    });

    elements.nowPlayingFeed.querySelectorAll('.play-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const stationId = btn.dataset.stationId;
            const station = state.stations.find(s => s.id === stationId);
            if (station) togglePlay(station);
        });
    });
    
    // Add schedule button handlers
    elements.nowPlayingFeed.querySelectorAll('.schedule-add-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const stationId = btn.dataset.stationId;
            const showName = btn.dataset.showName;
            if (typeof openAddToScheduleModal === 'function') {
                openAddToScheduleModal(stationId, showName);
            }
        });
    });
}

function renderStationsGrid() {
    elements.stationsGrid.innerHTML = state.stations.map(station => 
        renderStationCard(station)
    ).join('');

    // Add click handlers
    elements.stationsGrid.querySelectorAll('.station-card').forEach(card => {
        card.addEventListener('click', () => {
            const stationId = card.dataset.stationId;
            const station = state.stations.find(s => s.id === stationId);
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

    elements.schedulesList.innerHTML = state.schedules.map(schedule => {
        const slotCount = schedule.slots?.length || 0;
        const nextSlot = typeof getNextSlot === 'function' ? getNextSlot(schedule) : null;
        
        return `
            <div class="station-card schedule-card" data-schedule-id="${schedule.id}">
                <div class="station-header">
                    <div class="station-logo">📅</div>
                    <div class="station-info">
                        <h3>${schedule.name}</h3>
                        <div class="location">${slotCount} show${slotCount !== 1 ? 's' : ''} scheduled</div>
                    </div>
                </div>
                ${nextSlot ? `
                    <div class="show-info">
                        <div class="show-title">Next: ${nextSlot.showName || 'Show'}</div>
                        <div class="show-time">${['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][nextSlot.dayOfWeek]} at ${formatTime12h(nextSlot.time)}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
    
    // Add click handlers to schedule cards
    elements.schedulesList.querySelectorAll('.schedule-card').forEach(card => {
        card.addEventListener('click', () => {
            const scheduleId = card.dataset.scheduleId;
            if (typeof openScheduleDetail === 'function') {
                openScheduleDetail(scheduleId);
            }
        });
    });
}

function formatTime12h(time24) {
    if (!time24) return '';
    const [hours, minutes] = time24.split(':');
    const h = parseInt(hours);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${minutes} ${ampm}`;
}

// Player Functions
function getStreamUrl(station, streamIndex = 0, useProxy = false) {
    /**
    Get stream URL with CORS handling
    - First try direct URL
    - If CORS-blocked, fall back to backend proxy
    */
    if (useProxy) {
        return `${API_BASE}/proxy/stream/${station.id}`;
    }
    
    const stream = station.streams?.[streamIndex] || station.streams?.[0];
    return stream?.url || null;
}

function playStation(station, streamIndex = 0, useProxy = false) {
    if (state.currentStation?.id === station.id && streamIndex === 0 && !useProxy) {
        togglePlay(station);
        return;
    }

    state.currentStation = station;
    state.currentStreamIndex = streamIndex;
    state.isLoading = true;
    state.usingProxy = useProxy;
    updatePlayerUI();
    
    // Get stream URL (direct or proxied)
    const streamUrl = getStreamUrl(station, streamIndex, useProxy);
    if (!streamUrl) {
        alert('No stream available for this station');
        state.isLoading = false;
        return;
    }

    // Set audio source
    elements.audioPlayer.src = streamUrl;
    elements.audioPlayer.volume = elements.volumeSlider.value / 100;
    
    console.log(`Playing: ${station.name} from ${useProxy ? 'proxy' : 'direct'} (${streamUrl})`);
    
    // Try to play
    const playPromise = elements.audioPlayer.play();
    
    if (playPromise !== undefined) {
        playPromise
            .then(() => {
                state.isPlaying = true;
                state.isLoading = false;
                updatePlayerUI();
                renderNowPlaying();
                updateMediaSession(station);
            })
            .catch(error => {
                console.error('Playback failed:', error);
                
                // If direct stream failed, try proxy
                if (!useProxy && !state.usingProxy) {
                    console.log('Direct stream failed, trying proxy...');
                    playStation(station, streamIndex, true);
                    return;
                }
                
                // Try next stream if available
                if (streamIndex < (station.streams?.length - 1)) {
                    console.log(`Stream ${streamIndex} failed, trying next...`);
                    playStation(station, streamIndex + 1, false);
                    return;
                }
                
                // All options exhausted
                state.isPlaying = false;
                state.isLoading = false;
                updatePlayerUI();
                
                // Check error type
                if (error.name === 'NotAllowedError') {
                    alert('Playback blocked. Please tap the play button to start.');
                } else if (error.name === 'NotSupportedError') {
                    alert(`Stream format not supported. ${station.name} may require a different player.`);
                } else if (error.name === 'NetworkError' || error.message?.includes('Network')) {
                    alert(`Network error. ${station.name} stream may be temporarily unavailable.`);
                } else {
                    alert(`Failed to play ${station.name}. Stream may be unavailable.`);
                }
            });
    }
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
        elements.audioPlayer.play();
        state.isPlaying = true;
    }

    updatePlayerUI();
    renderNowPlaying();
}

function updatePlayerUI() {
    if (!state.currentStation) {
        elements.playerBar.classList.add('hidden');
        return;
    }

    elements.playerBar.classList.remove('hidden');
    elements.playerStation.textContent = state.currentStation.name;
    elements.playerShow.textContent = state.currentStation.callsign;
    
    // Update play button based on state
    if (state.isLoading) {
        elements.playPauseBtn.textContent = '⏳';
        elements.playPauseBtn.disabled = true;
    } else if (state.isPlaying) {
        elements.playPauseBtn.textContent = '⏸️';
        elements.playPauseBtn.disabled = false;
    } else {
        elements.playPauseBtn.textContent = '▶️';
        elements.playPauseBtn.disabled = false;
    }
    
    // Show stream quality info + proxy indicator
    const streamInfo = document.getElementById('player-stream-info');
    if (streamInfo && state.currentStation.streams) {
        const currentStream = state.currentStation.streams[state.currentStreamIndex];
        let infoText = '';
        
        if (currentStream) {
            const quality = currentStream.quality === 'high' ? 'High Quality' : 
                           currentStream.quality === 'low' ? 'Low Bandwidth' : 
                           currentStream.quality;
            const format = currentStream.format.toUpperCase();
            infoText = `${quality} • ${format}`;
        }
        
        // Add proxy indicator
        if (state.usingProxy) {
            infoText += ' • 🔒 Proxied';
        }
        
        streamInfo.textContent = infoText;
    }
}

// Media Session API for lock screen controls
function updateMediaSession(station) {
    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: station.name,
            artist: station.callsign,
            album: 'Radio Agnostic',
            artwork: [
                { src: '/icon-192.png', sizes: '192x192', type: 'image/png' }
            ]
        });

        navigator.mediaSession.setActionHandler('play', () => {
            elements.audioPlayer.play();
            state.isPlaying = true;
            updatePlayerUI();
        });

        navigator.mediaSession.setActionHandler('pause', () => {
            elements.audioPlayer.pause();
            state.isPlaying = false;
            updatePlayerUI();
        });

        navigator.mediaSession.setActionHandler('stop', () => {
            elements.audioPlayer.pause();
            elements.audioPlayer.currentTime = 0;
            state.isPlaying = false;
            updatePlayerUI();
        });
    }
}

// Schedule Functions
function createSchedule(name) {
    const schedule = {
        id: Date.now().toString(),
        name: name,
        slots: [],
        created_at: new Date().toISOString()
    };
    
    state.schedules.push(schedule);
    saveSchedules();
    renderSchedules();
}

function saveSchedules() {
    localStorage.setItem('radio_agnostic_schedules', JSON.stringify(state.schedules));
}

// Modal Functions
function openModal() {
    elements.scheduleModal.classList.remove('hidden');
}

function closeModal() {
    elements.scheduleModal.classList.add('hidden');
    elements.scheduleForm.reset();
}

// Helper Functions
function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// Event Listeners
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        state.activeTab = tabName;
        
        // Update tab UI
        elements.tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update content
        elements.tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

elements.playPauseBtn.addEventListener('click', () => {
    if (state.currentStation) {
        togglePlay(state.currentStation);
    }
});

// Add current station to schedule
document.getElementById('add-current-to-schedule')?.addEventListener('click', () => {
    if (state.currentStation && typeof openAddToScheduleModal === 'function') {
        openAddToScheduleModal(state.currentStation.id, '');
    }
});

elements.volumeSlider.addEventListener('input', (e) => {
    elements.audioPlayer.volume = e.target.value / 100;
});

elements.createScheduleBtn.addEventListener('click', openModal);

elements.closeModalBtns.forEach(btn => {
    btn.addEventListener('click', closeModal);
});

elements.scheduleForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('schedule-name').value.trim();
    if (name) {
        createSchedule(name);
        closeModal();
    }
});

elements.searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    // Filter now playing feed
    const cards = elements.nowPlayingFeed.querySelectorAll('.station-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? '' : 'none';
    });
});

// Audio event listeners
elements.audioPlayer.addEventListener('loadstart', () => {
    state.isLoading = true;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener('canplay', () => {
    state.isLoading = false;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener('playing', () => {
    state.isPlaying = true;
    state.isLoading = false;
    updatePlayerUI();
    
    // Update "now playing" to show this station is active
    renderNowPlaying();
});

elements.audioPlayer.addEventListener('pause', () => {
    state.isPlaying = false;
    updatePlayerUI();
    renderNowPlaying();
});

elements.audioPlayer.addEventListener('waiting', () => {
    state.isLoading = true;
    updatePlayerUI();
});

elements.audioPlayer.addEventListener('error', (e) => {
    console.error('Audio error:', e);
    console.error('Error code:', elements.audioPlayer.error?.code);
    console.error('Error message:', elements.audioPlayer.error?.message);
    
    const errorCode = elements.audioPlayer.error?.code;
    const station = state.currentStation;
    
    // If not already using proxy, try proxy
    if (station && !state.usingProxy) {
        console.log('Direct stream error, trying proxy...');
        playStation(station, state.currentStreamIndex, true);
        return;
    }
    
    // Try fallback stream first
    if (station && state.currentStreamIndex < (station.streams?.length - 1)) {
        console.log(`Stream ${state.currentStreamIndex} error, trying fallback...`);
        playStation(station, state.currentStreamIndex + 1, false);
        return;
    }
    
    state.isPlaying = false;
    state.isLoading = false;
    updatePlayerUI();
    
    let errorMsg = 'Failed to play station.';
    
    switch(errorCode) {
        case 1: // MEDIA_ERR_ABORTED
            errorMsg = 'Playback aborted. The stream may have been interrupted.';
            break;
        case 2: // MEDIA_ERR_NETWORK
            errorMsg = 'Network error. Check your connection and try again.';
            // Auto-retry once for network errors
            if (station) {
                console.log('Network error, retrying in 3 seconds...');
                setTimeout(() => {
                    if (state.currentStation?.id === station.id) {
                        playStation(station, 0, state.usingProxy);
                    }
                }, 3000);
                return;
            }
            break;
        case 3: // MEDIA_ERR_DECODE
            errorMsg = 'Audio decoding error. The stream format may be unsupported.';
            break;
        case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            errorMsg = 'Stream format not supported by your browser.';
            break;
    }
    
    alert(`${errorMsg} (${station?.name || 'Unknown station'})`);
});

elements.audioPlayer.addEventListener('stalled', () => {
    console.warn('Audio stalled - buffering issue');
    state.isLoading = true;
    updatePlayerUI();
});

// Initialization
async function init() {
    // Load initial data
    const [stations, genres] = await Promise.all([
        fetchStations(),
        fetchGenres()
    ]);
    
    state.stations = stations;
    state.genres = genres;
    
    // Render initial UI
    renderGenreFilters();
    renderStationsGrid();
    renderSchedules();
    
    // Load now playing
    await loadNowPlaying();
    
    // Set up polling for now playing updates
    setInterval(loadNowPlaying, 60000); // Update every minute
}

async function loadNowPlaying() {
    const nowPlaying = await fetchNowPlaying(state.activeGenre);
    state.nowPlaying = nowPlaying;
    renderNowPlaying();
}

// Start the app
document.addEventListener('DOMContentLoaded', init);

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(console.error);
}
