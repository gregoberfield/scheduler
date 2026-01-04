// Availability Editor - Personal availability management
(function() {
    let currentSlots = {};  // Map of slot_index to state
    let selectionMode = 2;  // Default to Available (2)
    let isSelecting = false;
    let startSlotIndex = null;
    let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Convert date and time to slot index (Unix timestamp / 1800)
    function dateTimeToSlotIndex(date, hour, minute) {
        const dt = new Date(date);
        dt.setHours(hour, minute, 0, 0);
        return Math.floor(dt.getTime() / 1000 / 1800);
    }
    
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
    
    // Build the availability grid
    function buildAvailabilityGrid(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        let html = '<div class="availability-grid">';
        html += '<table class="table table-bordered table-sm availability-table">';
        html += '<thead class="sticky-top bg-white">';
        html += '<tr><th class="time-header">Time</th>';
        
        // Day headers
        const days = [];
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const dayStr = d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
            days.push(new Date(d));
            html += `<th class="day-header">${dayStr}</th>`;
        }
        html += '</tr>';
        html += '</thead>';
        html += '<tbody>';
        
        // Time rows (24 hours x 2 = 48 half-hour slots per day)
        for (let hour = 0; hour < 24; hour++) {
            for (let minute = 0; minute < 60; minute += 30) {
                html += '<tr>';
                html += `<td class="time-label">${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}</td>`;
                
                // Cells for each day
                days.forEach((day, dayIndex) => {
                    const slotIndex = dateTimeToSlotIndex(day, hour, minute);
                    const state = currentSlots[slotIndex] || 0;
                    const stateClass = state === 2 ? 'state-available' : state === 1 ? 'state-maybe' : 'state-unavailable';
                    const dayClass = dayIndex === 0 ? 'first-day' : '';
                    html += `<td class="slot-cell ${stateClass} ${dayClass}" data-slot="${slotIndex}"></td>`;
                });
                
                html += '</tr>';
            }
        }
        
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
        
        return html;
    }
    
    // Load availability from server
    function loadAvailability() {
        const startDate = $('#start_date').val();
        const endDate = $('#end_date').val();
        
        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }
        
        const startSlot = dateTimeToSlotIndex(startDate, 0, 0);
        const endSlot = dateTimeToSlotIndex(endDate, 23, 30);
        
        $.ajax({
            url: '/api/availability',
            method: 'GET',
            data: {
                start_slot: startSlot,
                end_slot: endSlot,
                user_id: 'current'  // Will be handled by server
            },
            success: function(response) {
                // Reset current slots
                currentSlots = {};
                
                // Populate from response
                response.slots.forEach(slot => {
                    currentSlots[slot.slot_index] = slot.state;
                });
                
                // Build and render grid
                const gridHtml = buildAvailabilityGrid(startDate, endDate);
                $('#availability_grid').html(gridHtml);
                
                // Attach event handlers
                attachGridHandlers();
            },
            error: function(xhr) {
                alert('Error loading availability: ' + (xhr.responseJSON?.error || 'Unknown error'));
            }
        });
    }
    
    // Attach mouse event handlers to grid cells
    function attachGridHandlers() {
        // Remove any existing handlers first
        $('.slot-cell').off('mousedown mouseenter mouseup');
        $(document).off('mouseup.availability');
        
        $('.slot-cell')
            .on('mousedown', function(e) {
                e.preventDefault();
                isSelecting = true;
                startSlotIndex = $(this).data('slot');
                updateCell($(this), selectionMode);
            })
            .on('mouseenter', function(e) {
                if (isSelecting) {
                    updateCell($(this), selectionMode);
                }
            })
            .on('mouseup', function(e) {
                isSelecting = false;
            });
        
        $(document).on('mouseup.availability', function() {
            isSelecting = false;
        });
    }
    
    // Update a cell's state
    function updateCell($cell, state) {
        const slotIndex = $cell.data('slot');
        currentSlots[slotIndex] = state;
        
        // Update visual
        $cell.removeClass('state-available state-maybe state-unavailable');
        if (state === 2) {
            $cell.addClass('state-available');
        } else if (state === 1) {
            $cell.addClass('state-maybe');
        } else {
            $cell.addClass('state-unavailable');
        }
    }
    
    // Save availability to server
    function saveAvailability() {
        // Build slots array
        const slots = [];
        for (const slotIndex in currentSlots) {
            slots.push({
                slot_index: parseInt(slotIndex),
                state: currentSlots[slotIndex]
            });
        }
        
        if (slots.length === 0) {
            alert('No changes to save');
            return;
        }
        
        $.ajax({
            url: '/api/availability/bulk',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ slots }),
            success: function(response) {
                alert('Availability saved successfully!');
            },
            error: function(xhr) {
                alert('Error saving availability: ' + (xhr.responseJSON?.error || 'Unknown error'));
            }
        });
    }
    
    // Clear all selections
    function clearAll() {
        if (confirm('Are you sure you want to clear all availability in this date range?')) {
            $('.slot-cell').each(function() {
                updateCell($(this), 0);
            });
        }
    }
    
    // Event listeners
    $(document).ready(function() {
        // Load button
        $('#load_availability').click(loadAvailability);
        
        // Save button
        $('#save_availability').click(saveAvailability);
        
        // Selection mode buttons
        $('#select_mode_available').click(function() {
            selectionMode = 2;
            updateModeDisplay('Available');
        });
        
        $('#select_mode_maybe').click(function() {
            selectionMode = 1;
            updateModeDisplay('Maybe');
        });
        
        $('#select_mode_unavailable').click(function() {
            selectionMode = 0;
            updateModeDisplay('Unavailable');
        });
        
        // Clear all button
        $('#clear_all').click(clearAll);
        
        function updateModeDisplay(mode) {
            $('#current_mode_text').text(mode);
        }
    });
})();
