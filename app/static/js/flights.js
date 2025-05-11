document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.flight-cards')) {
        // Collect unique airlines
        const airlines = new Set();
        document.querySelectorAll('.flight-card').forEach(card => {
            airlines.add(card.dataset.airline);
        });

        // Create airline filters
        const airlineFilters = document.getElementById('airlineFilters');
        airlines.forEach(airline => {
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="checkbox" value="${airline}" checked>
                ${airline}
            `;
            airlineFilters.appendChild(label);
        });

        // Filter function
        function filterFlights() {
            const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseFloat(document.getElementById('maxPrice').value) || Infinity;
            const selectedStops = [...document.querySelectorAll('.filters input[type="checkbox"][value="0"], .filters input[type="checkbox"][value="1"], .filters input[type="checkbox"][value="2"]')]
                .filter(cb => cb.checked)
                .map(cb => parseInt(cb.value));
            const selectedAirlines = [...document.querySelectorAll('#airlineFilters input[type="checkbox"]')]
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            document.querySelectorAll('.flight-card').forEach(card => {
                const price = parseFloat(card.dataset.price);
                const stops = parseInt(card.dataset.stops);
                const airline = card.dataset.airline;

                const priceMatch = price >= minPrice && price <= maxPrice;
                const stopsMatch = selectedStops.includes(Math.min(stops, 2));
                const airlineMatch = selectedAirlines.includes(airline);

                card.style.display = priceMatch && stopsMatch && airlineMatch ? 'block' : 'none';
            });
        }

        // Add event listeners
        document.getElementById('minPrice').addEventListener('input', filterFlights);
        document.getElementById('maxPrice').addEventListener('input', filterFlights);
        document.querySelectorAll('.filters input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', filterFlights);
        });
    }

    // Modal functionality
    const modal = document.getElementById('saveFlightModal');
    const span = document.getElementsByClassName('close')[0];
    const itinerarySelect = document.getElementById('itinerary');
    const newItineraryFields = document.getElementById('newItineraryFields');

    window.selectFlight = function(flightData) {
        console.log('Flight selected:', flightData);  // Debug log
        const modal = document.getElementById('saveFlightModal');
        const flightDataInput = document.getElementById('flightData');
        
        if (!modal || !flightDataInput) {
            console.error('Modal or flight data input not found');  // Debug log
            return;
        }
        
        flightDataInput.value = JSON.stringify(flightData);
        console.log('Flight data set to:', flightDataInput.value);  // Debug log
        modal.style.display = 'block';
    }

    if (span) {
        span.onclick = function() {
            modal.style.display = 'none';
        }
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }

    if (itinerarySelect) {
        itinerarySelect.onchange = function() {
            if (this.value === 'new') {
                newItineraryFields.style.display = 'block';
            } else {
                newItineraryFields.style.display = 'none';
            }
        }
    }
});

function saveFlight(flightData) {
    const modal = document.getElementById('saveFlightModal');
    modal.style.display = 'block';
    modal.dataset.flightData = flightData;
}

function confirmSaveFlight() {
    const modal = document.getElementById('saveFlightModal');
    const flightData = JSON.parse(modal.dataset.flightData);
    const itineraryId = document.getElementById('itinerarySelect').value;
    
    fetch('/save-flight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            itinerary_id: itineraryId,
            flight: flightData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Flight saved to itinerary!');
        } else {
            alert('Error saving flight: ' + data.error);
        }
        closeModal();
    });
}

function closeModal() {
    const modal = document.getElementById('saveFlightModal');
    modal.style.display = 'none';
}

function showCreateItinerary() {
    document.getElementById('newItineraryForm').style.display = 'block';
}

function createItinerary() {
    const name = document.getElementById('newItineraryName').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    fetch('/create-itinerary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add new option to select
            const select = document.getElementById('itinerarySelect');
            const option = document.createElement('option');
            option.value = data.id;
            option.text = data.name;
            select.add(option);
            
            // Select the new option
            select.value = data.id;
            
            // Hide the form
            document.getElementById('newItineraryForm').style.display = 'none';
        } else {
            alert('Error creating itinerary: ' + data.error);
        }
    });
} 