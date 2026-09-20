import os
import requests
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# Force dotenv to load from the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, "../.env"))

DB_URI = os.getenv("DATABASE_URL")
SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

pool = ConnectionPool(conninfo=DB_URI)

def sync_shopify_orders():
    """Fetches real orders from Shopify via GraphQL and syncs them to Postgres."""
    if not SHOP_DOMAIN or not ACCESS_TOKEN:
        raise ValueError("Missing Shopify credentials in .env")

    # Connect to the 2024-07 GraphQL endpoint
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to fetch the most recent 50 orders
    query = """
    {
      orders(first: 50, sortKey: CREATED_AT, reverse: true) {
        edges {
          node {
            id
            createdAt
            totalPriceSet { shopMoney { amount } }
            totalDiscountsSet { shopMoney { amount } }
          }
        }
      }
    }
    """
    
    print(f"Connecting to {SHOP_DOMAIN}...")
    response = requests.post(url, headers=headers, json={"query": query})
    
    if response.status_code != 200:
        print(f"Error fetching from Shopify: {response.text}")
        return

    data = response.json()
    orders = data.get("data", {}).get("orders", {}).get("edges", [])
    
    print(f"Successfully fetched {len(orders)} real orders. Writing to PostgreSQL...")
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # 1. Ensure the canonical tables exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id VARCHAR(255) PRIMARY KEY,
                    shop_id VARCHAR(100) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    total_discounts DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS marketing_spend (
                    id SERIAL PRIMARY KEY,
                    shop_id VARCHAR(100) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    spend DECIMAL(10,2) NOT NULL,
                    date TIMESTAMP NOT NULL
                );
            """)
            
            # 2. Upsert real Shopify orders
            for edge in orders:
                node = edge["node"]
                order_id = node["id"]
                created_at = node["createdAt"]
                total_price = float(node["totalPriceSet"]["shopMoney"]["amount"])
                total_discounts = float(node["totalDiscountsSet"]["shopMoney"]["amount"])
                
                cur.execute("""
                    INSERT INTO orders (id, shop_id, total_price, total_discounts, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE 
                    SET total_price = EXCLUDED.total_price,
                        total_discounts = EXCLUDED.total_discounts;
                """, (order_id, SHOP_DOMAIN, total_price, total_discounts, created_at))
            
            # 3. Optional: Insert a real Meta Ads spend block here when you have a Facebook Graph API token.
            # For now, we seed a placeholder spend so the agent's MER calculation (Revenue / Spend) does not fail.
            cur.execute("""
                INSERT INTO marketing_spend (shop_id, platform, spend, date)
                VALUES (%s, 'Meta Ads', 1500.00, CURRENT_TIMESTAMP)
            """, (SHOP_DOMAIN,))
                
        conn.commit()
    print("Sync complete! The intelligence layer is now grounded in real revenue data.")

if __name__ == "__main__":
    sync_shopify_orders()