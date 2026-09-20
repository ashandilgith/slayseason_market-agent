from langchain_core.tools import tool
from core.config import db_pool

@tool
def calculate_cac(tenant_id: str, start_date: str, end_date: str) -> str:
    """
    Calculate blended Customer Acquisition Cost (CAC).
    Requires start_date and end_date in YYYY-MM-DD format.
    """
    spend_sql = """
        SELECT COALESCE(SUM(spend), 0) AS total_spend
        FROM marketing_spend
        WHERE shop_id = %s AND date >= %s AND date <= %s;
    """
    customers_sql = """
        SELECT COUNT(DISTINCT id) AS new_customers
        FROM orders
        WHERE shop_id = %s AND created_at >= %s AND created_at <= %s;
    """
    
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(spend_sql, (tenant_id, start_date, end_date))
                total_spend = float(cur.fetchone()[0])
                
                cur.execute(customers_sql, (tenant_id, start_date, end_date))
                new_customers = int(cur.fetchone()[0])
                
        cac = round(total_spend / new_customers, 2) if new_customers > 0 else 0.0
        
        return (
            f"Total Marketing Spend: ${total_spend}\n"
            f"New Customers Acquired: {new_customers}\n"
            f"Blended CAC: ${cac}"
        )
    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"