// Global state and config
window.plotActive = false;
window.availableKinases = [];
window.availableSamples = [];
window.sortableKinaseList;

// Constants for raster formats
const RASTER_FORMATS = {
  png: { dpi: 300 },
  jpg: { dpi: 300 },
  tif: { dpi: 300 }
};

// Utility functions
function getUpdateFormData() {
  console.log('Getting update form data');
  const formData = new FormData();
  const originalLogResults = document.getElementById('originalLogResultsJSON').value;
  const originalFprData = document.getElementById('originalFprDataJSON').value;
  
  if (!originalLogResults || originalLogResults.length < 10) {
    alert('Missing or invalid original data. Please regenerate the plot.');
    return null;
  }

  // Append data fields
  formData.append('original_log_results', originalLogResults);
  formData.append('original_fpr_df', originalFprData);
  formData.append('log_results', document.getElementById('logResultsJSON').value);
  formData.append('fpr_df', document.getElementById('fprDataJSON').value);

  // Selections and parameters
  formData.append('kinaseSelect', JSON.stringify($('#kinaseSelect').val() || []));
  formData.append('sampleSelect', JSON.stringify($('#sampleSelect').val() || []));
  formData.append('manualKinaseEdit', document.getElementById('manualKinaseEdit').value);
  formData.append('figureWidth', document.getElementById('figureWidth').value);
  formData.append('figureHeight', document.getElementById('figureHeight').value);
  formData.append('fontSize', document.getElementById('fontSize').value);
  formData.append('backgroundColor', document.getElementById('backgroundColor').value);
  formData.append('activityColor', document.getElementById('activityColor').value);
  formData.append('lackActivityColor', document.getElementById('lackActivityColor').value);
  formData.append('significantActivity', document.querySelector('input[name="significantActivity"]:checked').value);

  // Dendrogram toggles
  formData.append('showKinasesDendrogramInside', document.getElementById('showKinasesDendrogramInside').checked);
  formData.append('showSamplesDendrogram', document.getElementById('showSamplesDendrogram').checked);
  formData.append('kinases_dendrogram_color', document.getElementById('kinases_dendrogram_color').value);
  formData.append('samples_dendrogram_color', document.getElementById('samples_dendrogram_color').value);

  // Custom labels if enabled
  const changeXLabel = document.getElementById('changeXLabel').checked;
  formData.append('changeXLabel', changeXLabel);
  if (changeXLabel) {
    const customLabels = {};
    document.querySelectorAll('.custom-label-input').forEach(input => {
      const sample = input.dataset.sample;
      const newLabel = input.value.trim();
      if (newLabel) customLabels[sample] = newLabel;
    });
    formData.append('customXLabels', JSON.stringify(customLabels));
  }

  // Sorting options
  const sortKinasesMode = document.querySelector('input[name="sortKinases"]:checked').value;
  formData.append('sortKinases', sortKinasesMode);

  const sortSamplesModeRadio = document.querySelector('input[name="sortSamples"]:checked');
  if (sortSamplesModeRadio) {
    const sortSamplesMode = sortSamplesModeRadio.value;
    formData.append('sortSamples', sortSamplesMode);

    // If sorting samples by a selected kinase, get the selected kinase
    if (sortSamplesMode.startsWith('by_selected_kinase_')) {
      const sampleSortRefKinaseSelect = document.getElementById('sampleSortRefKinaseSelect');
      if (sampleSortRefKinaseSelect && sampleSortRefKinaseSelect.value) {
        formData.append('sample_sort_ref_kinase', sampleSortRefKinaseSelect.value);
        console.log('Appending sample_sort_ref_kinase:', sampleSortRefKinaseSelect.value);
      } else {
        console.warn('Sample sort mode is by_selected_kinase_ but sampleSortRefKinaseSelect is missing or has no value.');
        // Optionally, you could send 'none' or revert sortSamples to 'none' if the kinase isn't selected
        // formData.set('sortSamples', 'none'); 
      }
    }
  } else {
    formData.append('sortSamples', 'none'); // Default if no radio is checked (should not happen with proper HTML)
  }


  // Manual kinase order
  if (sortKinasesMode === 'manual') {
    const manualKinaseOrder = document.getElementById('manualKinaseOrderJSON').value;
    if (manualKinaseOrder) formData.append('manualKinaseOrder', manualKinaseOrder);
  }


  formData.append('restrictKinases', document.getElementById('restrictKinases').checked);

  return formData;
}

function displayPlotResults(data) {
  console.log('Displaying plot results:', data);
  document.getElementById('logResultsJSON').value = data.log_results;
  document.getElementById('fprDataJSON').value = data.fpr_df;

  if (data.original_log_results) {
    document.getElementById('originalLogResultsJSON').value = data.original_log_results;
    document.getElementById('originalFprDataJSON').value = data.original_fpr_df;
  }

  const imgSrc = `data:image/png;base64,${data.plot}`;
  document.getElementById('plotImageIntegrated').src = imgSrc;
  document.getElementById('plotOutput').style.display = 'block';

  window.plotActive = true;
  const exportBtn = document.getElementById('exportDataBtn');
  if (exportBtn) exportBtn.disabled = false;

  const statusField = document.getElementById('plotStatusField');
  if (statusField) statusField.value = '1';
  
  // Update kinase dropdown to reflect current restriction state
}

// AJAX interactions
function submitForm() {
  console.log('Submitting main form');
  const activitiesFile = document.getElementById('kstarActivitiesFile').files[0];
  const fprFile = document.getElementById('kstarFPRFile').files[0];

  if (!activitiesFile || !fprFile) {
    alert('Please upload both activities and FPR files');
    return;
  }

  const formData = new FormData();
  formData.append('activitiesFile', activitiesFile);
  formData.append('fprFile', fprFile);
  formData.append('figureWidth', document.getElementById('figureWidth').value);
  formData.append('figureHeight', document.getElementById('figureHeight').value);
  formData.append('fontSize', document.getElementById('fontSize').value);
  formData.append('significantActivity', document.querySelector('input[name="significantActivity"]:checked').value);
  formData.append('backgroundColor', document.getElementById('backgroundColor').value);
  formData.append('activityColor', document.getElementById('activityColor').value);
  formData.append('lackActivityColor', document.getElementById('lackActivityColor').value);
  formData.append('restrictKinases', document.getElementById('restrictKinases').checked);
  formData.append('manualKinaseEdit', document.getElementById('manualKinaseEdit').value);
  formData.append('changeXLabel', document.getElementById('changeXLabel').checked);
  formData.append('showKinasesDendrogramInside', document.getElementById('showKinasesDendrogramInside').checked);
  formData.append('showSamplesDendrogram', document.getElementById('showSamplesDendrogram').checked);
  formData.append('kinases_dendrogram_color', document.getElementById('kinases_dendrogram_color').value);
  formData.append('samples_dendrogram_color', document.getElementById('samples_dendrogram_color').value);

  if (document.getElementById('manualKinaseEdit').value !== 'none') {
    formData.append('kinaseSelect', JSON.stringify($('#kinaseSelect').val() || []));
    formData.append('kinaseEditMode', document.getElementById('manualKinaseEdit').value);
  }

  formData.append('manualSampleSelect', ($('#sampleSelect').val() || []).join(','));
  formData.append('sortKinases', document.querySelector('input[name="sortKinases"]:checked').value);
  formData.append('sortSamples', document.querySelector('input[name="sortSamples"]:checked').value);

  const manualOrder = document.getElementById('manualKinaseOrderJSON').value;
  if (manualOrder && document.querySelector('input[name="sortKinases"]:checked').value === 'manual') {
    let orderToSend = manualOrder;
    
    // Filter manual order if kinases are restricted to significant
    const restrictCheckbox = document.getElementById('restrictKinases');
    if (restrictCheckbox && restrictCheckbox.checked && window.plotActive) {
      const logResultsJson = document.getElementById('logResultsJSON')?.value;
      if (logResultsJson) {
        try {
          const logResultsData = JSON.parse(logResultsJson);
          const sampleNames = Object.keys(logResultsData);
          if (sampleNames.length > 0) {
            const firstSample = logResultsData[sampleNames[0]];
            if (firstSample && typeof firstSample === 'object') {
              const significantKinases = Object.keys(firstSample);
              const currentOrder = JSON.parse(manualOrder);
              // Filter the manual order to only include significant kinases
              const filteredOrder = currentOrder.filter(kinase => significantKinases.includes(kinase));
              orderToSend = JSON.stringify(filteredOrder);
            }
          }
        } catch (e) {
          console.error('Error filtering manual kinase order for significant kinases:', e);
        }
      }
    }
    
    formData.append('manualKinaseOrder', orderToSend);
  }

  formData.append('showPlot', document.getElementById('showPlot').checked);

  fetch(KSTAR.config.routes.plot, { method: 'POST', body: formData })
    .then(res => res.ok ? res.json() : res.json().then(err => Promise.reject(err)))
    .then(displayPlotResults)
    .catch(err => alert('Error generating plot: ' + (err.error || err.message)));
}

function updatePlotDynamically() {
  console.log('Updating plot dynamically');
  if (!window.plotActive) return;

  const formData = getUpdateFormData();
  if (!formData) return;

  fetch(KSTAR.config.routes.update, { method: 'POST', body: formData })
    .then(res => res.ok ? res.json() : res.json().then(e => Promise.reject(e)))
    .then(displayPlotResults)
    .catch(err => alert('Error updating plot: ' + (err.error || err.message)));
}

// Download and export
function setupDownloadHandler() {
  const btn = document.getElementById('downloadBtn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const formData = getUpdateFormData();
    if (!formData) return;

    const format = document.querySelector('input[name="downloadFormat"]:checked').value;
    const fname = document.getElementById('figureNameInput').value;
    formData.append('download_format', format);
    formData.append('file_name', fname);
    if (RASTER_FORMATS[format]) formData.append('dpi', RASTER_FORMATS[format].dpi);

    fetch(`${KSTAR.config.routes.plot}/download`, { method: 'POST', body: formData })
      .then(res => res.ok ? res.blob() : res.json().then(e => Promise.reject(e)))
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${fname}.${format}`;
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
      })
      .catch(err => alert('Error downloading plot: ' + (err.error||err.message)));
  });
}

function exportSpecificData(dataType, userFileNameParam) {
  const logJSON = document.getElementById('logResultsJSON').value;
  const fprJSON = document.getElementById('fprDataJSON').value;
  if (!logJSON || !fprJSON) return alert('No data available to export. Please generate a plot first.');

  const formData = new FormData();
  const exportFormat = document.getElementById('exportTsv').checked ? 'tsv' : 'csv';
  formData.append('export_format', exportFormat);
  
  //Check and send custom labels ***
  const changeXLabel = document.getElementById('changeXLabel')?.checked;
  formData.append('changeXLabel', changeXLabel || false); 
  if (changeXLabel) {
    const customLabels = {};
    document.querySelectorAll('.custom-label-input').forEach(input => {
      const sample = input.dataset.sample; // Original sample name from data-* attribute
      const newLabel = input.value.trim();
      if (sample && newLabel) { 
        customLabels[sample] = newLabel;
      }
    });
    if (Object.keys(customLabels).length > 0) {
        formData.append('customXLabels', JSON.stringify(customLabels));
        console.log("Sending custom labels for export:", JSON.stringify(customLabels));
    } else {
        console.log("Change X Label checked, but no custom labels found/entered.");
        // Ensure changeXLabel flag is false if no labels are actually sent
        formData.set('changeXLabel', false);
    }
  } else {
      console.log("Change X Label not checked for export.");
  }

  // Add file name if specified
  const userFileName = userFileNameParam || document.getElementById('exportFileName')?.value.trim() || 'KSTAR';
  formData.append('file_name', userFileName); 

  
  formData.append('log_results', logJSON);
  formData.append('fpr_df', fprJSON);

  const endpoint = dataType === 'both'
    ? KSTAR.config.routes.export
    : `${KSTAR.config.routes.export}/${dataType}`;

  fetch(endpoint, { method: 'POST', body: formData })
    .then(res => res.ok ? res.blob() : res.json().then(e => Promise.reject(e)))
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Use the custom filename if provided
      const baseFilename = userFileName; 
      let downloadFilename;
      if (dataType === 'both') {
        downloadFilename = `${baseFilename}_data_export.zip`;
      } else {
        downloadFilename = `${baseFilename}_${dataType}.${exportFormat}`;
      }
      console.log(`Setting download filename to: ${downloadFilename}`);
      a.download = downloadFilename;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      document.body.removeChild(a);
    })
    .catch(err => alert('Error exporting data: ' + (err.error || err.message)));
}

// Select2 and UI setup
function updateKinaseSelect() {
  const mode = document.getElementById('manualKinaseEdit').value;
  if (mode === 'none') return;
  
  const select = $('#kinaseSelect');
  const currentSelection = select.val() || []; 
  select.empty();

  // Use the same logic as getDisplayableKinases for consistency
  const kinasesToShow = window.getDisplayableKinases();

  // Populate dropdown with appropriate kinases
  kinasesToShow.forEach(k => select.append(new Option(k, k)));
  
  // Restore valid selections
  const validSelection = currentSelection.filter(k => kinasesToShow.includes(k));
  select.val(validSelection);

  select.select2({
    placeholder: mode === 'select' ? 'Select kinases to include...' : 'Select kinases to remove...',
    allowClear: true,
    width: '100%'
  });

  // Also refresh sort dropdowns when kinase list changes
  if (typeof window.updateSortableKinaseList === 'function') {
    window.updateSortableKinaseList();
  }
  if (typeof window.updateSampleSortKinaseDropdown === 'function') {
    window.updateSampleSortKinaseDropdown();
  }
}

function updateSampleSelect() {
  const select = $('#sampleSelect'); if (!select.length) return;
  select.empty();
  if (!window.availableSamples.length) return;
  window.availableSamples.forEach(s => select.append(new Option(s, s)));
  select.select2({ placeholder: 'Select samples...', allowClear: true, width: '100%' });
}

function initSelect2() {
  $('#kinaseSelect').select2({ placeholder: 'Select kinases...', allowClear: true, width: '100%' });
  $('#sampleSelect').select2({ placeholder: 'Select samples...', allowClear: true, width: '100%' });
}

function setupDendrogramToggles() {
  document.getElementById('sortKinasesHier').addEventListener('change', () => {
    document.getElementById('kinasesDendrogramOption').style.display = 'block';
  });
  document.querySelectorAll('input[name="sortKinases"]').forEach(r => {
    if (r.id !== 'sortKinasesHier') r.addEventListener('change', () => {
      document.getElementById('kinasesDendrogramOption').style.display = 'none';
    });
  });
  document.getElementById('sortSamplesHier').addEventListener('change', () => {
    document.getElementById('samplesDendrogramOption').style.display = 'block';
  });
  document.querySelectorAll('input[name="sortSamples"]').forEach(r => {
    if (r.id !== 'sortSamplesHier') r.addEventListener('change', () => {
      document.getElementById('samplesDendrogramOption').style.display = 'none';
    });
  });

  ['showKinasesDendrogramInside','showSamplesDendrogram'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
      if (window.plotActive) updatePlotDynamically();
    });
  });
}

// File input handling
function handleFileInputs() {
  console.log('File input changed');
  const activitiesFile = document.getElementById('kstarActivitiesFile').files[0];
  const fprFile = document.getElementById('kstarFPRFile').files[0];
  if (!activitiesFile || !fprFile) return;

  const formData = new FormData();
  formData.append('activitiesFile', activitiesFile);
  formData.append('fprFile', fprFile);

  console.log('Fetching columns from:', KSTAR.config.routes.columns);
  fetch(KSTAR.config.routes.columns, { method: 'POST', body: formData })
    .then(res => res.ok ? res.json() : res.json().then(e => Promise.reject(e)))
    .then(data => {
      window.availableSamples = data.columns;
      window.availableKinases = data.kinases;
      if (window.availableSamples.length) updateSampleSelect();
      if (window.availableKinases.length) updateKinaseSelect();
    })
    .catch(err => alert('Error processing files: ' + (err.error||err.message)));
}

// Add this function after your global variables at the top
window.getDisplayableKinases = function() {
  const restrictCheckbox = document.getElementById('restrictKinases');
  const isRestricted = restrictCheckbox ? restrictCheckbox.checked : false;
  
  if (isRestricted && window.plotActive) {
    const logResultsJson = document.getElementById('logResultsJSON')?.value;
    if (logResultsJson) {
      try {
        const logResultsData = JSON.parse(logResultsJson);
        const sampleNames = Object.keys(logResultsData);
        if (sampleNames.length > 0) {
          const firstSample = logResultsData[sampleNames[0]];
          return firstSample ? Object.keys(firstSample).sort() : [];
        }
      } catch (e) {
        console.error('Error parsing logResultsJSON:', e);
      }
    }
    return [];
  }
  return (window.availableKinases || []).slice().sort();
};

// DOM ready setup
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM Content Loaded');
  document.getElementById('kstarActivitiesFile')?.addEventListener('change', handleFileInputs);
  document.getElementById('kstarFPRFile')?.addEventListener('change', handleFileInputs);
  initSelect2();
  setupDendrogramToggles();

  // Full-update fields
  const fullUpdateSelectors = ['#figureWidth', '#figureHeight', '#fontSize', '#backgroundColor', 
    '#activityColor', '#lackActivityColor', 'input[name="significantActivity"]', 
    '#restrictKinases', '#changeXLabel'];
  fullUpdateSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => el.addEventListener('change', () => {
      if (window.plotActive) submitForm();
    }));
  });

  setupDownloadHandler();

  // Export CSV/TSV toggles
  const csvCheckbox = document.getElementById('exportCsv');
  const tsvCheckbox = document.getElementById('exportTsv');
  if (csvCheckbox && tsvCheckbox) {
    csvCheckbox.addEventListener('change', () => {
      if (csvCheckbox.checked) tsvCheckbox.checked = false;
      else if (!tsvCheckbox.checked) csvCheckbox.checked = true;
    });
    tsvCheckbox.addEventListener('change', () => {
      if (tsvCheckbox.checked) csvCheckbox.checked = false;
      else if (!csvCheckbox.checked) tsvCheckbox.checked = true;
    });
  }

  // Export data button
  document.getElementById('exportDataBtn')?.addEventListener('click', () => {
    exportSpecificData(document.getElementById('exportDataType').value);
  });

  // Selection change handlers
  $('#kinaseSelect').on('select2:select select2:unselect', () => {
    if (window.plotActive && document.getElementById('manualKinaseEdit').value !== 'none') {
      updatePlotDynamically();
    }
  });
  $('#sampleSelect').on('select2:select select2:unselect', () => {
    if (window.plotActive) updatePlotDynamically();
  });

  // Toggle plot visibility
  document.getElementById('showPlot').addEventListener('change', e => {
    if (e.target.checked) {
      submitForm();
      window.plotActive = true;
    } else {
      document.getElementById('plotOutput').style.display = 'none';
      window.plotActive = false;
      document.getElementById('exportDataBtn').disabled = true;
    }
  });

  // Add export route to KSTAR config if available
  if (typeof KSTAR !== 'undefined' && KSTAR.config && KSTAR.config.routes && KSTAR.config.routes.plot) {
    KSTAR.config.routes.export = KSTAR.config.routes.plot + '/export'; // e.g., /kstar/plot + /export
    console.log('Set KSTAR export route to:', KSTAR.config.routes.export); 
  } else {
    console.warn('KSTAR config or routes not fully defined for setting export route.');
  }
});