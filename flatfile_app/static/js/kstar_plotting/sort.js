// Sort tab functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sortable list for manual kinase sorting
    const sortableKinaseListElement = document.getElementById('sortableKinaseList');
    if (sortableKinaseListElement) {
        window.sortableKinaseList = new Sortable(sortableKinaseListElement, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            handle: '.drag-handle',
        });
    }

    // --- Kinase Sorting ---
    document.querySelectorAll('input[name="sortKinases"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const manualContainer = document.getElementById('manualKinaseOrderContainer');
            const dendrogramOption = document.getElementById('kinasesDendrogramOption');
            const dendrogramColorContainer = document.getElementById('kinasesDendrogramColorContainer');
            
            // Hide all kinase-specific containers initially
            if (manualContainer) manualContainer.style.display = 'none';
            if (dendrogramOption) dendrogramOption.style.display = 'none';
            if (dendrogramColorContainer) dendrogramColorContainer.style.display = 'none';
            
            if (this.value === 'manual') {
                if (manualContainer) manualContainer.style.display = 'block';
                updateSortableKinaseList(); // Populate the draggable list
            } else if (this.value === 'by_clustering') {
                if (dendrogramOption) dendrogramOption.style.display = 'block';
                if (dendrogramColorContainer) dendrogramColorContainer.style.display = 'block';  
            }
            
            if (window.plotActive) {
                window.updatePlotDynamically();
            }
        });
    });

    // Handle kinase search for manual sorting
    const searchBox = document.getElementById('kinaseSearchBox');
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const listItems = document.querySelectorAll('#sortableKinaseList li');
            
            listItems.forEach(item => {
                const kinaseNameElement = item.querySelector('.kinase-name');
                if (kinaseNameElement) {
                    const kinaseName = kinaseNameElement.textContent.toLowerCase();
                    item.style.display = kinaseName.includes(searchTerm) ? '' : 'none';
                }
            });
        });
    }

    // Function to update the draggable/sortable kinase list for manual reordering
    function updateSortableKinaseList() {
        const list = document.getElementById('sortableKinaseList');
        if (!list) return;
        
        list.innerHTML = ''; // Clear existing list
        
        let kinasesToShow = [];
        if (typeof window.getDisplayableKinases === 'function') {
            kinasesToShow = window.getDisplayableKinases();
        } else {
            console.warn('window.getDisplayableKinases is not defined. Falling back to window.availableKinases for sortable list.');
            kinasesToShow = window.availableKinases || [];
        }
        
        kinasesToShow.forEach(kinase => {
            const li = document.createElement('li');
            li.className = 'list-group-item sortable-item'; // Added list-group-item for Bootstrap styling
            li.dataset.kinaseName = kinase; // Store kinase name for easier retrieval
            li.innerHTML = `
                <span class="drag-handle me-2" style="cursor: grab;"><i class="bi bi-grip-vertical"></i></span>
                <span class="kinase-name">${kinase}</span>
            `;
            list.appendChild(li);
        });
    }
    window.updateSortableKinaseList = updateSortableKinaseList; // Make it globally accessible if needed by main.js

    // Handle "Apply Manual Kinase Order" button
    document.getElementById('applyKinaseOrderButton')?.addEventListener('click', function() {
        const currentOrder = window.getCurrentKinaseOrder();
        document.getElementById('manualKinaseOrderJSON').value = JSON.stringify(currentOrder);
        console.log('Applying new manual kinase order:', currentOrder);
        
        if (window.plotActive) {
            const manualSortRadio = document.querySelector('input[name="sortKinases"][value="manual"]');
            if (manualSortRadio?.checked) {
                window.updatePlotDynamically(); // This will pick up the new manualKinaseOrderJSON value
            }
        }
    });

    // --- Sample Sorting ---
    const sampleSortRefKinaseContainer = document.getElementById('sampleSortRefKinaseContainer');
    const sampleSortRefKinaseSelect = document.getElementById('sampleSortRefKinaseSelect');

    // Function to update the dropdown for selecting reference kinase for sample sorting
    function updateSampleSortKinaseDropdown() {
        if (!sampleSortRefKinaseSelect) return;

        const currentSelectedValue = sampleSortRefKinaseSelect.value;
        sampleSortRefKinaseSelect.innerHTML = ''; // Clear existing options

        let kinasesToPopulate = [];
        if (typeof window.getDisplayableKinases === 'function') {
            kinasesToPopulate = window.getDisplayableKinases();
        } else {
            console.warn('window.getDisplayableKinases is not defined. Falling back to window.availableKinases for sample sort dropdown.');
            kinasesToPopulate = window.availableKinases || [];
        }

        if (kinasesToPopulate.length === 0) {
            const option = new Option('No kinases available to sort by', '');
            option.disabled = true;
            sampleSortRefKinaseSelect.appendChild(option);
            sampleSortRefKinaseSelect.disabled = true;
        } else {
            sampleSortRefKinaseSelect.disabled = false;
            kinasesToPopulate.forEach(kinase => {
                const option = new Option(kinase, kinase);
                sampleSortRefKinaseSelect.appendChild(option);
            });
            // Try to reselect the previously selected value, if it still exists
            if (kinasesToPopulate.includes(currentSelectedValue)) {
                sampleSortRefKinaseSelect.value = currentSelectedValue;
            } else if (kinasesToPopulate.length > 0) {
                sampleSortRefKinaseSelect.value = kinasesToPopulate[0]; // Select the first available if previous is gone
            }
        }
    }
    window.updateSampleSortKinaseDropdown = updateSampleSortKinaseDropdown; // Make global if needed

    document.querySelectorAll('input[name="sortSamples"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const samplesDendrogramOption = document.getElementById('samplesDendrogramOption');
            const samplesDendrogramColorContainer = document.getElementById('samplesDendrogramColorContainer');

            // Hide all sample-specific containers initially
            if (samplesDendrogramOption) samplesDendrogramOption.style.display = 'none';
            if (samplesDendrogramColorContainer) samplesDendrogramColorContainer.style.display = 'none';
            if (sampleSortRefKinaseContainer) sampleSortRefKinaseContainer.style.display = 'none';
            
            if (this.value === 'by_clustering') {
                if (samplesDendrogramOption) samplesDendrogramOption.style.display = 'block';
                if (samplesDendrogramColorContainer) samplesDendrogramColorContainer.style.display = 'block';
            } else if (this.value.startsWith('by_selected_kinase_')) {
                if (sampleSortRefKinaseContainer) sampleSortRefKinaseContainer.style.display = 'block';
                updateSampleSortKinaseDropdown(); // Populate/update the dropdown
            }
            
            if (window.plotActive) {
                window.updatePlotDynamically();
            }
        });
    });

    // Add event listener for changes to the reference kinase select dropdown
    if (sampleSortRefKinaseSelect) {
        sampleSortRefKinaseSelect.addEventListener('change', function() {
            if (window.plotActive) {
                // Ensure one of the "by_selected_kinase_" radios is checked before updating
                const bySelectedKinaseRadio = document.querySelector('input[name="sortSamples"][value^="by_selected_kinase_"]:checked');
                if (bySelectedKinaseRadio) {
                    window.updatePlotDynamically();
                }
            }
        });
    }


    // --- Dendrogram Color Pickers ---
    const kinasesDendrogramColorPicker = document.getElementById('kinases_dendrogram_color');
    if (kinasesDendrogramColorPicker) {
        ['input', 'change'].forEach(eventType => {
            kinasesDendrogramColorPicker.addEventListener(eventType, function() {
                if (window.plotActive) {
                    window.updatePlotDynamically();
                }
            });
        });
    }

    const samplesDendrogramColorPicker = document.getElementById('samples_dendrogram_color');
    if (samplesDendrogramColorPicker) {
        ['input', 'change'].forEach(eventType => {
            samplesDendrogramColorPicker.addEventListener(eventType, function() {
                if (window.plotActive) {
                    window.updatePlotDynamically();
                }
            });
        });
    }

    // Initial UI setup based on checked radios (e.g., on page load/refresh)
    // Trigger change on initially checked kinase sort radio
    const checkedKinaseSort = document.querySelector('input[name="sortKinases"]:checked');
    if (checkedKinaseSort) checkedKinaseSort.dispatchEvent(new Event('change'));
    
    // Trigger change on initially checked sample sort radio
    const checkedSampleSort = document.querySelector('input[name="sortSamples"]:checked');
    if (checkedSampleSort) checkedSampleSort.dispatchEvent(new Event('change'));

});

// Get current manual kinase order from the sortable list
window.getCurrentKinaseOrder = function() {
    const list = document.getElementById('sortableKinaseList');
    if (!list) return [];
    
    const kinaseOrder = Array.from(list.querySelectorAll('.sortable-item .kinase-name'))
        .map(item => item.textContent);
    // console.log('Current manual kinase order from list:', kinaseOrder);
    return kinaseOrder;
};