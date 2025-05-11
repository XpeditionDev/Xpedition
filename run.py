from app import create_app, db

from app.models import User, UserSettings, Itinerary, Flight, Accommodation, Activity, Destination

import os



# Check and set environment variables if not already set

rapidapi_key = os.environ.get('RAPIDAPI_KEY')

if rapidapi_key:

    print(f"Found RAPIDAPI_KEY in environment variables: {rapidapi_key[:6]}...{rapidapi_key[-4:]}")

else:

    # Try to get from PowerShell environment variable directly

    import subprocess

    try:

        result = subprocess.run(['powershell', '-Command', 'Write-Output $env:RAPIDAPI_KEY'], 

                               capture_output=True, text=True, check=False)

        ps_key = result.stdout.strip()

        if ps_key:

            print(f"Setting RAPIDAPI_KEY from PowerShell environment: {ps_key[:6]}...{ps_key[-4:]}")

            os.environ['RAPIDAPI_KEY'] = ps_key

        else:

            print("WARNING: RAPIDAPI_KEY not found in PowerShell environment")

    except Exception as e:

        print(f"Error trying to get RAPIDAPI_KEY from PowerShell: {str(e)}")



app = create_app()



@app.shell_context_processor

def make_shell_context():

    return {

        'db': db, 

        'User': User, 

        'UserSettings': UserSettings,

        'Itinerary': Itinerary,

        'Flight': Flight,

        'Accommodation': Accommodation,

        'Activity': Activity,

        'Destination': Destination

    }



if __name__ == '__main__':

    print("Starting Xpedition application...")

    print("Open your browser and navigate to http://127.0.0.1:5000/")

    

    # Do one final check of environment variables

    print("\n===== ENVIRONMENT VARIABLES CHECK =====")

    api_key = os.environ.get('RAPIDAPI_KEY', 'NOT SET')

    if api_key != 'NOT SET':

        masked_key = api_key[:6] + '*****' + api_key[-4:]

        print(f"RAPIDAPI_KEY is set to: {masked_key}")

    else:

        print("RAPIDAPI_KEY is NOT SET")

    print("======================================\n")

    

    app.run(debug=True, host='0.0.0.0', port=5000) 