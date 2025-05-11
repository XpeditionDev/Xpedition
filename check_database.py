import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime
import re

# Load environment variables (if you have a .env file)
load_dotenv()

# Get database connection details from environment or use defaults
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # Empty string if no password
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'xpedition')  # Replace with your actual database name

def print_section(title):
    """Print a section header with clear separation"""
    print("\n" + "="*50)
    print(f"     {title}")
    print("="*50)

try:
    # Create connection string
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    
    print(f"Connecting to MySQL database: {DB_NAME}...")
    # Create engine
    engine = create_engine(connection_string)
    
    # Connect to the database
    with engine.connect() as connection:
        print(f"Connected successfully!")
        
        # Get min, max, and average prices
        print_section("FLIGHT PRICE STATISTICS")
        result = connection.execute(text("""
            SELECT 
                MIN(cost) as min_price, 
                MAX(cost) as max_price, 
                AVG(cost) as avg_price,
                COUNT(*) as total_flights
            FROM flight
        """))
        stats = result.fetchone()
        
        # Handle potentially None values
        if stats:
            min_price = stats[0] if stats[0] is not None else "N/A"
            max_price = stats[1] if stats[1] is not None else "N/A"
            avg_price = stats[2] if stats[2] is not None else "N/A"
            total_flights = stats[3] if stats[3] is not None else 0
            
            print(f"Minimum Price: £{min_price}")
            print(f"Maximum Price: £{max_price}")
            print(f"Average Price: £{avg_price if avg_price == 'N/A' else f'{avg_price:.2f}'}")
            print(f"Total Flights: {total_flights}")
        else:
            print("No flight price statistics available in the database.")
        
        # Check price distribution
        print_section("PRICE DISTRIBUTION")
        result = connection.execute(text("""
            SELECT 
                CASE
                    WHEN cost < 100 THEN 'Under £100'
                    WHEN cost >= 100 AND cost < 200 THEN '£100-£199'
                    WHEN cost >= 200 AND cost < 300 THEN '£200-£299'
                    WHEN cost >= 300 AND cost < 400 THEN '£300-£399'
                    WHEN cost >= 400 AND cost < 500 THEN '£400-£499'
                    ELSE '£500 and above'
                END as price_range,
                COUNT(*) as flight_count
            FROM flight
            GROUP BY price_range
            ORDER BY MIN(cost)
        """))
        for row in result:
            print(f"{row[0]}: {row[1]} flights")
            
        # Analyze data origin - check creation timestamps
        print_section("DATA ORIGIN ANALYSIS")
        
        # 1. Check creation timestamps for patterns
        print("\n1. Creation Date Patterns:")
        result = connection.execute(text("""
            SELECT 
                DATE(created_at) as creation_date,
                COUNT(*) as flight_count
            FROM flight
            WHERE created_at IS NOT NULL
            GROUP BY creation_date
            ORDER BY creation_date
        """))
        
        dates = result.fetchall()
        if not dates:
            print("  No creation dates found in the database.")
            date_counts = []
        else:
            for date_row in dates:
                print(f"  {date_row[0]}: {date_row[1]} flights added")
            
            # Check if all flights were added in batches
            date_counts = [row[1] for row in dates]
            if len(dates) == 1:
                print("\n  All flights were added on the same date - suggests batch import or sample data.")
            elif date_counts and max(date_counts) > 10:
                print("\n  Large batches of flights added on specific dates - suggests API data import or sample data population.")
                
        # 2. Check for airline code patterns
        print("\n2. Airline Distribution:")
        result = connection.execute(text("""
            SELECT 
                airline,
                COUNT(*) as flight_count
            FROM flight
            GROUP BY airline
            ORDER BY flight_count DESC
        """))
        
        airlines = result.fetchall()
        for airline in airlines:
            print(f"  {airline[0]}: {airline[1]} flights")
        
        # Check standard airline codes
        standard_airlines = ['BA', 'LH', 'AF', 'DL', 'AA', 'UA', 'EK', 'QF', 'SQ']
        real_airlines_found = [airline[0] for airline in airlines if airline[0] in standard_airlines]
        
        if real_airlines_found:
            print(f"\n  Found standard airline codes: {', '.join(real_airlines_found)} - suggests real flight data")
        else:
            print("\n  No standard airline codes found - might be using custom codes or sample data")
        
        # 3. Check for flight number patterns
        print("\n3. Flight Number Patterns:")
        result = connection.execute(text("""
            SELECT flight_number, COUNT(*) as count
            FROM flight
            WHERE flight_number IS NOT NULL
            GROUP BY flight_number
            ORDER BY count DESC
            LIMIT 10
        """))
        
        flight_numbers = result.fetchall()
        
        if not flight_numbers:
            print("  No flight numbers found - suggests sample data")
        else:
            for num in flight_numbers:
                print(f"  {num[0]}: {num[1]} occurrences")
            
            # Check for realistic flight number patterns (usually airline code + numbers)
            real_pattern = re.compile(r'^[A-Z]{2}\d{3,4}$')
            sample_pattern = re.compile(r'^[A-Z]+\d{1,2}$')
            
            real_format = [str(num[0]) for num in flight_numbers if num[0] and real_pattern.match(str(num[0]))]
            sample_format = [str(num[0]) for num in flight_numbers if num[0] and sample_pattern.match(str(num[0]))]
            
            if real_format:
                print(f"\n  Found realistic flight numbers: {', '.join(real_format)} - suggests Amadeus API data")
            if sample_format:
                print(f"\n  Found simplified flight numbers: {', '.join(sample_format)} - suggests sample data")
        
        # 4. Check for booking reference patterns
        print("\n4. Booking Reference Analysis:")
        result = connection.execute(text("""
            SELECT booking_reference, COUNT(*) as count
            FROM flight
            WHERE booking_reference IS NOT NULL
            GROUP BY booking_reference
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """))
        
        refs = result.fetchall()
        
        if not refs:
            print("  No duplicated booking references found")
        else:
            print("  Duplicated booking references (suggests flights in the same booking):")
            for ref in refs:
                print(f"  {ref[0]}: {ref[1]} flights")
                
            # Check connection groups
            result = connection.execute(text("""
                SELECT connection_group, COUNT(*) as segment_count
                FROM flight
                WHERE connection_group IS NOT NULL
                GROUP BY connection_group
                HAVING COUNT(*) > 1
                ORDER BY segment_count DESC
                LIMIT 5
            """))
            
            connections = result.fetchall()
            if connections:
                print("\n  Multi-segment connections found:")
                for conn in connections:
                    print(f"  {conn[0]}: {conn[1]} segments")
                print("  Multi-segment connections suggest real flight data from Amadeus API")
            else:
                print("\n  No multi-segment connections found - might be simple sample data")
        
        # 5. Check airport codes
        print("\n5. Airport Code Analysis:")
        result = connection.execute(text("""
            SELECT departure_airport as airport, COUNT(*) as count FROM flight
            GROUP BY airport
            UNION
            SELECT arrival_airport as airport, COUNT(*) as count FROM flight
            GROUP BY airport
            ORDER BY count DESC
        """))
        
        airports = result.fetchall()
        major_airports = ['LHR', 'JFK', 'LAX', 'CDG', 'DXB', 'FRA', 'AMS', 'SIN', 'HKG']
        minor_airports = ['KEF', 'BRU', 'MUC', 'YUL', 'IST']
        
        major_found = [airport[0] for airport in airports if airport[0] in major_airports]
        minor_found = [airport[0] for airport in airports if airport[0] in minor_airports]
        
        if major_found and minor_found:
            print(f"  Found a mix of major airports ({', '.join(major_found)}) and minor airports ({', '.join(minor_found)})")
            print("  This diverse set of airports suggests data from a real-world source like Amadeus API")
        elif major_found:
            print(f"  Only found major airports: {', '.join(major_found)}")
            print("  Limited airport diversity could be sample data using only well-known airports")
        else:
            print("  No standard airport codes found - might be using custom codes for sample data")
        
        # Overall assessment
        print_section("OVERALL ASSESSMENT")
        print("Based on the analysis, your flight data appears to be:")
        
        # We'll count indicators for each type
        real_data_indicators = 0
        sample_data_indicators = 0
        
        # Check creation dates
        if len(dates) > 3:
            real_data_indicators += 1
            print("  ✓ Created over multiple dates (suggests API data)")
        elif len(dates) <= 1:
            sample_data_indicators += 1
            print("  ✗ Created all at once (suggests sample data)")
        
        # Check airlines
        if len(real_airlines_found) > 2:
            real_data_indicators += 1
            print("  ✓ Uses standard airline codes (suggests API data)")
        else:
            sample_data_indicators += 1
            print("  ✗ Limited airline diversity (suggests sample data)")
        
        # Check airport diversity
        airport_set = set([a[0] for a in airports]) if airports else set()
        if len(airport_set) > 10:
            real_data_indicators += 1
            print("  ✓ High airport diversity (suggests API data)")
        else:
            print("  ✗ Limited airport set (suggests sample data)")
            sample_data_indicators += 1
            
        # Check multi-segment flights
        if refs and any(ref[1] > 1 for ref in refs):
            real_data_indicators += 1
            print("  ✓ Multi-segment bookings found (suggests API data)")
        else:
            sample_data_indicators += 1
            print("  ✗ No multi-segment bookings (suggests sample data)")
        
        # Final verdict
        if real_data_indicators > sample_data_indicators:
            print("\nVerdict: LIKELY REAL API DATA or realistic simulation data")
        elif sample_data_indicators > real_data_indicators:
            print("\nVerdict: LIKELY SAMPLE DATA")
        else:
            print("\nVerdict: MIXED DATA SOURCES or inconclusive evidence")
        
        # Execute binary search directly against the database
        print_section("BINARY SEARCH TEST")
        print("Testing search for flights in a specific price range:")
        # Try different price range that might have flights
        target_price = 200.0
        tolerance = 50.0
        
        result = connection.execute(text("""
            SELECT COUNT(*) FROM flight 
            WHERE cost BETWEEN :lower AND :upper
        """), {"lower": target_price - tolerance, "upper": target_price + tolerance})
        
        count = result.scalar()
        print(f"Flights with price £{target_price} ± £{tolerance}: {count}")
        
        if count and count > 0:
            # If there are matches, show them
            result = connection.execute(text("""
                SELECT id, departure_airport, arrival_airport, airline, cost, booking_reference
                FROM flight 
                WHERE cost BETWEEN :lower AND :upper
                ORDER BY ABS(cost - :target)
                LIMIT 5
            """), {"lower": target_price - tolerance, "upper": target_price + tolerance, "target": target_price})
            
            print("\nClosest matches:")
            for row in result:
                price_diff = abs(row[4]-target_price) if row[4] is not None else 0
                print(f"  Flight #{row[0]}: {row[1]} → {row[2]} ({row[3]}): £{row[4]} (diff: £{price_diff:.2f})")
                if row[5]:  # If booking reference exists
                    print(f"    Booking Reference: {row[5]}")

except Exception as e:
    print(f"Error connecting to database: {e}") 