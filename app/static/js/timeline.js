// Timeline Viewer - Guild availability timeline
(function() {
    let usersData = [];
    let slotsData = {};  // Map of user_id to slot data
    let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Convert slot index to readable time
    function slotIndexToTime(slotIndex) {
        const timestamp = slotIndex * 1800 * 1000;
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Convert slot index to date
    function slotIndexToDate(slotIndex) {
        const timestamp = slotIndex * 1800 * 1000;
        return new Date(timestamp);
    }
    
    // Convert date and time to slot index
    function dateTimeToSlotIndex(date, hour, minute) {
        const dt = new Date(date);
        dt.setHours(hour, minute, 0, 0);
        return Math.floor(dt.getTime() / 1000 / 1800);
    }
    
    // Build the timeline grid
    function buildTimelineGrid(startDate, endDate, users, slots) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        // Sort users based on selected sort option
        const sortBy = $('#sort_by').val();
        users = sortUsers(users, slots, sortBy);
        
        let html = '<div class="timeline-grid-wrapper">';
        html += '<table class="table table-bordered table-sm timeline-table">';
        html += '<thead class="sticky-top bg-white">';
        html += '<tr><th class="character-header">Character</th>';
        
        // Day headers
        const days = [];
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const dayStr = d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
            days.push(new Date(d));
            html += `<th colspan="48" class="day-header">${dayStr}</th>`;
        }
        html += '</tr>';
        
        // Time sub-headers (optional - could add these later if needed)
        html += '</thead>';
        html += '<tbody>';
        
        // Check if there's any data
        if (users.length === 0) {
            html += '<tr><td colspan="999" class="text-center py-5">';
            html += '<p class="text-muted">No availability data</p>';
            html += '</td></tr>';
        } else {
            // Row for each user
            users.forEach(user => {
                const userSlots = slots[user.id] || {};
                
                html += '<tr>';
                // Character info cell
                html += '<td class="character-cell">';
                html += `<img src="/static/img/classes/${user.wow_class.toLowerCase()}_small.gif" class="class-icon-small" alt="${user.wow_class}">`;
                html += `<span class="character-name">${user.character_name}</span>`;
                if (user.roles && user.roles.length > 0) {
                    user.roles.forEach(role => {
                        const badgeClass = role === 'tank' ? 'primary' : role === 'healer' ? 'success' : 'danger';
                        html += ` <span class="badge bg-${badgeClass}">${role}</span>`;
                    });
                }
                html += '</td>';
                
                // Time slots - iterate through days, then through time slots for each day
                days.forEach((day, dayIndex) => {
                    for (let hour = 0; hour < 24; hour++) {
                        for (let minute = 0; minute < 60; minute += 30) {
                            const slotIndex = dateTimeToSlotIndex(day, hour, minute);
                            const state = userSlots[slotIndex] || 0;
                            const stateClass = state === 2 ? 'state-available' : state === 1 ? 'state-maybe' : 'state-unavailable';
                            
                            // Only show tooltip for Available and Maybe states
                            let titleAttr = '';
                            if (state !== 0) {
                                const tooltipDate = new Date(day);
                                tooltipDate.setHours(hour, minute, 0, 0);
                                const dateStr = tooltipDate.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
                                const timeStr = String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
                                const stateStr = state === 2 ? 'Available' : 'Maybe';
                                titleAttr = ` title="${user.character_name} - ${dateStr} ${timeStr} - ${stateStr}"`;
                            }
                            
                            html += `<td class="timeline-cell ${stateClass}" data-slot="${slotIndex}" data-user-id="${user.id}"${titleAttr}></td>`;
                        }
                    }
                });
                
                html += '</tr>';
            });
        }
        
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
        
        return html;
    }
    
    // Build mobile accordion view
    function buildMobileView(startDate, endDate, users, slots) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        let html = '<div class="accordion" id="mobileTimeline">';
        
        if (users.length === 0) {
            html += '<div class="text-center py-5">';
            html += '<p class="text-muted">No availability data</p>';
            html += '</div>';
        } else {
            users.forEach((user, index) => {
                const userSlots = slots[user.id] || {};
                
                html += `<div class="accordion-item">`;
                html += `<h2 class="accordion-header" id="heading${index}">`;
                html += `<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}">`;
                html += `<img src="/static/img/classes/${user.wow_class.toLowerCase()}_small.gif" class="class-icon-small me-2" alt="${user.wow_class}">`;
                html += `${user.character_name}`;
                html += `</button>`;
                html += `</h2>`;
                html += `<div id="collapse${index}" class="accordion-collapse collapse" data-bs-parent="#mobileTimeline">`;
                html += `<div class="accordion-body">`;
                
                // Simplified timeline for mobile
                html += '<div class="mobile-slots">';
                const days = [];
                for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
                    days.push(new Date(d));
                }
                
                days.forEach(day => {
                    html += `<div class="day-section">`;
                    html += `<h6>${day.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}</h6>`;
                    html += '<div class="slots-row">';
                    
                    for (let hour = 0; hour < 24; hour++) {
                        for (let minute = 0; minute < 60; minute += 30) {
                            const slotIndex = dateTimeToSlotIndex(day, hour, minute);
                            const state = userSlots[slotIndex] || 0;
                            const stateClass = state === 2 ? 'state-available' : state === 1 ? 'state-maybe' : 'state-unavailable';
                            html += `<span class="mobile-slot ${stateClass}" title="${slotIndexToTime(slotIndex)}"></span>`;
                        }
                    }
                    
                    html += '</div></div>';
                });
                html += '</div>';
                
                html += `</div></div></div>`;
            });
        }
        
        html += '</div>';
        
        return html;
    }
    
    // Sort users based on criteria
    function sortUsers(users, slots, sortBy) {
        if (sortBy === 'alphabetical') {
            return users.sort((a, b) => a.character_name.localeCompare(b.character_name));
        } else if (sortBy === 'class') {
            return users.sort((a, b) => a.wow_class.localeCompare(b.wow_class));
        } else if (sortBy === 'most_available') {
            return users.sort((a, b) => {
                const aCount = Object.values(slots[a.id] || {}).filter(s => s === 2).length;
                const bCount = Object.values(slots[b.id] || {}).filter(s => s === 2).length;
                return bCount - aCount;
            });
        }
        return users;
    }
    
    // Load timeline data
    function loadTimeline() {
        const startDate = $('#tl_start_date').val();
        const endDate = $('#tl_end_date').val();
        const classFilter = $('#class_filter').val();
        const roleFilter = $('#role_filter').val();
        const confidenceFilter = $('#confidence_filter').val();
        
        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }
        
        const startSlot = dateTimeToSlotIndex(startDate, 0, 0);
        const endSlot = dateTimeToSlotIndex(endDate, 23, 30);
        
        const params = {
            start_slot: startSlot,
            end_slot: endSlot,
            confidence: confidenceFilter
        };
        
        if (classFilter) params.class = classFilter;
        if (roleFilter) params.role = roleFilter;
        
        $.ajax({
            url: '/api/availability',
            method: 'GET',
            data: params,
            success: function(response) {
                usersData = response.users;
                
                // Organize slots by user
                slotsData = {};
                response.slots.forEach(slot => {
                    if (!slotsData[slot.user_id]) {
                        slotsData[slot.user_id] = {};
                    }
                    slotsData[slot.user_id][slot.slot_index] = slot.state;
                });
                
                // Build and render grids
                const gridHtml = buildTimelineGrid(startDate, endDate, usersData, slotsData);
                $('#timeline_grid').html(gridHtml);
                
                const mobileHtml = buildMobileView(startDate, endDate, usersData, slotsData);
                $('#timeline_mobile').html(mobileHtml);
                
                // Attach tooltips
                attachTooltips();
            },
            error: function(xhr) {
                alert('Error loading timeline: ' + (xhr.responseJSON?.error || 'Unknown error'));
            }
        });
    }
    
    // Attach tooltips to show who's available
    function attachTooltips() {
        // Tooltips are already set in the HTML title attribute during grid building
        // No need to override them here
    }
    
    // Event listeners
    $(document).ready(function() {
        // Load button
        $('#load_timeline').click(loadTimeline);
        
        // Sort change
        $('#sort_by').change(function() {
            if (usersData.length > 0) {
                const startDate = $('#tl_start_date').val();
                const endDate = $('#tl_end_date').val();
                const gridHtml = buildTimelineGrid(startDate, endDate, usersData, slotsData);
                $('#timeline_grid').html(gridHtml);
                attachTooltips();
            }
        });
    });
})();
