$(document).ready(function() {
    // when the search form is submitted, start the task and check the status periodically
    $('form').submit(function(event){
        event.preventDefault();
        //var query = $('#query').val();
        $.ajax({
            type: 'POST',
            url: '/proteins/',
            data: $('form').serialize(),
            success: function (data) {
                var task_id = data.task_id;

                // display a loading icon while the task is running
                $('#search-results').empty()
                
                const loader = document.createElement("div");
                loader.classList.add("loader");

                const searchResultsDiv = document.getElementById('search-results');
                searchResultsDiv.appendChild(loader);
                
                check_task_status(task_id);
            },
            error: function () {
                // something went wrong, handle the error
            }
        });
    })


    function check_task_status(task_id) {
        $.ajax({
            type: 'GET',
            url: '/proteins/search_status/' + task_id,
            success: function (data) {
                switch (data.state) {
                    case 'SUCCESS':
                        // task is complete, show the results
                        const loader = document.querySelector(".loader");
                        loader.classList.add("loader-hidden");
                        loader.addEventListener("transitioned", () => {
                            const searchResultsDiv = document.getElementById('search-results');
                            searchResultsDiv.removeChild("loader");
                        })
                        console.log("Results succesful");
                        console.log(data.result);
                        show_results(data.result);
                        break;
                    case 'PENDING':
                        // task is not complete, check again in 1 second
                        console.log('Results for ' + task_id + ' are currently unavailable')
                        setTimeout(function() {
                            check_task_status(task_id);
                        }, 1000);
                        break;
                    case 'FAILURE':
                        // task failed
                        console.log('The search query failed')                                                    
                        break;
                }
            },
            error: function () {
                console.error('Something went wrong with the check_task_status function');
                // something went wrong, handle the error
            }
        });
    }
    

    function show_results(results) {
        // show the search results on the page
        // ...

        const table = document.createElement("table");
        table.id = 'protein_table';
        table.classList.add("table");
        table.classList.add("table-striped");
        const container = document.getElementById("search-results");
        
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        const proteinHeader = document.createElement("th");
        const geneHeader = document.createElement("th");
        const speciesHeader = document.createElement("th");
        const seqLengthHeader = document.createElement("th");
        const sourceHeader = document.createElement("th");
        const modNumHeader = document.createElement("th");
        const modAAHeader = document.createElement("th");
        const modTypeHeader = document.createElement("th");

        thead.classList.add('thead-dark');

        proteinHeader.textContent = 'Protein';
        geneHeader.textContent = 'Gene';
        speciesHeader.textContent = 'Species';
        seqLengthHeader.textContent = 'Sequence Length';
        sourceHeader.textContent = 'Reported Sources';
        modNumHeader.textContent = 'Modified Residues';
        modAAHeader.textContent = 'Modified Amino Acids';
        modTypeHeader.textContent = 'Modification Types';

        headerRow.appendChild(proteinHeader);
        headerRow.appendChild(geneHeader);
        headerRow.appendChild(speciesHeader);
        headerRow.appendChild(seqLengthHeader);
        headerRow.appendChild(sourceHeader);
        headerRow.appendChild(modNumHeader);
        headerRow.appendChild(modAAHeader);
        headerRow.appendChild(modTypeHeader);
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        Object.entries(results).forEach(function([key, value]) {
            const row = document.createElement("tr");

            const proteinCell = document.createElement("td");
            const geneCell = document.createElement("td");
            const speciesCell = document.createElement("td");
            const seqLengthCell = document.createElement("td");
            const sourceCell = document.createElement("td");
            const modNumCell = document.createElement("td");
            const modAACell = document.createElement("td");
            const modTypeCell = document.createElement("td");

            const anchor = document.createElement("a");
            anchor.href = key + '/structure';
            anchor.textContent = value[0];
            
            proteinCell.appendChild(anchor);
            geneCell.textContent = value[1];
            speciesCell.textContent = value[2];
            seqLengthCell.textContent = value[3];
            sourceCell.textContent = value[4];
            modNumCell.textContent = value[5];
            modAACell.textContent = value[6];
            modTypeCell.textContent = value[7];

            row.appendChild(proteinCell);
            row.appendChild(geneCell);
            row.appendChild(speciesCell);
            row.appendChild(seqLengthCell);
            row.appendChild(sourceCell);
            row.appendChild(modNumCell);
            row.appendChild(modAACell);
            row.appendChild(modTypeCell);
            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        container.appendChild(table);
        $('#protein_table').DataTable({retrieve: true, "pageLength": 25, "order":[[5,'desc']]});
    }

})
