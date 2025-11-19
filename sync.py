import os
import json
import time
import psycopg2
import requests
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Database credentials
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("dbname")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Track processed records to avoid duplicates
processed_records = set()


def fetch_from_openai(thread_id):
    """
    Fetches history from OpenAI based on the response id.
    
    Returns: 
        A list or dictionary that will be saved into the 'chat_history' column.
    """
    print(f"   ⏳ Fetching history for response: {thread_id}...")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.openai.com/v1/responses/{thread_id}/input_items"
    url2 = f"https://api.openai.com/v1/responses/{thread_id}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        response2 = requests.get(url2, headers=headers)
        response2.raise_for_status()

        input_items = response.json().get("data", [])[::-1]
        input_items = [{'role': item['role'], 'content': item['content'][0]['text']} for item in input_items]

        last_response = response2.json()
        
        input_items.append({
            'role': last_response['output'][0]['role'],
            'content': last_response['output'][0]['content'][0]['text']
        })
        
        return input_items

    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAI Request Failed: {e}")
        return None


def save_to_database(original_uuid, phone_from_response, thread_id_from_response, chat_data):
    """Save chat history to the database"""
    try:
        print(f"   💾 Syncing to 'openai_chat_history'...")
        
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        cur = conn.cursor()
        
        upsert_query = """
            INSERT INTO openai_chat_history (id, phone, response_id, chat_history, fetched_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (id) 
            DO UPDATE SET 
                chat_history = EXCLUDED.chat_history,
                phone = EXCLUDED.phone,  
                response_id = EXCLUDED.response_id,
                fetched_at = NOW();
        """
        
        cur.execute(upsert_query, (
            original_uuid,
            phone_from_response,
            thread_id_from_response,
            json.dumps(chat_data)
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Success! Data synced.")
        return True
        
    except Exception as err:
        print(f"❌ Error saving to database: {err}")
        return False


def check_for_updates():
    """Poll the database for recent updates"""
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        cur = conn.cursor()
        
        # Get all records updated in the last 60 seconds
        cur.execute("""
            SELECT id, phone, latest_response_id, updated_at
            FROM openai_responses 
            WHERE updated_at > NOW() - INTERVAL '60 seconds'
            AND latest_response_id IS NOT NULL
            ORDER BY updated_at DESC
        """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return []


def start_bot():
    """Main polling loop"""
    try:
        print("🔌 Connecting to database...")
        
        # Test connection
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        conn.close()
        
        print("✅ Python Bot connected.")
        print("👀 Polling for changes every 10 seconds...\n")
        
        while True:
            # Check for updates
            rows = check_for_updates()
            
            if rows:
                for row in rows:
                    original_uuid, phone, latest_response_id, updated_at = row
                    
                    # Use UUID as unique key to avoid processing same record twice
                    record_key = f"{original_uuid}:{latest_response_id}"
                    
                    if record_key not in processed_records:
                        print(f"\n🔔 Update detected for UUID: {original_uuid}")
                        print(f"   Latest Response ID: {latest_response_id}")
                        print(f"   Updated at: {updated_at}")
                        
                        if not latest_response_id or not original_uuid:
                            continue
                        
                        # Fetch from OpenAI
                        chat_data = fetch_from_openai(latest_response_id)
                        
                        if chat_data is None:
                            print("   ⚠️ Fetch returned None. Skipping save.")
                            continue
                        
                        # Save to database
                        if save_to_database(original_uuid, phone, latest_response_id, chat_data):
                            processed_records.add(record_key)
                            # Keep only recent records in memory (last 1000)
                            if len(processed_records) > 1000:
                                processed_records.clear()
            
            # Wait 10 seconds before next check
            time.sleep(10)

    except Exception as e:
        print(f"❌ Connection Error: {e}")


if __name__ == "__main__":
    start_bot()