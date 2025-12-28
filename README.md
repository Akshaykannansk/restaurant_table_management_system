# Restaurant Live Table Order & Billing System

A robust, production-ready Django application for managing restaurant dine-in operations, featuring real-time floor plan updates, role-based access control, and a clean service-oriented architecture.


## 🚀 Key Features
- **Real-time Dashboard**: Live WebSocket updates for table status (Available -> Occupied -> Bill Requested).
- **Architecture**: Domain-Driven Design using strict Service Layer (`core/services.py`) and standard Django internals.
- **Robustness**:
    - **Celery & Redis**: Background tasks for kitchen notifications and automated table cleanup.
    - **Daphne**: ASGI Production Server for handling HTTP and WebSocket protocols concurrently.
    - **Self-Healing**: Automated `entrypoint.sh` for migrations, static collection, and data seeding on every boot.
- **Security**: strict Role-Based Access Control (RBAC) for Managers, Waiters, and Cashiers.
- **Reporting**: Daily sales reports and "Top 5 Items" dashboard for Managers.

## 🛠️ Architecture Setup

### Technology Stack
*   **Backend**: Python 3.10, Django 4.2
*   **API**: Django REST Framework (DRF)
*   **Real-time**: Django Channels 4.0, Daphne, Redis
*   **Database**: PostgreSQL 15
*   **Task Queue**: Celery 5.3 + Celery Beat
*   **Containerization**: Docker & Docker Compose

### Application Structure
*   `core/`: **The Heart**. Contains `models.py`, `services.py` (Business Logic), `tasks.py` (Celery), and `consumers.py` (WebSockets).
*   `web/`: **The Face**. Standard Django Class-Based Views (MVT) rendering HTML Templates.
*   `api/`: **The Bridge**. DRF Serializers and ViewSets for external integrations.
*   `templates/`: Jinja2-style Django templates with modern dark-mode CSS.
*   `static/`: Organized CSS and JS (including `dashboard.js` for WebSocket logic).

## ⚡ Quick Start (Docker)

The system is fully containerized. You do **not** need Python or Postgres installed locally.

1.  **Clone & Build**
    ```bash
    git clone <repository_url>
    cd restaurant_table_management_system
    docker compose up --build -d
    ```

    > **Note**: The `entrypoint.sh` script will automatically:
    > *   Collect static files.
    > *   Apply database migrations.
    > *   Seed initial data (Users, Tables, Menu Items).

2.  **Access the Application**
    *   **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
    *   **Django Admin**: [http://localhost:8000/admin](http://localhost:8000/admin)

3.  **Login Credentials (Demo)**

    | Role | Username | Password | Purpose |
    |------|----------|----------|---------|
    | **Manager** | `manager` | `password123` | View Reports, Admin Panel, Manage Menu |
    | **Waiter** | `waiter` | `password123` | Take Orders, Serve Food, Update Status |
    | **Cashier** | `cashier` | `password123` | Generate & Pay Bills |

## 🧪 Verification & Testing

To run the full integration test suite (simulating a full user flow from login to payment):

```bash
docker compose exec web python manage.py test core.tests
```

