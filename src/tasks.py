from src.celery_app import celery_app
import time

@celery_app.task
def optimize_price(product_ids, percentage_change):
    # This is a synchronous task
    print(f"Starting optimization for {len(product_ids)} products with change {percentage_change}")
    time.sleep(1)
    # Simulate work
    print("Optimization complete")
    return {"status": "success", "processed": len(product_ids)}
