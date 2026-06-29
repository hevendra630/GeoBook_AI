import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {url}")
    # asyncpg requires the URL to start with postgresql:// or postgres://
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(url, ssl="require")
        print("Successfully connected!")
        
        # Create a new table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        print("Table 'test_users' ensured.")

        # Insert data into the table
        try:
            row = await conn.fetchrow('''
                INSERT INTO test_users (username, email) 
                VALUES ('testuser', 'testuser@example.com')
                RETURNING id, username, email;
            ''')
            print(f"Inserted row: {dict(row)}")
        except asyncpg.exceptions.UniqueViolationError:
            print("User 'testuser' already exists.")
        
        await conn.close()
    except Exception as e:
        print(f"Failed to connect or execute: {e}")

if __name__ == "__main__":
    asyncio.run(main())
