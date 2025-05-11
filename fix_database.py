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
        # Check if the itinerary table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = 'itinerary'
        """, (db_name,))
        
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            print("Creating itinerary table...")
            cursor.execute("""
                CREATE TABLE itinerary (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_budget FLOAT,
                    is_ai_generated BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """)
            connection.commit()
            print("Table created successfully!")
        else:
            print("Itinerary table already exists.")
            
            # Check if is_ai_generated column exists
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
                print("is_ai_generated column already exists!")
                
except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close()

print("Database check completed!") 