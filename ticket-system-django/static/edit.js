function setUpdate(){
    document.getElementById('updateForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent default form submission
        
        var formData = new FormData(this); // Create FormData object
        // Make a POST request to the endpoint
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                document.getElementById('set-form').style.display = 'block';
                getURL()
                $("#edit-form-container").empty();
                // Handle success (e.g., show success message)
            } else {
                console.error('Form submission failed.');
                // Handle failure (e.g., show error message)
            }
        })
        .catch(error => {
            console.error('Error:', error)
            // Handle errors
        });
    });
}

$(document).ready(function () {
    setUpdate();
});