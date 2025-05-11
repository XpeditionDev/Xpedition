import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT', 3306))
db_name = os.getenv('DB_NAME')

# Connect to the database
connection = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name,
    port=db_port
)

try:
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'itinerary' 
            AND COLUMN_NAME = 'is_ai_generated'
        """, (db_name,))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding is_ai_generated column to itinerary table...")
            cursor.execute("""
                ALTER TABLE itinerary 
                ADD COLUMN is_ai_generated BOOLEAN DEFAULT FALSE
            """)
            connection.commit()
            print("Column added successfully!")
        else:
            print("Column already exists!")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close() 