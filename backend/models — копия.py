from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# ============================================================
# Many-to-many: работы ↔ инструменты
# ============================================================
work_tool_table = Table(
    "work_tool",
    Base.metadata,
    Column("work_id", Integer, ForeignKey("contractor_works.id", ondelete="CASCADE")),
    Column("tool_id", Integer, ForeignKey("tools.id", ondelete="CASCADE")),
)


# ============================================================
# OBJECTS (Объекты)
# ============================================================
class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    client_email = Column(String, default="")
    client_address = Column(String, default="")
    status = Column(String, default="Заявка")
    created_at = Column(String, default="")
    notes = Column(Text, default="")

    estimates = relationship("Estimate", back_populates="object", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="object", cascade="all, delete-orphan")
    contractor_works = relationship("ContractorWork", back_populates="object", cascade="all, delete-orphan")
    material_purchases = relationship("MaterialPurchase", back_populates="object", cascade="all, delete-orphan")
    documents = relationship("ObjectDocument", back_populates="object", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="object", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="object", cascade="all, delete-orphan")
    contractor_estimates = relationship("ContractorEstimate", back_populates="object", cascade="all, delete-orphan")
    extra_works = relationship("ExtraWork", back_populates="object", cascade="all, delete-orphan")
    material_requests = relationship("MaterialRequest", back_populates="object", cascade="all, delete-orphan")


# ============================================================
# ESTIMATES (Сметы объекта — из Excel, клиентские цены)
# ============================================================
class Estimate(Base):
    __tablename__ = "estimates"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, default="")
    file_path = Column(String, default="")
    created_at = Column(String, default="")

    object = relationship("Object", back_populates="estimates")
    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")


class EstimateItem(Base):
    __tablename__ = "estimate_items"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    quantity = Column(Float, default=0)
    price_per_unit = Column(Float, default=0)
    total_price = Column(Float, default=0)

    estimate = relationship("Estimate", back_populates="items")
    contractor_estimate_items = relationship("ContractorEstimateItem", back_populates="estimate_item")


# ============================================================
# PAYMENTS (Платежи клиентов)
# ============================================================
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")
    description = Column(Text, default="")
    date = Column(String, default="")

    object = relationship("Object", back_populates="payments")


# ============================================================
# CONTRACTORS (Подрядчики)
# ============================================================
class Contractor(Base):
    __tablename__ = "contractors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    specialization = Column(String, default="")
    notes = Column(Text, default="")

    works = relationship("ContractorWork", back_populates="contractor", cascade="all, delete-orphan")
    estimates = relationship("ContractorEstimate", back_populates="contractor", cascade="all, delete-orphan")
    contractor_payments = relationship("ContractorPayment", back_populates="contractor", cascade="all, delete-orphan")


# ============================================================
# CONTRACTOR WORKS (Работы подрядчиков — старые, для совместимости)
# ============================================================
class ContractorWork(Base):
    __tablename__ = "contractor_works"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    estimate_item_id = Column(Integer, ForeignKey("estimate_items.id", ondelete="SET NULL"), nullable=True)
    description = Column(String, default="")
    unit = Column(String, default="")
    quantity = Column(Float, default=0)
    price_per_unit = Column(Float, default=0)
    total_price = Column(Float, default=0)
    advance = Column(Float, default=0)
    deadline = Column(String, nullable=True)
    status = Column(String, default="planned")
    notes = Column(Text, default="")
    created_at = Column(String, default="")

    object = relationship("Object", back_populates="contractor_works")
    contractor = relationship("Contractor", back_populates="works")
    tools = relationship("Tool", secondary=work_tool_table, back_populates="works")


# ============================================================
# CONTRACTOR ESTIMATES (Сметы подрядчика — НОВОЕ: с привязкой к смете объекта)
# ============================================================
class ContractorEstimate(Base):
    __tablename__ = "contractor_estimates"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, default="")
    status = Column(String, default="planned")  # planned, in_progress, completed, paid
    total_sum = Column(Float, default=0)
    notes = Column(Text, default="")
    created_at = Column(String, default="")
    completed_at = Column(String, nullable=True)
    paid_at = Column(String, nullable=True)

    object = relationship("Object", back_populates="contractor_estimates")
    contractor = relationship("Contractor", back_populates="estimates")
    items = relationship("ContractorEstimateItem", back_populates="estimate", cascade="all, delete-orphan")


class ContractorEstimateItem(Base):
    __tablename__ = "contractor_estimate_items"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("contractor_estimates.id", ondelete="CASCADE"), nullable=False)
    estimate_item_id = Column(Integer, ForeignKey("estimate_items.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    quantity = Column(Float, default=0)
    price_per_unit = Column(Float, default=0)  # Цена подрядчика
    total_price = Column(Float, default=0)

    estimate = relationship("ContractorEstimate", back_populates="items")
    estimate_item = relationship("EstimateItem", back_populates="contractor_estimate_items")


# ============================================================
# CONTRACTOR PAYMENTS (Оплаты подрядчикам — НОВОЕ)
# ============================================================
class ContractorPayment(Base):
    __tablename__ = "contractor_payments"
    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(String, default="")
    date = Column(String, default="")

    contractor = relationship("Contractor", back_populates="contractor_payments")


# ============================================================
# EXTRA WORKS (Доп. работы вне сметы — НОВОЕ)
# ============================================================
class ExtraWork(Base):
    __tablename__ = "extra_works"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    contractor_name = Column(String, default="")
    quantity = Column(Float, default=1)
    unit = Column(String, default="")
    price = Column(Float, default=0)
    total_price = Column(Float, default=0)
    status = Column(String, default="completed")  # completed, paid
    created_at = Column(String, default="")
    paid_at = Column(String, nullable=True)

    object = relationship("Object", back_populates="extra_works")


# ============================================================
# MATERIALS (Справочник материалов)
# ============================================================
class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    price_per_unit = Column(Float, default=0)
    description = Column(Text, default="")

    purchases = relationship("MaterialPurchase", back_populates="material", cascade="all, delete-orphan")


# ============================================================
# MATERIAL PURCHASES (Закупки)
# ============================================================
class MaterialPurchase(Base):
    __tablename__ = "material_purchases"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, default=0)
    total_price = Column(Float, default=0)
    supplier = Column(String, default="")
    date = Column(String, default="")
    status = Column(String, default="ordered")
    notes = Column(Text, default="")

    object = relationship("Object", back_populates="material_purchases")
    material = relationship("Material", back_populates="purchases")


# ============================================================
# SUPPLIERS (Поставщики)
# ============================================================
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    email = Column(String, default="")
    address = Column(String, default="")
    notes = Column(Text, default="")
    created_at = Column(String, default="")

    price_files = relationship("SupplierPriceFile", back_populates="supplier", cascade="all, delete-orphan")
    material_requests = relationship("MaterialRequest", back_populates="supplier")


class SupplierPriceFile(Base):
    __tablename__ = "supplier_price_files"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, default="")
    file_path = Column(String, default="")
    description = Column(String, default="")
    uploaded_at = Column(String, default="")

    supplier = relationship("Supplier", back_populates="price_files")
    items = relationship("SupplierPriceItem", back_populates="price_file", cascade="all, delete-orphan")


class SupplierPriceItem(Base):
    __tablename__ = "supplier_price_items"
    id = Column(Integer, primary_key=True, index=True)
    price_file_id = Column(Integer, ForeignKey("supplier_price_files.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    price_per_unit = Column(Float, default=0)
    row_number = Column(Integer, nullable=True)

    price_file = relationship("SupplierPriceFile", back_populates="items")


# ============================================================
# MATERIAL REQUESTS (Заявки на материалы)
# ============================================================
class MaterialRequest(Base):
    __tablename__ = "material_requests"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, default="")
    status = Column(String, default="Черновик")
    total_sum = Column(Float, default=0)
    notes = Column(Text, default="")
    created_at = Column(String, default="")
    paid_at = Column(String, nullable=True)
    file_path = Column(String, nullable=True)

    object = relationship("Object", back_populates="material_requests")
    supplier = relationship("Supplier", back_populates="material_requests")
    items = relationship("MaterialRequestItem", back_populates="request", cascade="all, delete-orphan")


class MaterialRequestItem(Base):
    __tablename__ = "material_request_items"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("material_requests.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    quantity = Column(Float, default=0)
    price_per_unit = Column(Float, default=0)
    total_price = Column(Float, default=0)
    supplier_price_item_id = Column(Integer, nullable=True)

    request = relationship("MaterialRequest", back_populates="items")


# ============================================================
# TOOLS (Инструменты)
# ============================================================
class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    serial_number = Column(String, default="")
    purchase_price = Column(Float, default=0)
    purchase_date = Column(String, nullable=True)
    status = Column(String, default="available")
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, default="")

    works = relationship("ContractorWork", secondary=work_tool_table, back_populates="tools")


# ============================================================
# DOCUMENTS
# ============================================================
class ObjectDocument(Base):
    __tablename__ = "object_documents"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String, default="")
    name = Column(String, default="")
    file_path = Column(String, default="")
    created_at = Column(String, default="")

    object = relationship("Object", back_populates="documents")


# ============================================================
# COMMUNICATIONS
# ============================================================
class Communication(Base):
    __tablename__ = "communications"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, default="")
    description = Column(Text, default="")
    date = Column(String, default="")

    object = relationship("Object", back_populates="communications")


# ============================================================
# TASKS
# ============================================================
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="To Do")
    deadline = Column(String, nullable=True)
    created_at = Column(String, default="")

    object = relationship("Object", back_populates="tasks")


# ============================================================
# GENERAL EXPENSES
# ============================================================
class GeneralExpense(Base):
    __tablename__ = "general_expenses"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, default="")
    description = Column(Text, default="")
    amount = Column(Float, default=0)
    date = Column(String, default="")


# ============================================================
# FINANCIAL PLANS
# ============================================================
class FinancialPlan(Base):
    __tablename__ = "financial_plans"
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, nullable=False, unique=True)
    planned_income = Column(Float, default=0)
    planned_expenses = Column(Float, default=0)
    notes = Column(Text, default="")