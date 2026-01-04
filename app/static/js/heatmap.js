// Heatmap Viewer - Aggregated availability heatmap
(function() {
    let aggregateData = [];
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
    
    // Get intensity class based on count
    function getIntensityClass(count, maxCount) {
        if (count === 0) return 'intensity-0';
        const ratio = count / maxCount;
        if (ratio < 0.2) return 'intensity-1';
        if (ratio < 0.4) return 'intensity-2';
        if (ratio < 0.6) return 'intensity-3';
        if (ratio < 0.8) return 'intensity-4';
        return 'intensity-5';
    }
    
    // Build heatmap grid
    function buildHeatmapGrid(startDate, endDate, aggregates) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        // Find max count for intensity scaling
        const maxCount = Math.max(...aggregates.map(a => a.available_count), 1);
        
        // Create aggregate map
        const aggMap = {};
        aggregates.forEach(agg => {
            aggMap[agg.slot_index] = agg.available_count;
        });
        
        let html = '<div class="heatmap-grid-wrapper">';
        html += '<table class="table table-bordered table-sm heatmap-table">';
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
                days.forEach(day => {
                    const slotIndex = dateTimeToSlotIndex(day, hour, minute);
                    const count = aggMap[slotIndex] || 0;
                    const intensityClass = getIntensityClass(count, maxCount);
                    html += `<td class="heatmap-cell ${intensityClass}" data-slot="${slotIndex}" data-count="${count}" title="${count} available"></td>`;
                });
                
                html += '</tr>';
            }
        }
        
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
        
        return html;
    }
    
    // Load heatmap data
    function loadHeatmap() {
        const startDate = $('#hm_start_date').val();
        const endDate = $('#hm_end_date').val();
        
        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }
        
        const startSlot = dateTimeToSlotIndex(startDate, 0, 0);
        const endSlot = dateTimeToSlotIndex(endDate, 23, 30);
        
        $.ajax({
            url: '/api/availability/aggregate',
            method: 'GET',
            data: {
                start_slot: startSlot,
                end_slot: endSlot
            },
            success: function(response) {
                aggregateData = response.aggregates;
                
                // Build and render grid
                const gridHtml = buildHeatmapGrid(startDate, endDate, aggregateData);
                $('#heatmap_grid').html(gridHtml);
                
                // Attach click handlers
                attachCellHandlers();
            },
            error: function(xhr) {
                alert('Error loading heatmap: ' + (xhr.responseJSON?.error || 'Unknown error'));
            }
        });
    }
    
    // Attach click handlers to navigate to timeline
    function attachCellHandlers() {
        $('.heatmap-cell').click(function() {
            const slotIndex = $(this).data('slot');
            const count = $(this).data('count');
            
            if (count > 0) {
                // Navigate to timeline with this slot highlighted
                const date = slotIndexToDate(slotIndex);
                const dateStr = date.toISOString().split('T')[0];
                
                // Store slot index in session storage for timeline to highlight
                sessionStorage.setItem('highlight_slot', slotIndex);
                
                window.location.href = `/timeline?date=${dateStr}`;
            }
        });
    }
    
    // Event listeners
    $(document).ready(function() {
        $('#load_heatmap').click(loadHeatmap);
    });
})();
