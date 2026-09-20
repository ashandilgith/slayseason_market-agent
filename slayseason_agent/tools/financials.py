from langchain_core.tools import tool
from core.config import db_pool

@tool
def calculate_mer(tenant_id: str, start_date: str, end_date: str) -> str:
    """
    Use this tool to calculate Marketing Efficiency Ratio (MER) and Net Revenue.
    Requires start_date and end_date in YYYY-MM-DD format.
    """
    revenue_sql = """
        SELECT COALESCE(SUM(total_price - total_discounts), 0) AS net_revenue
        FROM orders
        WHERE shop_id = %s AND created_at >= %s AND created_at <= %s;
    """
    spend_sql = """
        SELECT COALESCE(SUM(spend), 0) AS meta_spend
        FROM marketing_spend
        WHERE shop_id = %s AND platform = 'Meta Ads' AND date >= %s AND date <= %s;
    """
    
    try:
        with db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(revenue_sql, (tenant_id, start_date, end_date))
                net_revenue = float(cur.fetchone()[0])
                
                cur.execute(spend_sql, (tenant_id, start_date, end_date))
                meta_spend = float(cur.fetchone()[0])
                
        # Calculate MER safely
        mer = round(net_revenue / meta_spend, 2) if meta_spend > 0 else 0.0
        
        return (
            f"RECONCILIATION SUCCESS:\n"
            f"Shopify Net Revenue: ${net_revenue}\n"
            f"Meta Ad Spend: ${meta_spend}\n"
            f"MER: {mer}x"
        )
    except Exception as e:
        return f"DATABASE ERROR (Data Unavailable): {str(e)}"

# Register tools
jarvis_tools = [calculate_mer]