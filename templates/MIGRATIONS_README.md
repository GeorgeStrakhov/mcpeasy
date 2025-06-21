# Custom Migrations Guide

This guide explains how to create and manage database migrations for your custom tools and resources.

## Overview

Custom tools and resources can define their own database models that are automatically discovered and included in Alembic migrations. This ensures your custom functionality has proper database schema management while maintaining compatibility with mcpeasy core.

## Quick Start

1. **Create models.py** in your custom tool/resource directory
2. **Define SQLAlchemy models** that inherit from mcpeasy's Base class
3. **Generate migration** using the enhanced migrate.sh script
4. **Deploy** with automatic migration execution

## Creating Custom Models

### 1. Add models.py to your custom tool/resource

```
your-org-tools/
├── tools/
│   └── invoice_generator/
│       ├── __init__.py
│       ├── tool.py
│       └── models.py          # Add this file
└── requirements.txt
```

### 2. Define your models

```python
# your-org-tools/tools/invoice_generator/models.py
from datetime import datetime
import uuid
from sqlalchemy import DateTime, Integer, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

class InvoiceData(Base):
    __tablename__ = "invoice_generator_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True)
    amount: Mapped[int] = mapped_column(Integer)  # Amount in cents
    status: Mapped[str] = mapped_column(String(50), default="pending")
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

## Generating Migrations

### For Custom Tools/Resources

Use the enhanced migrate.sh script with the `--custom` flag:

```bash
# Generate migration for custom tool/resource
./migrate.sh create "add invoice tables" --custom acme

# This creates a migration named: 20241221_140000_custom_acme_add_invoice_tables.py
```

### For Core Changes

Core mcpeasy changes use the standard command:

```bash
# Generate core migration
./migrate.sh create "add user preferences"

# This creates a migration named: 20241221_120000_core_add_user_preferences.py
```

## Migration Naming Convention

**Core migrations**: `YYYYMMDD_HHMMSS_core_description.py`
**Custom migrations**: `YYYYMMDD_HHMMSS_custom_org_description.py`

This ensures core migrations always run before custom migrations, preventing dependency issues.

## How It Works

### 1. Automatic Model Discovery

The migration system automatically discovers custom models:

```python
# In src/migrations/env.py
def discover_custom_models():
    # Scans src/custom_tools/*/models.py
    # Scans src/custom_resources/*/models.py
    # Imports all found models for Alembic
```

### 2. Model Registration

When you import a custom models.py file, SQLAlchemy automatically registers the models with the Base metadata, making them available for migration generation.

### 3. Migration Generation

Alembic sees all models (core + custom) and generates migrations that include:
- New tables for custom models
- Relationships to existing core tables
- Indexes and constraints
- Data migrations if needed

## Best Practices

### 1. **Table Naming Convention**

Use your organization/tool name as a prefix:

```python
# Good: Clear ownership and no conflicts
__tablename__ = "acme_invoice_data"
__tablename__ = "widgets_inc_reporting_cache"

# Bad: Could conflict with core or other custom tables
__tablename__ = "invoices"
__tablename__ = "cache"
```

### 2. **Link to Core Models**

Always link to core models when relevant:

```python
# Link to core client model
client_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), 
    ForeignKey("clients.id"), 
    nullable=False
)

# Add relationship for easy access
client: Mapped["Client"] = relationship("Client")
```

### 3. **Use JSONB for Flexibility**

Store flexible/evolving data in JSONB columns:

```python
# Flexible metadata storage
metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
```

### 4. **Include Timestamps**

Always include created_at and updated_at:

```python
created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(
    DateTime, 
    default=func.now(), 
    onupdate=func.now(), 
    nullable=False
)
```

### 5. **Add Meaningful Indexes**

Include indexes for common query patterns:

```python
__table_args__ = (
    Index('ix_invoice_client_id', 'client_id'),
    Index('ix_invoice_status', 'status'),
    Index('ix_invoice_created_at', 'created_at'),
)
```

## Common Patterns

### 1. **Data Storage Model**

```python
class ToolNameData(Base):
    """Main data storage for your tool"""
    __tablename__ = "toolname_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    external_id: Mapped[str] = mapped_column(String(255), nullable=True)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # ... other fields
```

### 2. **Audit/Logging Model**

```python
class ToolNameLog(Base):
    """Audit log for tool operations"""
    __tablename__ = "toolname_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    # ... other fields
```

### 3. **Configuration Model**

```python
class ToolNameConfig(Base):
    """Per-client configuration storage"""
    __tablename__ = "toolname_config"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), unique=True)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=True)
    # ... other config fields
```

### 4. **Resource Item Model**

```python
class ResourceNameItem(Base):
    """Storage for resource items"""
    __tablename__ = "resourcename_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # ... other fields
```

## Testing Migrations

### 1. **Test Migration Creation**

```bash
# Create test migration
./migrate.sh create "test custom models" --custom acme

# Check generated migration file
ls src/migrations/versions/*custom_acme*
```

### 2. **Test Migration Execution**

```bash
# Apply migrations
./migrate.sh upgrade

# Check migration status
./migrate.sh status
```

### 3. **Test Model Usage**

```python
# In your tool/resource code
from your_org.tools.invoice_generator.models import InvoiceData

async def create_invoice(client_id: str, amount: int):
    async with db.get_session() as session:
        invoice = InvoiceData(
            client_id=client_id,
            amount=amount,
            invoice_number=generate_invoice_number()
        )
        session.add(invoice)
        await session.commit()
        return invoice
```

## Troubleshooting

### Migration Discovery Issues

If your models aren't being discovered:

1. **Check file location**: Ensure `models.py` is in the correct location
2. **Check imports**: Ensure models inherit from `src.models.base.Base`
3. **Check syntax**: Ensure no Python syntax errors in models.py
4. **Check logs**: Look for discovery messages when running migrations

### Migration Conflicts

If you get migration conflicts:

1. **Check naming**: Ensure custom migrations use `--custom org_name`
2. **Check timing**: Ensure core migrations are created before custom ones
3. **Check dependencies**: Ensure custom models only reference existing core tables

### Database Issues

If migrations fail:

1. **Check database connection**: Ensure DATABASE_URL is correct
2. **Check permissions**: Ensure database user has CREATE TABLE permissions
3. **Check constraints**: Ensure foreign key references are valid

## Docker Integration

Custom migrations work automatically with Docker:

1. **Models discovered**: Custom models.py files are automatically found
2. **Migrations generated**: Use `./migrate.sh create --custom` in development
3. **Migrations applied**: Docker startup automatically runs `alembic upgrade head`

## Security Considerations

### 1. **Sensitive Data**

Never store sensitive data in plain text:

```python
# Good: Store encrypted
api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=True)

# Bad: Store plain text
api_key: Mapped[str] = mapped_column(String(255), nullable=True)
```

### 2. **Data Isolation**

Ensure proper client isolation:

```python
# Always link to client_id for multi-tenancy
client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))

# Add client-aware queries
async def get_client_invoices(client_id: str):
    return await session.execute(
        select(InvoiceData).where(InvoiceData.client_id == client_id)
    )
```

### 3. **Access Control**

Implement proper access control in your tools/resources:

```python
# In your tool
async def execute(self, arguments: Dict[str, Any], config: Dict[str, Any] = None) -> ToolResult:
    # Get client from context
    client_id = self._context.get('client', {}).get('id')
    
    # Only access data for this client
    data = await get_client_data(client_id)
```

This migration system ensures your custom tools and resources have proper database schema management while maintaining security and compatibility with mcpeasy core.