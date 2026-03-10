from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Optional, Dict, Any, Union
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

class Bakery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    owner_user_id: str
    wc_url: Optional[str] = None
    wc_consumer_key: Optional[str] = None
    wc_consumer_secret: Optional[str] = None
    wc_webhook_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    bakery_id: Optional[str] = None
    google_sub: Optional[str] = None # NEW: Google Subject ID (Stable Identifier)
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None

class IngredientBase(BaseModel):
    name: str
    quantity: float
    unit: str
    reorder_threshold: float
    cost_per_unit: float

class IngredientCreate(IngredientBase):
    pass

class Ingredient(IngredientBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    bakery_id: str

class RecipeIngredient(BaseModel):
    name: str
    quantity_per_unit: float
    unit: str

class Recipe(BaseModel):
    model_config = {"populate_by_name": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    bakery_id: Optional[str] = None
    product_id: str
    product_name: str
    base_weight_kg: float = 1.0
    ingredients: List[RecipeIngredient] = []

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    sku: Optional[str] = None
    stock_status: Optional[str] = None
    source: Optional[str] = "manual"

    @validator('source', pre=True)
    def handle_none_source(cls, v):
        return v or "manual"

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    bakery_id: str

class OrderItemMeta(BaseModel):
    writing: Optional[str] = None
    flavor: Optional[str] = None
    allergens_note: Optional[str] = None
    weight_kg: Optional[float] = None
    raw: List[Dict[str, Any]] = []

class OrderItem(BaseModel):
    wc_item_id: Optional[str] = None
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    meta: OrderItemMeta = Field(default_factory=OrderItemMeta)

class OrderCustomer(BaseModel):
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    email: str = ""

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    wc_order_id: Optional[str] = None
    bakery_id: str
    customer: OrderCustomer = Field(default_factory=OrderCustomer)
    source: str = "woocommerce"
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus = OrderStatus.RECEIVED
    payment_status: str = "unpaid"
    archived: bool = False
    pickup_date: Optional[str] = None
    pickup_time: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    items: List[OrderItem]
    notes: Optional[str] = None
