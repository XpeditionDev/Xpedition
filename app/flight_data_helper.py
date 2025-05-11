def format_flight_data_for_saving(flight_data):
    """
    Format flight data to match the structure expected by the save_flight route
    """
    return {
        'outbound': {
            'departure': {
                'city': flight_data.get('departure', {}).get('city', ''),
                'time': flight_data.get('departure', {}).get('time', ''),
                'airport': flight_data.get('departure', {}).get('airport', '')
            },
            'arrival': {
                'city': flight_data.get('arrival', {}).get('city', ''),
                'time': flight_data.get('arrival', {}).get('time', ''),
                'airport': flight_data.get('arrival', {}).get('airport', '')
            },
            'stops': flight_data.get('details', {}).get('outbound', {}).get('stops', 0),
            'duration': flight_data.get('details', {}).get('outbound', {}).get('duration', '')
        },
        'airline': flight_data.get('airline', ''),
        'price': flight_data.get('price', {}),
        'booking_reference': flight_data.get('booking_reference', '')
    } 