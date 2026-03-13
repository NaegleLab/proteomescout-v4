// Filter tab functionality
// This function is now global and will be called when manualKinaseEdit changes
window.handleKinaseEditChange = function() {
    const editMode = document.getElementById('manualKinaseEdit').value;
    const container = document.getElementById('kinaseSelectionContainer');
    const label = document.getElementById('kinaseSelectLabel');
    
    if (editMode === 'none') {
        container.style.display = 'none';
        if (window.plotActive) window.updatePlotDynamically();
    } else {
        container.style.display = 'block';
        label.textContent = (editMode === 'select') ? 'Select kinases to include:' : 'Select kinases to remove:';
        window.updateKinaseSelect();
        // Add immediate update when switching to a selection mode
        if (window.plotActive && $('#kinaseSelect').val()) {
            window.updatePlotDynamically();
        }
    }
}

// Custom label handlers
document.addEventListener('DOMContentLoaded', function() {
    // Setup kinase select change listener
    $('#kinaseSelect').on('change', function() {
        if (window.plotActive) {
            window.updatePlotDynamically();
        }
    });

    // Setup sample select change listener
    $('#sampleSelect').on('change', function() {
        if (window.plotActive) {
            window.updatePlotDynamically();
        }
        // Update custom labels if they're visible
        if (document.getElementById('changeXLabel').checked) {
            populateCustomLabelsInputs();
        }
    });

    // Existing event listeners
    document.getElementById('changeXLabel').addEventListener('change', function() {
        const container = document.getElementById('customLabelsContainer');
        if (this.checked) {
            container.style.display = 'block';
            populateCustomLabelsInputs();
        } else {
            container.style.display = 'none';
            if (window.plotActive) window.updatePlotDynamically();
        }
    });
    
    // Add event listener to the Change Labels button if it exists
    const changeLabelButton = document.getElementById('changeLabelButton');
    if (changeLabelButton) {
        changeLabelButton.addEventListener('click', function() {
            if (window.plotActive) window.updatePlotDynamically();
        });
    }

    // Add listener for restrictKinases checkbox
    const restrictKinasesCheckbox = document.getElementById('restrictKinases');
    if (restrictKinasesCheckbox) {
        restrictKinasesCheckbox.addEventListener('change', function() {
            if (window.plotActive) {
                window.submitForm(); 
            }
        });
    }

    // Add listeners for significantActivity radio buttons
    document.querySelectorAll('input[name="significantActivity"]').forEach(radio => {
        radio.addEventListener('change', function() {
            if (window.plotActive) {
                window.submitForm(); 
            }
        });
    });

    // Add listener for thresholdValue if it exists
    const thresholdInput = document.getElementById('thresholdValue');
    if (thresholdInput) {
         thresholdInput.addEventListener('change', function() { // Or 'input' with debounce
             if (window.plotActive) {
                 window.submitForm(); // or window.updatePlotDynamically();
             }
         });
    }
});

function populateCustomLabelsInputs() {
    const container = document.getElementById('customLabelsInputs');
    if (!container) return;
    container.innerHTML = '';
    const selectedSamples = $('#sampleSelect').val() || [];
    const samplesToUse = selectedSamples.length > 0 ? selectedSamples : window.availableSamples;
    
    if (!Array.isArray(samplesToUse) || samplesToUse.length === 0) {
        container.innerHTML = '<div class="alert alert-warning">No samples available</div>';
        return;
    }
    
    samplesToUse.forEach(sample => {
        const div = document.createElement('div');
        div.className = 'col-md-6 mb-2';
        div.innerHTML = `
            <div class="input-group">
                <span class="input-group-text text-truncate" style="max-width: 180px;">${sample}</span>
                <input type="text" class="form-control custom-label-input flex-grow-1" style="flex: 1; min-width: 0;" data-sample="${sample}" placeholder="New label for ${sample}">
            </div>
        `;
        container.appendChild(div);
    });

    // Add event listeners to all custom label inputs
    document.querySelectorAll('.custom-label-input').forEach(input => {
        input.addEventListener('change', function() {
            if (window.plotActive) {
                window.updatePlotDynamically();
            }
        });
        
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (window.plotActive) {
                    window.updatePlotDynamically();
                }
            }, 500); // Wait 500ms after typing stops
        });
    });
}