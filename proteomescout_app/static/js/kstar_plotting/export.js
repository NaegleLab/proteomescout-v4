// Setup for export buttons
  document.addEventListener('DOMContentLoaded', function() {
    // Add export route to KSTAR config
    if (typeof KSTAR !== 'undefined' && KSTAR.config && KSTAR.config.routes) {
      KSTAR.config.routes.export = KSTAR.config.routes.plot + '/export';
    }
    
    // Format selection handling
    const exportCsvCheckbox = document.getElementById('exportCsv');
    const exportTsvCheckbox = document.getElementById('exportTsv');
    
    if (exportCsvCheckbox && exportTsvCheckbox) {
      // Make sure only one format is selected at a time
      exportCsvCheckbox.addEventListener('change', function() {
        if (this.checked) {
          exportTsvCheckbox.checked = false;
        } else if (!exportTsvCheckbox.checked) {
          // Ensure at least one is checked
          this.checked = true;
        }
      });
      
      exportTsvCheckbox.addEventListener('change', function() {
        if (this.checked) {
          exportCsvCheckbox.checked = false;
        } else if (!exportCsvCheckbox.checked) {
          // Ensure at least one is checked
          this.checked = true;
        }
      });
    }
    
    // Function to enable/disable export buttons
    const toggleExportButtons = function() {
      const exportDataBtn = document.getElementById('exportDataBtn');
      if (exportDataBtn) {
        exportDataBtn.disabled = !window.plotActive;
      }
    };
    
    // Add observer for when plot becomes active
    const plotObserver = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'style' && 
            document.getElementById('plotOutput').style.display !== 'none') {
          window.plotActive = document.getElementById('plotOutput').style.display !== 'none';
          toggleExportButtons();
        }
      });
    });
    
    const plotOutput = document.getElementById('plotOutput');
    if (plotOutput) {
      plotObserver.observe(plotOutput, { attributes: true });
      toggleExportButtons(); // Initial state
    }
    
    // Update button state when plot toggles
    document.getElementById('showPlot')?.addEventListener('change', function() {
      window.plotActive = this.checked;
      toggleExportButtons();
    });
  });