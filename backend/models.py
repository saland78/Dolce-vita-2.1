from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
from enum import Enum

class OrderStatus(str, Enum):
    RECEIVED = "received"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    ADMIN = "admin"
    BAKER = "baker"
    SALES = "sales"
    CUSTOMER = "customer"

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Ingredient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    quantity: float
    unit: str
    reorder_threshold: float
    cost_per_unit: float

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    sku: Optional[str] = None
    stock_status: Optional[str] = None
    source: str = "manual"

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    customer_name: str
    customer_email: Optional[str] = None
    source: str = "woocommerce"
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus = OrderStatus.RECEIVED
    payment_status: str = "unpaid"
    archived: bool = False  # NEW FIELD for Archiving
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    items: List[OrderItem]
    notes: Optional[str] = None
