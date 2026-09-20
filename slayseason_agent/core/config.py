import os
from psycopg_pool import ConnectionPool
from langchain_openai import ChatOpenAI

# Load the SlaySeason canonical database URI
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/slayseason")

# Initialize a thread-safe connection pool for our data tools
db_pool = ConnectionPool(conninfo=DB_URI)

# Initialize the flexible LLM (OpenAI as requested)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0 # Temperature 0 enforces analytical precision over creativity
)