# OpenAI Chat History Sync Bot

A Python automation script that polls a PostgreSQL database for new OpenAI interactions, fetches the full conversation history (inputs and outputs) from the OpenAI API, and archives the data back into a dedicated history table.


  * **Automated Polling:** Checks the database every 10 seconds for recently updated records.
  * **Data Synchronization:** Fetches input items and generated outputs from OpenAI's `responses` endpoint.
  * **Database Upsert:** Inserts new history records or updates existing ones if the ID matches.


## 🗄️ Database Schema


### 1\. Source Table (`openai_responses`)

This is the table the bot watches for updates.

```sql
CREATE TABLE openai_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone TEXT NOT NULL,
  country TEXT,
  latest_response_id TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2\. Destination Table (`openai_chat_history`)

This is where the bot saves the synced chat history.

```sql
CREATE TABLE openai_chat_history (
  id UUID PRIMARY KEY REFERENCES openai_responses(id) ON DELETE CASCADE,
  phone TEXT NOT NULL,
  response_id TEXT,
  chat_history JSONB,
  fetched_at TIMESTAMPTZ DEFAULT NOW()
);
```


## 🔄 How It Works

1.  **Connect:** The script establishes a connection to the PostgreSQL database defined in the `.env` file.
2.  **Poll:** It enters an infinite loop, querying the `openai_responses` table every 10 seconds.
3.  **Filter:** It looks for records where `updated_at` is within the last 60 seconds and `latest_response_id` is present.
4.  **Fetch:** For every new record, it calls the OpenAI API (`/v1/responses/{id}`) to retrieve the input prompts and the final model output.
5.  **Merge:** It combines inputs and outputs into a single chronological list.
6.  **Save:** It writes this list to the `openai_chat_history` table.
