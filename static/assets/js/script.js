// Get references to the input field and dropdown menu
const gametypeInput = document.getElementById('gametype');
const gametypeDropdown = document.getElementById('gametypeDropdown');

// Show the dropdown when the input field is clicked
gametypeInput.addEventListener('click', function() {
    gametypeDropdown.style.display = 'block';
});

// Hide the dropdown when the user clicks outside of it
document.addEventListener('click', function(event) {
    if (event.target !== gametypeInput && event.target.parentNode !== gametypeDropdown) {
        gametypeDropdown.style.display = 'none';
    }
});

// Handle dropdown item selection
gametypeDropdown.addEventListener('click', function(event) {
    const selectedValue = event.target.dataset.value;
    gametype.value = selectedValue;
    gametypeDropdown.style.display = 'none';
});
