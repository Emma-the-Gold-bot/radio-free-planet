/**
 * Radio Agnostic Scheduler Module
 * Handles user schedules, show slots, and timeline view
 */

// Schedule Data Structure:
// {
//   id: string,
//   name: string,
//   slots: [
//     {
//       id: string,
//       dayOfWeek: 0-6 (Mon-Sun),
//       time: "HH:MM",
//       stationId: string,
//       showId?: string,
//       showName?: string,
//       recurring: boolean,
//       notes?: string
//     }
//   ],
//   created_at: ISO date
// }

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const HOURS = Array.from({length: 24}, (_, i) => i);

// Initialize scheduler
document.addEventListener('DOMContentLoaded', () => {
    // Add schedule detail modal to DOM
    addScheduleModals();
});

function addScheduleModals() {
    const modalsContainer = document.createElement('div');
    modalsContainer.id = 'scheduler-modals';
    modalsContainer.innerHTML = `
        <!-- Add to Schedule Modal -->
        <div id="add-to-schedule-modal" class="modal hidden">
            <div class="modal-content">
                <header>
                    <h3>Add to Schedule</h3>
                    <button class="close-btn" onclick="closeAddToScheduleModal()">&times;</button>
                </header>
                <form id="add-to-schedule-form">
                    <div class="form-group">
                        <label>Station</label>
                        <div id="schedule-station-name" class="form-value"></div>
                    </div>
                    <div class="form-group">
                        <label>Show (optional)</label>
                        <input type="text" id="schedule-show-name" placeholder="Show name">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Day</label>
                            <select id="schedule-day" required>
                                ${DAYS.map((d, i) => `<option value="${i}">${d}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Time</label>
                            <input type="time" id="schedule-time" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Save to Schedule</label>
                        <select id="schedule-select" required>
                            <option value="">-- Select Schedule --</option>
                        </select>
                    </div>
                    <div class="form-group checkbox-group">
                        <label>
                            <input type="checkbox" id="schedule-recurring" checked>
                            Weekly recurring
                        </label>
                    </div>
                    <div class="form-group">
                        <label>Notes (optional)</label>
                        <textarea id="schedule-notes" rows="2" placeholder="e.g., New episodes Thursday"></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" onclick="closeAddToScheduleModal()">Cancel</button>
                        <button type="submit" class="btn-primary">Add to Schedule</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Schedule Detail Modal -->
        <div id="schedule-detail-modal" class="modal hidden">
            <div class="modal-content modal-large">
                <header>
                    <h3 id="detail-schedule-name">Schedule Name</h3>
                    <button class="close-btn" onclick="closeScheduleDetailModal()">&times;</button>
                </header>
                <div class="schedule-detail-body">
                    <div class="schedule-timeline" id="schedule-timeline">
                        <!-- Timeline rendered here -->
                    </div>
                    <div class="schedule-actions">
                        <button class="btn-secondary" onclick="deleteCurrentSchedule()">Delete Schedule</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalsContainer);
    
    // Add form handler
    document.getElementById('add-to-schedule-form').addEventListener('submit', handleAddToSchedule);
}

// Open "Add to Schedule" modal
function openAddToScheduleModal(stationId, showName = '') {
    const station = state.stations.find(s => s.id === stationId);
    if (!station) return;
    
    document.getElementById('schedule-station-name').textContent = station.name;
    document.getElementById('schedule-show-name').value = showName;
    
    // Populate schedule dropdown
    const select = document.getElementById('schedule-select');
    select.innerHTML = `
        <option value="">-- Select Schedule --</option>
        ${state.schedules.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
    `;
    
    // Set default time to now
    const now = new Date();
    document.getElementById('schedule-time').value = 
        `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
    
    // Store current selection
    state.tempScheduleSelection = { stationId, showName };
    
    document.getElementById('add-to-schedule-modal').classList.remove('hidden');
}

function closeAddToScheduleModal() {
    document.getElementById('add-to-schedule-modal').classList.add('hidden');
    document.getElementById('add-to-schedule-form').reset();
    state.tempScheduleSelection = null;
}

function handleAddToSchedule(e) {
    e.preventDefault();
    
    const scheduleId = document.getElementById('schedule-select').value;
    if (!scheduleId) {
        alert('Please select a schedule');
        return;
    }
    
    const schedule = state.schedules.find(s => s.id === scheduleId);
    if (!schedule) return;
    
    const slot = {
        id: Date.now().toString(),
        stationId: state.tempScheduleSelection?.stationId,
        showName: document.getElementById('schedule-show-name').value || null,
        dayOfWeek: parseInt(document.getElementById('schedule-day').value),
        time: document.getElementById('schedule-time').value,
        recurring: document.getElementById('schedule-recurring').checked,
        notes: document.getElementById('schedule-notes').value
    };
    
    if (!schedule.slots) schedule.slots = [];
    schedule.slots.push(slot);
    
    // Sort slots by day then time
    schedule.slots.sort((a, b) => {
        if (a.dayOfWeek !== b.dayOfWeek) return a.dayOfWeek - b.dayOfWeek;
        return a.time.localeCompare(b.time);
    });
    
    saveSchedules();
    renderSchedules();
    closeAddToScheduleModal();
    
    // Show confirmation
    showToast(`Added to "${schedule.name}"`);
}

// View schedule detail
let currentViewingSchedule = null;

function openScheduleDetail(scheduleId) {
    const schedule = state.schedules.find(s => s.id === scheduleId);
    if (!schedule) return;
    
    currentViewingSchedule = schedule;
    document.getElementById('detail-schedule-name').textContent = schedule.name;
    renderScheduleTimeline(schedule);
    document.getElementById('schedule-detail-modal').classList.remove('hidden');
}

function closeScheduleDetailModal() {
    document.getElementById('schedule-detail-modal').classList.add('hidden');
    currentViewingSchedule = null;
}

function renderScheduleTimeline(schedule) {
    const container = document.getElementById('schedule-timeline');
    
    if (!schedule.slots || schedule.slots.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No shows scheduled yet.</p>
                <p>Browse stations and add shows to this schedule!</p>
            </div>
        `;
        return;
    }
    
    // Group by day
    const byDay = DAYS.map((day, i) => ({
        day,
        dayIndex: i,
        slots: schedule.slots.filter(s => s.dayOfWeek === i)
    }));
    
    container.innerHTML = `
        <div class="timeline-grid">
            ${byDay.map(({day, slots}) => `
                <div class="timeline-day ${slots.length === 0 ? 'empty' : ''}">
                    <h4 class="day-label">${day}</h4>
                    <div class="day-slots">
                        ${slots.length === 0 
                            ? '<span class="no-slots">—</span>'
                            : slots.map(slot => {
                                const station = state.stations.find(s => s.id === slot.stationId);
                                return `
                                    <div class="slot-card" data-slot-id="${slot.id}">
                                        <div class="slot-time">${formatTime12h(slot.time)}</div>
                                        <div class="slot-station">${station?.name || 'Unknown Station'}</div>
                                        ${slot.showName ? `<div class="slot-show">${slot.showName}</div>` : ''}
                                        ${slot.recurring ? '<span class="recurring-badge">↻ Weekly</span>' : ''}
                                        ${slot.notes ? `<div class="slot-notes">${slot.notes}</div>` : ''}
                                        <button class="slot-delete" onclick="deleteSlot('${schedule.id}', '${slot.id}')" title="Remove">×</button>
                                    </div>
                                `;
                            }).join('')
                        }
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function deleteSlot(scheduleId, slotId) {
    const schedule = state.schedules.find(s => s.id === scheduleId);
    if (!schedule) return;
    
    schedule.slots = schedule.slots.filter(s => s.id !== slotId);
    saveSchedules();
    renderSchedules();
    renderScheduleTimeline(schedule);
    showToast('Removed from schedule');
}

function deleteCurrentSchedule() {
    if (!currentViewingSchedule) return;
    
    if (confirm(`Delete schedule "${currentViewingSchedule.name}"?`)) {
        state.schedules = state.schedules.filter(s => s.id !== currentViewingSchedule.id);
        saveSchedules();
        renderSchedules();
        closeScheduleDetailModal();
        showToast('Schedule deleted');
    }
}

function formatTime12h(time24) {
    const [hours, minutes] = time24.split(':');
    const h = parseInt(hours);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${minutes} ${ampm}`;
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// Update renderSchedules to make schedules clickable
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
        const nextSlot = getNextSlot(schedule);
        
        return `
            <div class="station-card schedule-card" data-schedule-id="${schedule.id}" onclick="openScheduleDetail('${schedule.id}')">
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
                        <div class="show-time">${DAYS[nextSlot.dayOfWeek]} at ${formatTime12h(nextSlot.time)}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function getNextSlot(schedule) {
    if (!schedule.slots || schedule.slots.length === 0) return null;
    
    const now = new Date();
    const currentDay = now.getDay(); // 0 = Sunday, need to adjust
    const currentTime = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
    
    // Find next slot from now
    // This is simplified - proper implementation would calculate actual next occurrence
    const todaySlots = schedule.slots.filter(s => s.dayOfWeek === currentDay && s.time > currentTime);
    if (todaySlots.length) return todaySlots.sort((a,b) => a.time.localeCompare(b.time))[0];
    
    // Look ahead to next days
    for (let i = 1; i <= 7; i++) {
        const checkDay = (currentDay + i) % 7;
        const daySlots = schedule.slots.filter(s => s.dayOfWeek === checkDay);
        if (daySlots.length) return daySlots.sort((a,b) => a.time.localeCompare(b.time))[0];
    }
    
    return schedule.slots[0]; // Fallback
}

// Schedule button handlers are now attached in app.js renderNowPlaying()
// This file provides the modal functions and schedule management
