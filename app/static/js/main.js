// Set minimum date for departure date input
document.addEventListener('DOMContentLoaded', function() {
    // Apply theme based on data-theme attribute on body
    const theme = document.body.dataset.theme;
    if (theme === 'dark') {
        document.documentElement.style.setProperty('--bg-color', '#121212');
        document.documentElement.style.setProperty('--text-color', '#e0e0e0');
        document.documentElement.style.setProperty('--card-bg', '#1e1e1e');
        document.documentElement.style.setProperty('--border-color', '#444');
        document.documentElement.style.setProperty('--input-bg', '#333');
        document.documentElement.style.setProperty('--input-color', '#e0e0e0');
        document.documentElement.style.setProperty('--muted-color', '#adb5bd');
        
        // Update navbar
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.remove('bg-primary');
            navbar.classList.add('bg-dark');
        }
    } else {
        document.documentElement.style.setProperty('--bg-color', '#ffffff');
        document.documentElement.style.setProperty('--text-color', '#333333');
        document.documentElement.style.setProperty('--card-bg', '#f8f9fa');
        document.documentElement.style.setProperty('--border-color', '#dee2e6');
        document.documentElement.style.setProperty('--input-bg', '#ffffff');
        document.documentElement.style.setProperty('--input-color', '#333333');
        document.documentElement.style.setProperty('--muted-color', '#6c757d');
        
        // Update navbar
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.remove('bg-dark');
            navbar.classList.add('bg-primary');
        }
    }

    const departureDateInput = document.getElementById('departure_date');
    if (departureDateInput) {
        const today = new Date().toISOString().split('T')[0];
        departureDateInput.min = today;
    }

    // Convert airport codes to uppercase
    const airportInputs = document.querySelectorAll('input[type="text"][pattern="[A-Z]{3}"]');
    airportInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });

    // Handle flight search form submission
    const flightSearchForm = document.getElementById('flightSearchForm');
    if (flightSearchForm) {
        flightSearchForm.addEventListener('submit', function(e) {
            const origin = document.getElementById('origin').value;
            const destination = document.getElementById('destination').value;
            
            if (origin === destination) {
                e.preventDefault();
                alert('Origin and destination airports cannot be the same');
                return;
            }
        });
    }

    // Handle save flight functionality
    const saveFlightButtons = document.querySelectorAll('.save-flight-btn');
    saveFlightButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const flightData = JSON.parse(this.dataset.flight);
            const select = this.closest('.save-flight-section').querySelector('.itinerary-select');
            const itineraryId = select.value;
            
            if (!itineraryId) {
                alert('Please select an itinerary');
                return;
            }
            
            try {
                const response = await fetch('/save-flight', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        flight_data: flightData,
                        itinerary_id: itineraryId
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Flight saved successfully!');
                    button.disabled = true;
                    button.textContent = 'Saved';
                } else {
                    alert(result.error || 'Failed to save flight');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while saving the flight');
            }
        });
    });

    // Handle modal functionality
    const modal = document.getElementById('saveFlightModal');
    if (modal) {
        // Close modal when clicking the X
        const closeBtn = modal.querySelector('.close');
        if (closeBtn) {
            closeBtn.onclick = function() {
                modal.style.display = 'none';
            };
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };

        // Handle new itinerary option
        const itinerarySelect = document.getElementById('itinerary');
        if (itinerarySelect) {
            itinerarySelect.addEventListener('change', function() {
                const newItineraryFields = document.getElementById('newItineraryFields');
                const newItineraryName = document.getElementById('new_itinerary_name');
                
                if (this.value === 'new') {
                    newItineraryFields.style.display = 'block';
                    newItineraryName.required = true;
                } else {
                    newItineraryFields.style.display = 'none';
                    newItineraryName.required = false;
                }
            });
        }
    }

    // Handle settings form submission
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(event) {
            // Prevent the default form submission
            event.preventDefault();
            
            // Get the selected theme and font size
            const themeSelect = document.getElementById('theme');
            const fontSizeSelect = document.getElementById('font_size');
            const notificationsEnabled = document.getElementById('notifications_enabled');
            const languageSelect = document.getElementById('language');
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            if (themeSelect && fontSizeSelect) {
                const theme = themeSelect.value;
                const fontSize = fontSizeSelect.value;
                const notifications = notificationsEnabled && notificationsEnabled.checked;
                const language = languageSelect ? languageSelect.value : 'en';
                
                // Check if theme has changed
                const currentTheme = document.body.dataset.theme;
                const themeChanged = (currentTheme !== theme);
                
                // Apply theme immediately
                document.body.dataset.theme = theme;
                
                // Update CSS variables
                if (theme === 'dark') {
                    document.documentElement.style.setProperty('--bg-color', '#121212');
                    document.documentElement.style.setProperty('--text-color', '#e0e0e0');
                    document.documentElement.style.setProperty('--card-bg', '#1e1e1e');
                    document.documentElement.style.setProperty('--border-color', '#444');
                    document.documentElement.style.setProperty('--input-bg', '#333');
                    document.documentElement.style.setProperty('--input-color', '#e0e0e0');
                    document.documentElement.style.setProperty('--muted-color', '#adb5bd');
                    
                    // Update navbar
                    document.querySelector('.navbar').classList.remove('bg-primary');
                    document.querySelector('.navbar').classList.add('bg-dark');
                } else {
                    document.documentElement.style.setProperty('--bg-color', '#ffffff');
                    document.documentElement.style.setProperty('--text-color', '#333333');
                    document.documentElement.style.setProperty('--card-bg', '#f8f9fa');
                    document.documentElement.style.setProperty('--border-color', '#dee2e6');
                    document.documentElement.style.setProperty('--input-bg', '#ffffff');
                    document.documentElement.style.setProperty('--input-color', '#333333');
                    document.documentElement.style.setProperty('--muted-color', '#6c757d');
                    
                    // Update navbar
                    document.querySelector('.navbar').classList.remove('bg-dark');
                    document.querySelector('.navbar').classList.add('bg-primary');
                }
                
                // Apply font size immediately
                if (fontSize === 'small') {
                    document.documentElement.style.setProperty('--font-size-base', '0.875rem');
                } else if (fontSize === 'medium') {
                    document.documentElement.style.setProperty('--font-size-base', '1rem');
                } else if (fontSize === 'large') {
                    document.documentElement.style.setProperty('--font-size-base', '1.125rem');
                }
                
                // Update language attribute on html tag
                document.documentElement.setAttribute('lang', language);
                
                // Store theme in localStorage for detection of changes
                localStorage.setItem('xpedition-theme', theme);
                
                // Show saving indicator
                const submitBtn = settingsForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';
                
                // Save settings via AJAX
                fetch('/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRF-Token': csrfToken
                    },
                    body: new URLSearchParams({
                        'csrf_token': csrfToken,
                        'theme': theme,
                        'font_size': fontSize,
                        'notifications_enabled': notifications ? 'true' : 'false',
                        'language': language
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success in the alert area
                        const alertDiv = document.getElementById('settings-alert');
                        const messageSpan = document.getElementById('settings-message');
                        
                        alertDiv.classList.remove('d-none', 'alert-danger');
                        alertDiv.classList.add('alert-success');
                        messageSpan.textContent = data.message || 'Settings updated successfully';
                        
                        // If theme changed, consider page reload to ensure all styles apply properly
                        if (themeChanged) {
                            messageSpan.textContent += ' - Please refresh other open pages to see all changes.';
                        }
                        
                        // Hide after a few seconds
                        setTimeout(() => {
                            alertDiv.classList.add('d-none');
                        }, 3000);
                    } else {
                        // Show error in the alert area
                        const alertDiv = document.getElementById('settings-alert');
                        const messageSpan = document.getElementById('settings-message');
                        
                        alertDiv.classList.remove('d-none', 'alert-success');
                        alertDiv.classList.add('alert-danger');
                        messageSpan.textContent = data.message || 'Failed to update settings';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    // Show error in the alert area
                    const alertDiv = document.getElementById('settings-alert');
                    const messageSpan = document.getElementById('settings-message');
                    
                    alertDiv.classList.remove('d-none', 'alert-success');
                    alertDiv.classList.add('alert-danger');
                    messageSpan.textContent = 'An error occurred while saving settings';
                })
                .finally(() => {
                    // Reset button text and enable
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                });
            }
        });
    }
});

// Helper functions for showing messages
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.card'));
}

function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.card'));
}