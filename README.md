# AI Dropshipping Automation System

A comprehensive, AI-powered Shopify dropshipping automation system built with Python, FastAPI, and integrated with AutoDS and Shopify APIs.

## Overview

This system automates the entire dropshipping workflow:

- **Phase 1**: AI Store Creation via AutoDS AI Store Builder
- **Phase 2**: Automated Product Research & Catalog Management
- **Phase 3**: AI-Powered Pricing Optimization & Inventory Sync
- **Phase 4**: Content Generation, Email Flows, and AI Customer Support

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI DROPSHIPPING SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Shopify    │  │    AutoDS    │  │  AI/LLM API  │          │
│  │    API       │  │     API      │  │ (OpenAI/etc) │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│  ┌──────▼─────────────────▼─────────────────▼───────┐          │
│  │           Automation Engine (Python)              │          │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │          │
│  │  │  Store   │ │ Product  │ │ Pricing/Fulfill  │  │          │
│  │  │ Builder  │ │ Research │ │    Monitor       │  │          │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │          │
│  └─────────────────────┬────────────────────────────┘          │
│                        │                                        │
│  ┌─────────────────────▼────────────────────────────┐          │
│  │         Web Dashboard (FastAPI + HTML)           │          │
│  │  • Exception Queue  • Pending Approvals          │          │
│  │  • Product Mgmt     • Pricing Control            │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 1. AI Store Builder
- Create complete Shopify stores via AutoDS AI Store Builder
- Automated theme generation, branding, and page creation
- AI-generated content (About Us, FAQ, Shipping policies)

### 2. Product Research Automation
- Automated trending product discovery
- AI-powered product analysis against business constraints
- Automatic import with approval gates
- Daily research jobs

### 3. Pricing Optimization
- AI-suggests price changes based on performance metrics
- Constraint-based pricing (min margin, max change %)
- Automatic or approval-based price updates
- Full audit trail and rollback capability

### 4. Inventory & Fulfillment
- Real-time inventory synchronization
- Automatic stockout handling
- Exception queue for failed fulfillments
- Supplier performance monitoring

### 5. Dashboard & Monitoring
- Real-time statistics and KPIs
- Pending approvals queue
- Exception management
- System logs and audit trails

## Quick Start

### 1. Installation

```bash
# Clone or create the project
cd dropshipping_ai_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:

```env
# Shopify
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_access_token

# AutoDS
AUTODS_API_KEY=your_autods_api_key

# AI Provider
AI_API_KEY=your_openai_or_anthropic_key

# Optional: Notifications
NOTIFY_EMAIL_ENABLED=true
NOTIFY_SMTP_USER=your_email@gmail.com
NOTIFY_SMTP_PASSWORD=your_app_password
NOTIFY_SLACK_ENABLED=true
NOTIFY_SLACK_WEBHOOK_URL=your_webhook_url
```

### 3. Initialize Database

```python
from models.database import init_db
init_db()
```

### 4. Run the System

```bash
python main.py
```

The system will start on `http://localhost:8000`

## API Endpoints

### Store Management
- `POST /api/stores/create` - Create new AI store
- `GET /api/stores` - List all stores

### Product Research
- `POST /api/research/run` - Trigger product research
- `GET /api/research/jobs` - List research jobs
- `GET /api/products/pending` - Get pending products
- `POST /api/products/{id}/approve` - Approve product
- `POST /api/products/{id}/reject` - Reject product

### Pricing
- `POST /api/pricing/optimize` - Run pricing optimization
- `GET /api/pricing/pending` - Get pending price changes
- `POST /api/pricing/{id}/approve` - Approve price change
- `POST /api/pricing/{id}/reject` - Reject price change

### Fulfillment
- `GET /api/exceptions` - Get exception queue
- `POST /api/exceptions/{id}/resolve` - Resolve exception
- `POST /api/inventory/sync` - Trigger inventory sync

### AI Content
- `POST /api/ai/generate-content` - Generate AI content

## Scheduled Jobs

The system automatically runs these jobs:

| Job | Frequency | Description |
|-----|-----------|-------------|
| Product Research | Daily | Finds new products to import |
| Pricing Optimization | Daily | Adjusts prices based on performance |
| Inventory Sync | Every 30 min | Syncs stock levels |
| Fulfillment Check | Every 15 min | Detects failed orders |
| Supplier Analysis | Daily at 2 AM | Updates supplier metrics |
| Daily Summary | Daily at 8 AM | Sends reports |

## Configuration Options

### Business Rules (via environment variables)

```env
# AI Guardrails
AI_MAX_PRICE_CHANGE_PERCENT=10.0    # Max daily price change %
AI_MIN_PROFIT_MARGIN=30.0            # Minimum profit margin
AI_MAX_PRODUCTS_PER_DAY=5            # Max new products per day
AI_MIN_PRODUCT_RATING=4.0            # Minimum supplier rating
AI_MAX_SHIPPING_DAYS=14              # Max shipping time

# Pricing
STORE_BASE_MARKUP=2.5                # Cost multiplier
STORE_MIN_PRICE=15.0                 # Minimum selling price
STORE_MAX_PRICE=500.0                # Maximum selling price
STORE_PRICE_ROUNDING=0.99            # Round to .99

# Approval Gates
SYSTEM_REQUIRE_APPROVAL_FOR_IMPORT=false
SYSTEM_REQUIRE_APPROVAL_FOR_PRICE_CHANGES=false
```

## Directory Structure

```
dropshipping_ai_system/
├── api_clients/          # Shopify & AutoDS API clients
├── automation/           # Core automation workflows
│   ├── store_builder.py
│   ├── product_research.py
│   ├── pricing_engine.py
│   ├── fulfillment_monitor.py
│   └── scheduler.py
├── services/             # AI service, notifications
├── models/               # Database models
├── config/               # Configuration
├── web/                  # Dashboard templates
├── main.py              # FastAPI application
└── requirements.txt
```

## Web Dashboard

Access the dashboard at `http://localhost:8000`

- **Dashboard**: Overview, quick actions, create store
- **Products**: Pending approvals, product list, research history
- **Pricing**: Pending price changes, pricing rules
- **Exceptions**: Failed fulfillments, manual tools

## Extending the System

### Adding a New Automation Job

1. Create the automation logic in `automation/`
2. Add the job to `automation/scheduler.py`
3. Add API endpoints in `main.py` if needed

### Adding a New AI Capability

1. Add the method to `services/ai_service.py`
2. Create appropriate prompt templates
3. Add logging for audit trail

### Custom Integrations

The system is built with modularity in mind:
- Swap AI providers by updating `AI_PROVIDER` env var
- Add new notification channels in `services/notification_service.py`
- Extend database models in `models/database.py`

## Security Considerations

- All API keys are stored in environment variables
- Webhook signatures are validated
- Approval gates prevent unauthorized actions
- All AI decisions are logged for audit

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python -c "from models.database import init_db; init_db()"

CMD ["python", "main.py"]
```

### Using systemd

```ini
[Unit]
Description=AI Dropshipping Automation
After=network.target

[Service]
Type=simple
User=automation
WorkingDirectory=/opt/dropshipping_ai
Environment=PATH=/opt/dropshipping_ai/venv/bin
ExecStart=/opt/dropshipping_ai/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring & Alerts

The system sends notifications for:
- New fulfillment exceptions
- Supplier performance issues
- Daily summary reports

Configure via environment variables for email and Slack.

## License

MIT License - Feel free to use and modify for your own dropshipping operations.

## Support

For issues or questions:
1. Check the logs in the dashboard
2. Review AI decision logs in the database
3. Verify API credentials in `.env`
