from fastapi import APIRouter, Depends, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from typing import List, Optional
from pydantic import BaseModel
from dependencies import get_current_user_and_bakery
from services.pdf_service import generate_monthly_report_pdf
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])

class CustomerSummary(BaseModel):
    name: str
    email: Optional[str] = None
    total_spent: float
    last_order_date: Optional[str] = None
    orders_count: Optional[int] = 0
    source: str = "woocommerce"

@router.get("/", response_model=List[CustomerSummary])
async def get_customers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    synced_customers = await db.customers.find({"bakery_id": bakery_id}).sort("total_spent", -1).to_list(100)
    if synced_customers:
        return synced_customers

    pipeline = [
        {"$match": {"bakery_id": bakery_id}},
        {"$group": {
            "_id": "$customer_email",
            "name": {"$first": "$customer_name"},
            "email": {"$first": "$customer_email"},
            "total_spent": {"$sum": "$total_amount"},
            "last_order_date": {"$max": "$created_at"},
            "orders_count": {"$sum": 1},
            "source": {"$first": "$source"}
        }},
        {"$sort": {"last_order_date": -1}},
        {"$project": {
            "_id": 0,
            "name": 1,
            "email": 1,
            "total_spent": 1,
            "last_order_date": 1,
            "orders_count": 1,
            "source": 1
        }}
    ]
    
    customers = await db.orders.aggregate(pipeline).to_list(100)
    
    for c in customers:
        if c.get("last_order_date"):
            if hasattr(c["last_order_date"], 'isoformat'):
                c["last_order_date"] = c["last_order_date"].isoformat()
            else:
                c["last_order_date"] = str(c["last_order_date"])
            
    return customers


@router.get("/{email}/orders")
async def get_customer_orders(
    email: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    orders = await db.orders.find(
        {"bakery_id": bakery_id, "customer_email": email},
        {"_id": 1, "created_at": 1, "status": 1, "total_amount": 1, "items": 1, "notes": 1, "pickup_date": 1}
    ).sort("created_at", -1).to_list(100)
    
    for o in orders:
        if o.get("created_at") and hasattr(o["created_at"], 'isoformat'):
            o["created_at"] = o["created_at"].isoformat()
    
    return orders


@router.get("/report/monthly")
async def get_monthly_report(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year

    from datetime import timedelta
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    orders = await db.orders.find({
        "bakery_id": bakery_id,
        "created_at": {"$gte": start, "$lte": end},
        "status": {"$ne": "cancelled"}
    }).to_list(1000)

    total_revenue = sum(o.get("total_amount", 0) for o in orders)
    total_orders = len(orders)
    avg_order = total_revenue / total_orders if total_orders > 0 else 0

    # Prodotti più venduti
    product_counts = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("product_name", "Sconosciuto")
            qty = item.get("quantity", 1)
            product_counts[name] = product_counts.get(name, 0) + qty
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Clienti top
    customer_spent = {}
    for o in orders:
        email = o.get("customer_email", "")
        name = o.get("customer_name", "")
        customer_spent[email] = {
            "name": name,
            "email": email,
            "total": customer_spent.get(email, {}).get("total", 0) + o.get("total_amount", 0),
            "orders": customer_spent.get(email, {}).get("orders", 0) + 1
        }
    top_customers = sorted(customer_spent.values(), key=lambda x: x["total"], reverse=True)[:10]

    return {
        "month": month,
        "year": year,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order": avg_order,
        "top_products": [{"name": p[0], "quantity": p[1]} for p in top_products],
        "top_customers": top_customers,
    }


@router.get("/report/monthly/pdf")
async def download_monthly_report_pdf(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    now = datetime.now(timezone.utc)
    month = month or now.month
    year = year or now.year

    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    orders = await db.orders.find({
        "bakery_id": bakery_id,
        "created_at": {"$gte": start, "$lte": end},
        "status": {"$ne": "cancelled"}
    }).to_list(1000)

    # Calcola dati
    total_revenue = sum(o.get("total_amount", 0) for o in orders)
    total_orders = len(orders)
    avg_order = total_revenue / total_orders if total_orders > 0 else 0

    product_counts = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("product_name", "Sconosciuto")
            qty = item.get("quantity", 1)
            product_counts[name] = product_counts.get(name, 0) + qty
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    customer_spent = {}
    for o in orders:
        email = o.get("customer_email", "")
        name = o.get("customer_name", "")
        customer_spent[email] = {
            "name": name,
            "total": customer_spent.get(email, {}).get("total", 0) + o.get("total_amount", 0),
            "orders": customer_spent.get(email, {}).get("orders", 0) + 1
        }
    top_customers = sorted(customer_spent.values(), key=lambda x: x["total"], reverse=True)[:10]

    report_data = {
        "month": month,
        "year": year,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order": avg_order,
        "top_products": [{"name": p[0], "quantity": p[1]} for p in top_products],
        "top_customers": top_customers,
    }

    pdf_buffer = generate_monthly_report_pdf(report_data)

    import calendar as cal
    month_name = cal.month_name[month]
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{month_name}_{year}.pdf"}
    )
