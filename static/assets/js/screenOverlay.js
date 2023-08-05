document.addEventListener('DOMContentLoaded', function() {
  
    // Function to show the overlay content and button
    function showOverlay() {
      document.getElementById('overlay').style.display = 'flex';
      document.getElementById('overlay-content').style.display = 'block';
      document.getElementById('overlay-button').style.display = 'block';
    }
  
    // Function to close the overlay
    function closeOverlay() {
      document.getElementById('overlay').style.display = 'none';
    }
  
    // Custom function to handle the form submission after the overlay button is clicked
    function handleFormSubmission(event) {
      // Prevent the default form submission behavior
      event.preventDefault();
  
      // Get the form data from the main form
      const usernamePrivate = document.getElementById('usernamePrivate').elements.usernamePrivate.value;
      const gametype = document.getElementById('usernamePrivate').elements.gametype.value;


  
      // Submit the form data to the server using AJAX
      fetch('/get_data_private', {
        method: 'POST',
        body: JSON.stringify({
            usernamePrivate: usernamePrivate,
            gametype: gametype,
        }),
        headers: {
            'Content-Type': 'application/json'
        }
      })
    
      .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);

            // Check if the server response contains the data you need
            if (data.success) {
                // Update your webpage or perform actions based on the response data
                // For example, you can display a success message, show the retrieved data, etc.
                // ...

                // Close the overlay after processing the form data
                closeOverlay();
            } else {
                // Handle the case when the server request was not successful
                console.error('Error: Server request failed.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
        console.log('Form submitted');
    }

    
    // Attach event listener to the form button
    document.getElementById('username-submit-private').addEventListener('click', function(event) {
      // Prevent the default form submission behavior
      event.preventDefault();
  
      // Open the pop-up window using Selenium here
      fetch('/open_popup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      .then(response => {
        if (response.ok) {
          // The request was successful, show the overlay
          showOverlay();
  
        } else {
          // Handle any errors that occurred during the request
          console.error('Failed to open the pop-up window.');
        }
      })
      .catch(error => {
        console.error('An error occurred during the request:', error);
      });
      // Show the overlay after the pop-up is opened
      showOverlay();
    });
  
    // Attach event listener to the overlay button
    const overlayButton = document.getElementById('overlay-button');
    if (overlayButton) {
      overlayButton.addEventListener('click', function(event) {
        // Trigger the form submission when the button inside the overlay is clicked
        console.log('Overlay button clicked');
        handleFormSubmission(event);
      });
    } else {
      console.log('Overlay button not found');
    }
  
  
    // Attach event listener to the form submission
    document.getElementById('usernamePrivate').addEventListener('submit', handleFormSubmission);
  });
  