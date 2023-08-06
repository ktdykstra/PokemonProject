document.addEventListener('DOMContentLoaded', function () {

  
    // Function to show the overlay content and button
    function showOverlay() {
      document.getElementById('overlay').style.display = 'flex';
      document.getElementById('overlay-content').style.display = 'block';
      document.getElementById('overlay-button').style.display = 'block';
    }
  
    // Function to close the overlay
    function closeOverlay() {
      document.getElementById('overlay').style.display = 'none';
      console.log('Overlay Closed');
  
    }
  

  
    function attachOverlayButtonListener() {
      const overlayButton = document.getElementById('overlay-button');
      overlayButton.addEventListener('click', function (event) {
        // Trigger the form submission when the button inside the overlay is clicked
        console.log('Overlay button clicked');
        document.getElementById('usernamePrivate').submit(); // Submit the form
      });
    }
  
  
    // Attach event listener to the form button
    document.getElementById('username-submit-private').addEventListener('click', function (event) {
      // Prevent the default form submission behavior
      event.preventDefault();

      showOverlay();
  
      // Call the Flask route to open the pop-up window
      fetch('/open_popup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      })
      .then((response) => response.json())
      .then((data) => {
        
        handleFormSubmission;

        // Show the overlay after receiving the driver data
        showOverlay();
      })
      .catch((error) => {
        console.error('An error occurred during the request:', error);
      });
  });



  // Call the function to attach the event listener when the DOM is ready
  attachOverlayButtonListener();
});

