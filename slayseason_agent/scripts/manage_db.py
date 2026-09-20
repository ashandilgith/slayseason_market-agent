import argparse
import sys
import os
from dotenv import load_dotenv

# Load environment variables before importing anything else
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, "../.env"))

# Add parent directory to system path so we can import 'core' and 'sync'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config import db_pool

# Safely import the live sync connector if it exists
try:
    from sync.shopify_connector import sync_shopify_orders
except ImportError:
    def sync_shopify_orders():
        print("Error: sync/shopify_connector.py not found or not configured.")

# The designated ID for all synthetic data to prevent polluting real client metrics
SYNTHETIC_TENANT = "synthetic_shop_123"

def setup_tables():
    """Ensures canonical tables exist before any operations."""
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
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
        conn.commit()

def seed_synthetic():
    """Seeds synthetic data strictly under the SYNTHETIC_TENANT ID."""
    setup_tables()
    wipe_synthetic() # Clear old synthetic data to prevent duplicate stacking
    
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            # Seed 2026-01 Orders: $5,000 gross - $500 discount = $4,500 Net Revenue
            cur.execute("""
                INSERT INTO orders (id, shop_id, total_price, total_discounts, created_at)
                VALUES 
                ('syn_ord_1', %s, 3000.00, 250.00, '2026-01-10 10:00:00'),
                ('syn_ord_2', %s, 2000.00, 250.00, '2026-01-15 14:00:00');
            """, (SYNTHETIC_TENANT, SYNTHETIC_TENANT))
            
            # Seed 2026-01 Meta Spend: $1,500
            cur.execute("""
                INSERT INTO marketing_spend (shop_id, platform, spend, date)
                VALUES (%s, 'Meta Ads', 1500.00, '2026-01-15 10:00:00');
            """, (SYNTHETIC_TENANT,))
        conn.commit()
    print(f"[SUCCESS] Synthetic data seeded for tenant: {SYNTHETIC_TENANT}")

def wipe_synthetic():
    """Wipes ONLY data belonging to the synthetic tenant, preserving live client data."""
    setup_tables()
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orders WHERE shop_id = %s;", (SYNTHETIC_TENANT,))
            cur.execute("DELETE FROM marketing_spend WHERE shop_id = %s;", (SYNTHETIC_TENANT,))
        conn.commit()
    print(f"[SUCCESS] Wiped all synthetic data for {SYNTHETIC_TENANT}.")

def refresh_actual_data():
    """Wipes live client data (protecting synthetic data) and forces a fresh sync."""
    setup_tables()
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            # Delete everything EXCEPT the synthetic tenant
            cur.execute("DELETE FROM orders WHERE shop_id != %s;", (SYNTHETIC_TENANT,))
            cur.execute("DELETE FROM marketing_spend WHERE shop_id != %s;", (SYNTHETIC_TENANT,))
        conn.commit()
    
    print("[INFO] Live data wiped. Initiating fresh API sync...")
    sync_shopify_orders()
    print("[SUCCESS] Live data completely refreshed.")

def main():
    parser = argparse.ArgumentParser(description="SlaySeason Database Operations Manager")
    parser.add_argument("--sync", action="store_true", help="a) Run the live Shopify/Meta sync.")
    parser.add_argument("--seed", action="store_true", help="b) Seed synthetic dataset for testing.")
    parser.add_argument("--refresh", action="store_true", help="c) Wipe live data and perform a fresh sync.")
    parser.add_argument("--wipe-synthetic", action="store_true", help="d) Wipe all synthetic data.")
    
    args = parser.parse_args()
    
    if args.sync:
        setup_tables()
        sync_shopify_orders()
    elif args.seed:
        seed_synthetic()
    elif args.refresh:
        refresh_actual_data()
    elif args.wipe_synthetic:
        wipe_synthetic()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()