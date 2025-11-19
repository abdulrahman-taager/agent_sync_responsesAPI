Here is a comprehensive `README.md` file for your project. It includes installation instructions, database requirements (inferred from your code), and a guide on how to run the bot.

-----

# OpenAI Chat History Sync Bot

A Python automation script that polls a PostgreSQL database for new OpenAI interactions, fetches the full conversation history (inputs and outputs) from the OpenAI API, and archives the data back into a dedicated history table.

## 🚀 Features

  * **Automated Polling:** Checks the database every 10 seconds for recently updated records.
  * **Data Synchronization:** Fetches input items and generated outputs from OpenAI's `responses` endpoint.
  * **Duplicate Prevention:** Uses in-memory tracking to ensure the same response isn't processed twice in short succession.
  * **Database Upsert:** Inserts new history records or updates existing ones if the ID matches.
  * **JSON Storage:** Stores the full conversation flow as structured JSON in the database.

## 🛠️ Prerequisites

  * Python 3.8+
  * PostgreSQL Database
  * OpenAI API Key

## 📦 Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Install dependencies:**
    You can create a `requirements.txt` or install them directly:

    ```bash
    pip install psycopg2-binary requests python-dotenv
    ```

## ⚙️ Configuration

1.  Create a `.env` file in the root directory.
2.  Add your database credentials and OpenAI API key as shown below:

<!-- end list -->

```ini
# Database Configuration
user=your_db_user
password=your_db_password
host=localhost
port=5432
dbname=your_database_name

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## 🗄️ Database Schema

Ensure your PostgreSQL database has the required tables. Based on the script logic, here is the SQL to create them:

### 1\. Source Table (`openai_responses`)

This is the table the bot watches for updates.

```sql
CREATE TABLE IF NOT EXISTS openai_responses (
    id UUID PRIMARY KEY,
    phone VARCHAR(20),
    latest_response_id VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2\. Destination Table (`openai_chat_history`)

This is where the bot saves the synced chat history.

```sql
CREATE TABLE IF NOT EXISTS openai_chat_history (
    id UUID PRIMARY KEY,
    phone VARCHAR(20),
    response_id VARCHAR(255),
    chat_history JSONB,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

## 🏃 Usage

Run the script using Python:

```bash
python main.py
```

*Note: Replace `main.py` with the actual name of your python file.*

## 🔄 How It Works

1.  **Connect:** The script establishes a connection to the PostgreSQL database defined in the `.env` file.
2.  **Poll:** It enters an infinite loop, querying the `openai_responses` table every 10 seconds.
3.  **Filter:** It looks for records where `updated_at` is within the last 60 seconds and `latest_response_id` is present.
4.  **Fetch:** For every new record, it calls the OpenAI API (`/v1/responses/{id}`) to retrieve the input prompts and the final model output.
5.  **Merge:** It combines inputs and outputs into a single chronological list.
6.  **Save:** It writes this list to the `openai_chat_history` table.

## 📝 Logging

The script prints status updates to the console with emojis for easy readability:

  * 🔌 / ✅ Connection status
  * 🔔 Detection of new updates
  * ⏳ / ❌ API fetching status
  * 💾 / ✅ Database syncing status

## 🛑 Stopping the Bot

To stop the bot, simply press `Ctrl + C` in the terminal where it is running.