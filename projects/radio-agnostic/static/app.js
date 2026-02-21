/**
 * Radio Agnostic - Static Version with Schedules
 * Shows "What's On Now" from schedule data
 */

const CONFIG = {
  stationsUrl: './data/stations.json',
  schedulesUrl: './data/schedules.json',
  nowPlayingUrl: './data/now_playing.json',
  // Netlify serverless function for CORS proxy
  // This works with ALL stations (HTTP and HTTPS, CORS blocked or open)
  corsProxy: '/.netlify/functions/proxy?url=',
  autoProxy: true
};

let state = {
  stations: [],
  schedules: {},
  nowPlaying: [],
  genres: [],
  schedules_user: JSON.parse(localStorage.getItem('radio_agnostic_schedules') || '[]'),
  currentStation: null,
  isPlaying: false,
  isLoading: false,
  usingProxy: false,
  activeGenre: null,
  activeTab: 'discover'
};

// Current time info
function getCurrentTimeInfo() {
  const now = new Date();
  return {
    dayOfWeek: now.getDay(), // 0=Sunday, need 0=Monday
    dayName: ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][now.getDay()],
    time: now.toTimeString().slice(0, 5), // HH:MM
    timestamp: now.toISOString()
  };
}

// Convert time string "HH:MM" to minutes for comparison
function timeToMinutes(timeStr) {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

// Check if a show slot is currently playing
function isShowNow(slot, timeInfo) {
  // Handle day wrapping (Sunday = 0, but we need Monday = 0)
  const slotDay = slot.day_of_week;
  const currentDay = timeInfo.dayOfWeek === 0 ? 6 : timeInfo.dayOfWeek - 1; // Convert Sun=0 to Mon=0
  
  if (slotDay !== currentDay) return false;
  
  const nowMinutes = timeToMinutes(timeInfo.time);
  const startMinutes = timeToMinutes(slot.start_time);
  const endMinutes = timeToMinutes(slot.end_time);
  
  // Handle shows that wrap past midnight
  if (endMinutes < startMinutes) {
    return nowMinutes >= startMinutes || nowMinutes < endMinutes;
  }
  
  return nowMinutes >= startMinutes && nowMinutes < endMinutes;
}

// Calculate what's on now from schedules
function calculateNowPlaying() {
  const timeInfo = getCurrentTimeInfo();
  const nowPlaying = [];
  
  for (const [stationId, schedule] of Object.entries(state.schedules)) {
    const station = state.stations.find(s => s.id === stationId);
    if (!station) continue;
    
    const daySchedule = schedule.schedule?.[timeInfo.dayName] || [];
    
    for (const slot of daySchedule) {
      if (isShowNow(slot, timeInfo)) {
        nowPlaying.push({
          station: station,
          show: slot,
          genre: slot.genre,
          timeInfo: timeInfo
        });
        break; // Only first matching show per station
      }
    }
  }
  
  return nowPlaying;
}

// Data loading
async function loadAllData() {
  console.log('Loading station data...');
  console.log('Stations URL:', CONFIG.stationsUrl);
  console.log('Schedules URL:', CONFIG.schedulesUrl);
  
  try {
    // Load stations
    console.log('Fetching stations...');
    const stationsResp = await fetch(CONFIG.stationsUrl);
    console.log('Stations response:', stationsResp.status, stationsResp.ok);
    if (!stationsResp.ok) {
      throw new Error(`Stations fetch failed: ${stationsResp.status}`);
    }
    const stationsData = await stationsResp.json();
    console.log('Stations data:', stationsData);
    state.stations = stationsData.stations || [];
    console.log(`Loaded ${state.stations.length} stations`);
    
    // Load schedules
    console.log('Fetching schedules...');
    const schedulesResp = await fetch(CONFIG.schedulesUrl);
    console.log('Schedules response:', schedulesResp.status, schedulesResp.ok);
    if (!schedulesResp.ok) {
      throw new Error(`Schedules fetch failed: ${schedulesResp.status}`);
    }
    const schedulesData = await schedulesResp.json();
    console.log('Schedules data count:', schedulesData.count);
    
    // Convert array to object keyed by station_id
    state.schedules = {};
    for (const sched of schedulesData.schedules || []) {
      state.schedules[sched.station_id] = sched;
    }
    
    // Calculate now playing
    state.nowPlaying = calculateNowPlaying();
    
    // Extract all unique genres from schedules
    const allGenres = new Set();
    for (const sched of Object.values(state.schedules)) {
      for (const day of Object.values(sched.schedule || {})) {
        for (const slot of day) {
          if (slot.genre) allGenres.add(slot.genre);
        }
      }
    }
    state.genres = Array.from(allGenres).sort();
    
    console.log(`Loaded ${state.stations.length} stations, ${state.nowPlaying.length} now playing, ${state.genres.length} genres`);
    
  } catch (err) {
    console.error('Error loading data:', err);
    
    // Show error in UI
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'background: #ff6b6b; color: white; padding: 15px; margin: 10px; border-radius: 8px; font-family: sans-serif;';
    errorDiv.innerHTML = `<strong>Error loading data:</strong> ${err.message}<br><small>Check browser console (F12) for details.</small>`;
    document.body.insertBefore(errorDiv, document.body.firstChild);
    
    // Fallback to single station
    state.stations = [{
      id: 'kexp', name: 'KEXP 90.3 FM',
      location: {city: 'Seattle', state: 'WA'},
      streams: [{url: 'https://kexp-mp3-128.streamguys1.com/kexp128.mp3', quality: 'high'}],
      genres: ['indie', 'rock'], cors_status: 'open'
    }];
  }
}

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
  playPauseBtn: document.getElementById('play-pause-btn'),
  volumeSlider: document.getElementById('volume-slider'),
  audioPlayer: document.getElementById('audio-player'),
  schedulesList: document.getElementById('schedules-list'),
  createScheduleBtn: document.getElementById('create-schedule-btn'),
  scheduleModal: document.getElementById('schedule-modal'),
  scheduleForm: document.getElementById('schedule-form'),
  closeModalBtns: document.querySelectorAll('.close-modal, .close-btn')
};

// UI Rendering
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

  elements.genreFilters.querySelectorAll('.genre-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      state.activeGenre = pill.dataset.genre || null;
      renderGenreFilters();
      renderNowPlaying();
    });
  });
}

function renderNowPlayingCard(item) {
  const station = item.station;
  const show = item.show;
  const isCurrentStation = state.currentStation?.id === station.id;
  const isPlaying = isCurrentStation && state.isPlaying;
  
  let buttonIcon = '▶️';
  if (isCurrentStation && state.isLoading) buttonIcon = '⏳';
  else if (isPlaying) buttonIcon = '⏸️';
  
  const corsWarning = station.cors_status === 'blocked' 
    ? '<span class="cors-badge" title="Uses proxy">🔒</span>' 
    : '';
  
  // Calculate time remaining
  const timeInfo = getCurrentTimeInfo();
  const showEndMinutes = timeToMinutes(show.end_time);
  const nowMinutes = timeToMinutes(timeInfo.time);
  let minutesLeft = showEndMinutes - nowMinutes;
  if (minutesLeft < 0) minutesLeft += 24 * 60; // Wrapped past midnight
  const timeLeft = `${Math.floor(minutesLeft / 60)}h ${minutesLeft % 60}m left`;
  
  return `
    <div class="station-card now-playing-card ${isPlaying ? 'playing' : ''}" data-station-id="${station.id}">
      <div class="station-header">
        <div class="station-logo">📻</div>
        <div class="station-info">
          <h3>${station.name} ${corsWarning}</h3>
          <div class="location">${station.location.city}, ${station.location.state}</div>
        </div>
        <button class="play-btn" data-station-id="${station.id}">
          ${buttonIcon}
        </button>
      </div>
      <div class="show-info now-playing-info">
        <div class="show-title">${show.title}</div>
        <div class="show-host">with ${show.host}</div>
        <div class="show-time">${show.start_time} - ${show.end_time} • ${timeLeft}</div>
        <div class="show-genres">
          <span class="genre-tag active">${show.genre}</span>
        </div>
        ${show.description ? `<div class="show-description">${show.description.slice(0, 100)}${show.description.length > 100 ? '...' : ''}</div>` : ''}
      </div>
    </div>
  `;
}

function renderNowPlaying() {
  let filtered = state.nowPlaying;
  
  // Filter by genre
  if (state.activeGenre) {
    filtered = filtered.filter(item => item.show.genre === state.activeGenre);
  }
  
  // Filter by search
  const query = elements.searchInput?.value?.toLowerCase() || '';
  if (query) {
    filtered = filtered.filter(item => 
      item.station.name.toLowerCase().includes(query) ||
      item.show.title.toLowerCase().includes(query) ||
      item.show.host.toLowerCase().includes(query) ||
      item.show.genre.toLowerCase().includes(query)
    );
  }
  
  if (filtered.length === 0) {
    elements.nowPlayingFeed.innerHTML = `
      <div class="empty-state">
        <p>No stations currently playing${state.activeGenre ? ` ${state.activeGenre}` : ''}.</p>
        <p class="subtext">Try selecting a different genre or check back later.</p>
      </div>
    `;
    return;
  }

  elements.nowPlayingFeed.innerHTML = filtered.map(item => renderNowPlayingCard(item)).join('');

  // Add click handlers
  elements.nowPlayingFeed.querySelectorAll('.station-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (!e.target.closest('.play-btn')) {
        const stationId = card.dataset.stationId;
        const item = state.nowPlaying.find(i => i.station.id === stationId);
        if (item) playStation(item.station);
      }
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
}

function renderStationsGrid() {
  let filtered = state.stations;
  
  if (state.activeGenre) {
    filtered = filtered.filter(s => s.genres?.includes(state.activeGenre));
  }
  
  const query = elements.searchInput?.value?.toLowerCase() || '';
  if (query) {
    filtered = filtered.filter(s => 
      s.name.toLowerCase().includes(query) ||
      s.location.city.toLowerCase().includes(query)
    );
  }
  
  if (filtered.length === 0) {
    elements.stationsGrid.innerHTML = `
      <div class="empty-state">
        <p>No stations found.</p>
      </div>
    `;
    return;
  }

  elements.stationsGrid.innerHTML = filtered.map(station => `
    <div class="station-card" data-station-id="${station.id}">
      <div class="station-header">
        <div class="station-logo">📻</div>
        <div class="station-info">
          <h3>${station.name}</h3>
          <div class="location">${station.location.city}, ${station.location.state}</div>
        </div>
        <button class="play-btn" data-station-id="${station.id}">▶️</button>
      </div>
      <div class="show-genres">
        ${station.genres.map(g => `<span class="genre-tag">${g}</span>`).join('')}
      </div>
    </div>
  `).join('');

  elements.stationsGrid.querySelectorAll('.play-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const stationId = btn.dataset.stationId;
      const station = state.stations.find(s => s.id === stationId);
      if (station) togglePlay(station);
    });
  });
}

// Player Functions
function getStreamUrl(station, useProxy = false) {
  const stream = station.streams?.find(s => s.is_primary) || station.streams?.[0];
  if (!stream) return null;
  
  // Use Netlify proxy for all streams (handles CORS + HTTP/HTTPS)
  if (useProxy || CONFIG.autoProxy) {
    return CONFIG.corsProxy + encodeURIComponent(stream.url);
  }
  
  return stream.url;
}

function playStation(station, useProxy = true) {
  if (state.currentStation?.id === station.id && !useProxy) {
    togglePlay(station);
    return;
  }

  state.currentStation = station;
  state.isLoading = true;
  state.usingProxy = useProxy;
  updatePlayerUI();
  
  const streamUrl = getStreamUrl(station, useProxy);
  if (!streamUrl) {
    alert('No stream available for ' + station.name);
    state.isLoading = false;
    return;
  }

  elements.audioPlayer.src = streamUrl;
  elements.audioPlayer.volume = elements.volumeSlider?.value / 100 || 0.8;
  
  elements.audioPlayer.play()
    .then(() => {
      state.isPlaying = true;
      state.isLoading = false;
      updatePlayerUI();
      renderNowPlaying();
    })
    .catch(error => {
      console.error('Play error:', error);
      
      // If proxy fails, try direct (for CORS-open stations)
      if (useProxy && station.cors_status === 'open') {
        console.log('Proxy failed, trying direct...');
        playStation(station, false);
        return;
      }
      
      state.isPlaying = false;
      state.isLoading = false;
      updatePlayerUI();
      alert(`Failed to play ${station.name}. The stream may be temporarily unavailable.`);
    });
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
    elements.playerBar?.classList.add('hidden');
    return;
  }

  elements.playerBar?.classList.remove('hidden');
  if (elements.playerStation) elements.playerStation.textContent = state.currentStation.name;
  
  // Find current show
  const item = state.nowPlaying.find(i => i.station.id === state.currentStation.id);
  if (item && elements.playerShow) {
    elements.playerShow.textContent = `${item.show.title} with ${item.show.host}`;
  } else if (elements.playerShow) {
    elements.playerShow.textContent = state.currentStation.callsign || '';
  }
  
  if (elements.playPauseBtn) {
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
  }
}

// Schedule Functions
function renderSchedules() {
  if (!elements.schedulesList) return;
  
  if (state.schedules_user.length === 0) {
    elements.schedulesList.innerHTML = `
      <div class="empty-state">
        <p>No schedules yet. Create one to build custom listening lists.</p>
      </div>
    `;
    return;
  }
  
  elements.schedulesList.innerHTML = state.schedules_user.map(schedule => {
    const count = schedule.slots?.length || 0;
    return `
      <div class="station-card schedule-card" data-schedule-id="${schedule.id}">
        <div class="station-header">
          <div class="station-logo">📅</div>
          <div class="station-info">
            <h3>${schedule.name}</h3>
            <div class="location">${count} show${count !== 1 ? 's' : ''}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function saveSchedules() {
  localStorage.setItem('radio_agnostic_schedules', JSON.stringify(state.schedules_user));
}

function openModal() {
  elements.scheduleModal?.classList.remove('hidden');
}

function closeModal() {
  elements.scheduleModal?.classList.add('hidden');
  elements.scheduleForm?.reset();
}

// Event Listeners
function setupEventListeners() {
  elements.tabs?.forEach(tab => {
    tab.addEventListener('click', () => {
      state.activeTab = tab.dataset.tab;
      elements.tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      elements.tabContents.forEach(c => c.classList.remove('active'));
      document.getElementById(`${tab.dataset.tab}-tab`)?.classList.add('active');
    });
  });

  elements.playPauseBtn?.addEventListener('click', () => {
    if (state.currentStation) togglePlay(state.currentStation);
  });

  elements.volumeSlider?.addEventListener('input', (e) => {
    elements.audioPlayer.volume = e.target.value / 100;
  });

  elements.createScheduleBtn?.addEventListener('click', openModal);
  elements.closeModalBtns?.forEach(btn => btn.addEventListener('click', closeModal));

  elements.scheduleForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('schedule-name')?.value.trim();
    if (name) {
      state.schedules_user.push({
        id: Date.now().toString(),
        name: name,
        slots: [],
        created_at: new Date().toISOString()
      });
      saveSchedules();
      renderSchedules();
      closeModal();
    }
  });

  elements.searchInput?.addEventListener('input', () => {
    if (state.activeTab === 'discover') {
      renderNowPlaying();
    } else {
      renderStationsGrid();
    }
  });

  elements.audioPlayer?.addEventListener('error', () => {
    console.error('Audio error');
    state.isPlaying = false;
    state.isLoading = false;
    updatePlayerUI();
  });
}

// Initialize
async function init() {
  console.log('Radio Agnostic loading...');
  
  await loadAllData();
  renderGenreFilters();
  renderNowPlaying();
  renderStationsGrid();
  renderSchedules();
  setupEventListeners();
  
  // Refresh "now playing" every minute
  setInterval(() => {
    state.nowPlaying = calculateNowPlaying();
    if (state.activeTab === 'discover') {
      renderNowPlaying();
    }
    updatePlayerUI();
  }, 60000);
  
  console.log(`Loaded ${state.stations.length} stations, ${state.nowPlaying.length} currently playing`);
}

document.addEventListener('DOMContentLoaded', init);
