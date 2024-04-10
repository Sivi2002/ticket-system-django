document.getElementById('myForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission
    
    var formData = new FormData(this); // Create FormData object
    
    // Make a POST request to the endpoint
    fetch('/api/ticket', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('Form submitted successfully.');
            document.getElementById("myForm").reset();
            getURL()
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