from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# ===== Валидаторы =====
def validate_date_str(v: Optional[str]) -> Optional[str]:
    if v:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Формат даты: ГГГГ-ММ-ДД")
    return v


def validate_phone(v: str) -> str:
    cleaned = v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if not cleaned.isdigit():
        raise ValueError("Неверный формат телефона")
    return v


# ===== Инструменты =====
class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1)
    serial_number: Optional[str] = None
    purchase_price: float = Field(..., gt=0)
    purchase_date: Optional[str] = None
    status: str = "available"
    contractor_id: Optional[int] = None
    object_id: Optional[int] = None
    notes: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[str] = None
    status: Optional[str] = None
    contractor_id: Optional[int] = None
    object_id: Optional[int] = None
    notes: Optional[str] = None


class ToolResponse(BaseModel):
    id: int
    name: str
    serial_number: Optional[str] = None
    purchase_price: float
    purchase_date: Optional[str] = None
    status: str
    contractor_id: Optional[int] = None
    object_id: Optional[int] = None
    notes: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Объекты =====
class ObjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    client_phone: str = Field(..., min_length=5)
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    status: str = "Заявка"
    notes: Optional[str] = None
    @field_validator("client_phone")
    @classmethod
    def v_phone(cls, v): return validate_phone(v)


class ObjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    @field_validator("client_phone")
    @classmethod
    def v_phone(cls, v):
        if v is not None: return validate_phone(v)
        return v


# ===== Сметы =====
class EstimateItemResponse(BaseModel):
    id: int
    estimate_id: int
    name: str
    unit: str
    quantity: float
    price_per_unit: float
    total_price: float
    class Config:
        from_attributes = True


class EstimateResponse(BaseModel):
    id: int
    object_id: int
    name: str
    file_path: Optional[str] = None
    created_at: Optional[str] = None
    items: List[EstimateItemResponse] = []
    class Config:
        from_attributes = True


# ===== Подрядчики =====
class ContractorCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=5)
    specialization: Optional[str] = None
    notes: Optional[str] = None
    @field_validator("phone")
    @classmethod
    def v_phone(cls, v): return validate_phone(v)


class ContractorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    notes: Optional[str] = None


class ContractorResponse(BaseModel):
    id: int
    name: str
    phone: str
    specialization: Optional[str] = None
    notes: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Работы подрядчиков (старые) =====
class ContractorWorkCreate(BaseModel):
    object_id: int
    contractor_id: int
    estimate_item_id: Optional[int] = None
    description: str = ""
    unit: Optional[str] = None
    quantity: float = 0
    price_per_unit: float = 0
    total_price: float = 0
    advance: float = 0
    deadline: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None
    tool_ids: List[int] = []


class ContractorWorkUpdate(BaseModel):
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    total_price: Optional[float] = None
    advance: Optional[float] = None
    deadline: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    estimate_item_id: Optional[int] = None
    contractor_id: Optional[int] = None
    tool_ids: Optional[List[int]] = None


class ContractorWorkResponse(BaseModel):
    id: int
    object_id: int
    contractor_id: int
    estimate_item_id: Optional[int] = None
    description: str
    unit: Optional[str] = None
    quantity: float
    price_per_unit: float
    total_price: float
    advance: float
    deadline: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    contractor: Optional[ContractorResponse] = None
    tools: List[ToolResponse] = []
    class Config:
        from_attributes = True


# ===== Сметы подрядчика (с привязкой к estimate_item_id) =====
class ContractorEstimateItemCreate(BaseModel):
    estimate_item_id: Optional[int] = None
    name: str = Field(..., min_length=1)
    unit: str = Field(default="шт")
    quantity: float = Field(default=1, gt=0)
    price_per_unit: float = Field(default=0, ge=0)
    total_price: float = 0
    @field_validator("total_price")
    @classmethod
    def calc_total(cls, v, info):
        if v == 0:
            qty = info.data.get("quantity", 0)
            ppu = info.data.get("price_per_unit", 0)
            if qty and ppu: return round(qty * ppu, 2)
        return v


class ContractorEstimateCreate(BaseModel):
    object_id: int
    contractor_id: int
    name: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None
    items: List[ContractorEstimateItemCreate] = []


class ContractorEstimateUpdate(BaseModel):
    contractor_id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[ContractorEstimateItemCreate]] = None


class ContractorEstimateItemResponse(BaseModel):
    id: int
    estimate_id: int
    estimate_item_id: Optional[int] = None
    name: str
    unit: str
    quantity: float
    price_per_unit: float
    total_price: float
    client_price_per_unit: float = 0
    client_total_price: float = 0
    class Config:
        from_attributes = True


class ContractorEstimateResponse(BaseModel):
    id: int
    object_id: int
    contractor_id: int
    name: str
    status: str
    total_sum: float
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    paid_at: Optional[str] = None
    notes: Optional[str] = None
    items: List[ContractorEstimateItemResponse] = []
    contractor: Optional[ContractorResponse] = None
    class Config:
        from_attributes = True


# ===== Доп. работы (НОВОЕ) =====
class ExtraWorkCreate(BaseModel):
    object_id: int
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    contractor_name: Optional[str] = None
    quantity: float = 1
    unit: Optional[str] = None
    price: float = 0


class ExtraWorkUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contractor_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None


# ===== Оплаты подрядчикам (НОВОЕ) =====
class ContractorPaymentCreate(BaseModel):
    contractor_id: int
    object_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    date: Optional[str] = None


# ===== Материалы =====
class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    price_per_unit: float = Field(..., gt=0)
    description: Optional[str] = None


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    description: Optional[str] = None


class MaterialResponse(BaseModel):
    id: int
    name: str
    unit: str
    price_per_unit: float
    description: Optional[str] = None
    class Config:
        from_attributes = True


class MaterialPurchaseCreate(BaseModel):
    object_id: int
    material_id: int
    quantity: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    supplier: Optional[str] = None
    date: Optional[str] = None
    status: str = "delivered"
    notes: Optional[str] = None


class MaterialPurchaseUpdate(BaseModel):
    quantity: Optional[float] = None
    total_price: Optional[float] = None
    supplier: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class MaterialPurchaseResponse(BaseModel):
    id: int
    object_id: int
    material_id: int
    quantity: float
    total_price: float
    supplier: Optional[str] = None
    date: Optional[str] = None
    status: str
    notes: Optional[str] = None
    material: Optional[MaterialResponse] = None
    class Config:
        from_attributes = True


# ===== Платежи =====
class PaymentCreate(BaseModel):
    object_id: int
    amount: float = Field(..., gt=0)
    status: str = "pending"
    description: Optional[str] = None
    date: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    object_id: int
    amount: float
    status: str
    description: Optional[str] = None
    date: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Документы =====
class ObjectDocumentResponse(BaseModel):
    id: int
    object_id: int
    doc_type: str
    name: str
    file_path: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Коммуникации =====
class CommunicationCreate(BaseModel):
    object_id: int
    type: str
    description: str
    date: str
    @field_validator("date")
    @classmethod
    def v_date(cls, v): return validate_date_str(v)


class CommunicationResponse(BaseModel):
    id: int
    object_id: int
    type: str
    description: str
    date: str
    class Config:
        from_attributes = True


# ===== Задачи =====
class TaskCreate(BaseModel):
    object_id: int
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "To Do"
    deadline: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    object_id: int
    title: str
    description: Optional[str] = None
    status: str
    deadline: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Общие расходы =====
class GeneralExpenseCreate(BaseModel):
    category: str = Field(..., min_length=1)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    date: Optional[str] = None


class GeneralExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None


class GeneralExpenseResponse(BaseModel):
    id: int
    category: str
    description: Optional[str] = None
    amount: float
    date: Optional[str] = None
    class Config:
        from_attributes = True


# ===== Финплан =====
class FinancialPlanCreate(BaseModel):
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    planned_income: float = 0
    planned_expenses: float = 0
    notes: Optional[str] = None


# ===== Ответ объекта =====
class ObjectFinancials(BaseModel):
    object_id: int
    object_name: str
    client_name: str
    total_debit: float
    contractor_expenses: float
    material_expenses: float
    acts_total: float
    total_credit: float
    profit: float
    margin_percent: float


class ObjectFullResponse(BaseModel):
    id: int
    name: str
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    notes: Optional[str] = None
    estimates: List[EstimateResponse] = []
    payments: List[PaymentResponse] = []
    contractor_works: List[ContractorWorkResponse] = []
    material_purchases: List[MaterialPurchaseResponse] = []
    documents: List[ObjectDocumentResponse] = []
    communications: List[CommunicationResponse] = []
    tasks: List[TaskResponse] = []
    contractor_estimates: List[ContractorEstimateResponse] = []
    financials: Optional[ObjectFinancials] = None
    class Config:
        from_attributes = True


# ===== Акты выполненных работ =====
class ActCreate(BaseModel):
    object_id: int
    notes: Optional[str] = None


class ActUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ActItemResponse(BaseModel):
    name: str
    unit: str
    quantity: float
    price_per_unit: float  # Клиентская цена
    total_price: float
    source: str  # estimate или extra_work


class ActResponse(BaseModel):
    id: int
    object_id: int
    object_name: Optional[str] = None
    act_number: str
    created_at: str
    status: str
    total_sum: float
    notes: Optional[str] = None
    signed_at: Optional[str] = None
    items: List[ActItemResponse] = []
    class Config:
        from_attributes = True


class ActListItem(BaseModel):
    id: int
    act_number: str
    object_id: int
    object_name: str
    created_at: str
    status: str
    total_sum: float
    signed_at: Optional[str] = None
    class Config:
        from_attributes = True
# ===== ЗАЯВКИ НА РАБОТЫ =====
class WorkBatchItemCreate(BaseModel):
    estimate_item_id: Optional[int] = None
    name: str
    unit: str = "шт"
    quantity: float = 1

class WorkBatchCreate(BaseModel):
    object_id: int
    name: Optional[str] = None
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None
    items: List[WorkBatchItemCreate] = []
    contractor_ids: List[int] = []

class TelegramUserCreate(BaseModel):
    contractor_id: Optional[int] = None
    telegram_id: str
    telegram_username: Optional[str] = None
