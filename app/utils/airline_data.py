class AirlineData:
    AIRLINES = {
        'BA': {
            'name': 'British Airways',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/BA.png'
        },
        'AF': {
            'name': 'Air France',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/AF.png'
        },
        'LH': {
            'name': 'Lufthansa',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/LH.png'
        },
        'KL': {
            'name': 'KLM Royal Dutch Airlines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/KL.png'
        },
        'EK': {
            'name': 'Emirates',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/EK.png'
        },
        'IB': {
            'name': 'Iberia',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/IB.png'
        },
        'FR': {
            'name': 'Ryanair',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/FR.png'
        },
        'U2': {
            'name': 'easyJet',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/U2.png'
        },
        'VY': {
            'name': 'Vueling',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/VY.png'
        },
        'LX': {
            'name': 'Swiss International Air Lines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/LX.png'
        },
        'TK': {
            'name': 'Turkish Airlines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/TK.png'
        },
        'AY': {
            'name': 'Finnair',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/AY.png'
        },
        'SK': {
            'name': 'SAS',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/SK.png'
        },
        'LO': {
            'name': 'LOT Polish Airlines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/LO.png'
        },
        'OS': {
            'name': 'Austrian Airlines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/OS.png'
        },
        'TP': {
            'name': 'TAP Air Portugal',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/TP.png'
        },
        'SN': {
            'name': 'Brussels Airlines',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/SN.png'
        },
        'EI': {
            'name': 'Aer Lingus',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/EI.png'
        }
    }

    @staticmethod
    def get_airline_info(code):
        """Get airline name and logo URL for a given airline code"""
        default_info = {
            'name': f'Airline ({code})',
            'logo': 'https://www.gstatic.com/flights/airline_logos/70px/generic.png'  # Updated default logo
        }
        return AirlineData.AIRLINES.get(code, default_info) 