$(document).ready(function() {
    $('#downloadForm').on('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');  // Log when the form is submitted
        $(this).find(':submit').attr('disabled', 'disabled');  // Disable the submit button after first submission to not overload the app 
        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: $(this).serialize(),
            success: function(data) {
                console.log('AJAX request successful');  // Log when the AJAX request is successful
                console.log('Server response:', data);  // Log the server response
                $('#flashMessages').html('<ul class="flashes"><li>' + data.message + '</li></ul>');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log('AJAX request failed');  // Log when the AJAX request fails
                console.log('Status:', textStatus);  // Log the status
                console.log('Error:', errorThrown);  // Log the error
            },
            complete: function() {
                console.log('AJAX request complete');  // Log when the AJAX request is complete
                $('#downloadForm').find(':submit').removeAttr('disabled');  // Enable the submit button again when the AJAX request is complete
            }
        });
    });
});






/* $(document).ready(function() {
    $('#downloadForm').on('submit', function(e) {
        e.preventDefault();
        $(this).find(':submit').attr('disabled', 'disabled');  // Disable the submit button after first submission to not overload the app 
        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: $(this).serialize(),
            success: function(data) {
                $('#flashMessages').html('<ul class="flashes"><li>' + data.message + '</li></ul>');
            },
            complete: function() {
                $('#downloadForm').find(':submit').removeAttr('disabled');  // Enable the submit button again when the AJAX request is complete
            }
        });
    });
});*/