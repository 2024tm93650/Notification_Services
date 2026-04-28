# Notification Service – Event Ticketing & Seat Reservation

A Django REST API microservice that sends booking confirmations, payment
status updates, e-tickets, and event-cancellation notices for the Event
Ticketing platform. It is one of the independent microservices in the
system (others: User, Catalog, Seating, Order, Payment).

## Features

- **REST API** for triggering and managing notifications (DRF ViewSet)
- **Multi-channel** delivery: Email (SMTP) and SMS (pluggable stub)
- **Database-per-service**: own PostgreSQL DB, no cross-service joins
- **Idempotent integration endpoint** other services call to notify users
- **Prometheus metrics** at `/metrics` (Golden Signals: counts, failures)
- **Structured logs** with correlation IDs (`X-Correlation-ID`) for tracing
- **Health endpoint** for Kubernetes liveness/readiness probes
- **Dockerized** + ready-to-apply Kubernetes manifests for Minikube
- **Admin panel** for browsing and resending notifications

## Technology Stack

| Layer | Tech |
|---|---|
| Framework | Django 4.2 + Django REST Framework 3.14 |
| Database | PostgreSQL (SQLite for local dev) |
| Metrics | django-prometheus / prometheus_client |
| Email | Django `send_mail` (Console / Mailtrap / any SMTP) |
| Container | Docker + docker-compose |
| Orchestration | Kubernetes (Minikube) |

## Project Structure

```
notification_service/
├── notification_service/        # Django project config
│   ├── settings.py              # All env-driven settings
│   ├── urls.py                  # /api, /admin, /health, /metrics
│   ├── wsgi.py / asgi.py
├── notifications/               # The app
│   ├── models.py                # Notification model (own DB)
│   ├── serializers.py
│   ├── views.py                 # ViewSet + custom actions
│   ├── urls.py
│   ├── admin.py
│   ├── middleware.py            # Correlation-ID propagation
│   ├── metrics.py               # Prometheus counters
│   ├── services/
│   │   ├── dispatcher.py        # orchestrates persist + send
│   │   ├── senders.py           # EmailSender, SmsSender
│   │   └── templates.py         # subject/body per notification type
│   └── tests.py
├── k8s/                         # Kubernetes manifests
│   ├── 00-namespace.yaml
│   ├── 10-config.yaml           # ConfigMap + Secret
│   ├── 20-database.yaml         # Postgres + PVC
│   └── 30-deployment.yaml       # Service Deployment + NodePort
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Installation (Local Development)

```bash
# 1. Clone and enter the service folder
cd notification_service

# 2. Create a virtualenv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations (uses SQLite by default)
python manage.py migrate

# 5. (Optional) create an admin user
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver 0.0.0.0:8005
```

Service is now available at `http://127.0.0.1:8005/`.

## Run with Docker Compose

```bash
docker compose up --build
```

This brings up:

- `notification-db` (PostgreSQL on host port `5435`)
- `notification-service` (Django on host port `8005`)

Validate:
```bash
docker ps
curl http://localhost:8005/health/
curl http://localhost:8005/metrics | head
```

## Deploy to Minikube

```bash
# 1. Point your Docker CLI at Minikube's daemon, then build the image inside it
eval $(minikube docker-env)
docker build -t notification-service:latest .

# 2. Apply manifests in order
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-config.yaml
kubectl apply -f k8s/20-database.yaml
kubectl apply -f k8s/30-deployment.yaml

# 3. Verify
kubectl get pods -n ticketing
kubectl get svc  -n ticketing
kubectl logs -n ticketing -l app=notification-service --tail=50

# 4. Hit it via NodePort
minikube service notification-service -n ticketing --url
```

## API Reference

Base URL (local): `http://127.0.0.1:8005/api/`

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/notifications/send/` | **Primary integration endpoint** — other services call this |
| `GET`  | `/api/notifications/` | List all notifications (paginated, filterable) |
| `GET`  | `/api/notifications/{id}/` | Retrieve one |
| `POST` | `/api/notifications/{id}/retry/` | Retry a failed notification |
| `GET`  | `/api/notifications/by_user/?user_id=42` | All notifications for a user |
| `GET`  | `/api/notifications/stats/` | Counts by status / type / channel |
| `GET`  | `/health/` | Liveness/readiness check |
| `GET`  | `/metrics` | Prometheus scrape endpoint |
| `GET`  | `/admin/` | Django admin |

### `POST /api/notifications/send/`

Other microservices (Order, Payment, Catalog) call this after a domain
event occurs. The service builds the subject/body from the templates,
persists the row, dispatches via the channel, and returns the result.

**Request:**
```http
POST /api/notifications/send/
Content-Type: application/json
X-Correlation-ID: 7c3b6f8a-0a1d-4e7f-95dc-2c4f2f0d11aa

{
  "user_id": 42,
  "order_id": 101,
  "event_id": 12,
  "type": "ORDER_CONFIRMED",
  "channel": "EMAIL",
  "recipient": "user@example.com",
  "payload": {
    "event_name": "Coldplay World Tour",
    "venue": "MG Stadium, Bengaluru",
    "event_date": "2026-05-15 19:30",
    "seats": ["A12", "A13"],
    "total": 5250,
    "order_id": 101
  }
}
```

**Response `201 Created`:**
```json
{
  "notification_id": 1,
  "user_id": 42,
  "order_id": 101,
  "event_id": 12,
  "type": "ORDER_CONFIRMED",
  "channel": "EMAIL",
  "recipient": "user@example.com",
  "subject": "Booking Confirmed: Coldplay World Tour",
  "message": "Hi,\n\nYour booking for Coldplay World Tour ...",
  "status": "SENT",
  "retry_count": 0,
  "error_message": "",
  "correlation_id": "7c3b6f8a-0a1d-4e7f-95dc-2c4f2f0d11aa",
  "created_at": "2026-04-28T10:30:00Z",
  "sent_at":    "2026-04-28T10:30:01Z"
}
```

### Supported `type` values
`ORDER_CONFIRMED`, `ORDER_CANCELLED`, `PAYMENT_FAILED`, `PAYMENT_REFUNDED`,
`EVENT_CANCELLED`, `SEAT_RESERVED`, `WELCOME`.

### Supported `channel` values
`EMAIL`, `SMS` (SMS is a logging stub — swap in Twilio/MSG91 in `senders.py`).

### Filtering & search

```
GET /api/notifications/?status=FAILED
GET /api/notifications/?type=ORDER_CONFIRMED&channel=EMAIL
GET /api/notifications/?user_id=42&ordering=-created_at
GET /api/notifications/?search=user@example.com
```

## Data Model

| Field | Type | Notes |
|---|---|---|
| `notification_id` | int (PK) | Auto |
| `user_id` | int | Reference to User Service (no FK) |
| `order_id` | int | Reference to Order Service (no FK) |
| `event_id` | int | Reference to Catalog Service (no FK) |
| `type` | enum | See list above |
| `channel` | enum | `EMAIL` / `SMS` |
| `recipient` | str | Email or phone |
| `subject` | str | Auto-built from template if omitted |
| `message` | text | Auto-built from template + payload |
| `status` | enum | `PENDING` / `SENT` / `FAILED` |
| `retry_count` | int | Incremented on each failure |
| `error_message` | text | Last error for failed sends |
| `correlation_id` | str | For distributed tracing |
| `created_at`, `updated_at`, `sent_at` | datetime | |

## Inter-Service Workflow (Buy Tickets)

The Notification Service participates as the final step:

```
Client -> Order Service       /v1/orders   (Idempotency-Key)
Order  -> Seating Service     reserve seats (15-min hold)
Order  -> Payment Service     /charge
Payment -> SUCCESS
Order  -> Seating Service     allocate
Order  -> Notification Service POST /api/notifications/send/
                                {type: ORDER_CONFIRMED, ...}
Notification -> SMTP/Email gateway
```

On failure paths, Order Service or Payment Service equally call
`/api/notifications/send/` with `ORDER_CANCELLED` or `PAYMENT_FAILED`.

## Observability

### Metrics (Prometheus)

| Metric | Labels |
|---|---|
| `notifications_received_total` | `type` |
| `notifications_sent_total` | `type`, `channel` |
| `notifications_failed_total` | `type`, `channel`, `reason` |

Plus all default `django_prometheus` HTTP/DB/cache metrics.

Scrape config example:
```yaml
- job_name: notification-service
  static_configs:
    - targets: ['notification-service.ticketing.svc:8000']
```

### Logging

Structured single-line JSON logs include `correlation_id`. Propagate
`X-Correlation-ID` from upstream services to enable end-to-end tracing.

```json
{"time":"2026-04-28 10:30:01","level":"INFO","logger":"notifications",
 "correlation_id":"7c3b6f8a-...","message":"Email dispatched to user@example.com"}
```

## Testing

```bash
python manage.py test
```

Tests cover the model, the `/send/` endpoint (success + failure path), and
the health endpoint. SMTP is mocked, so no external dependency is needed.

## Configuration (Environment Variables)

| Var | Default | Description |
|---|---|---|
| `SECRET_KEY` | dev-only | Django secret |
| `DEBUG` | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-separated |
| `DB_ENGINE` | (sqlite) | Set `postgres` to use Postgres |
| `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | — | Postgres |
| `EMAIL_BACKEND` | console | Use `django.core.mail.backends.smtp.EmailBackend` for real SMTP |
| `EMAIL_HOST` `EMAIL_PORT` `EMAIL_HOST_USER` `EMAIL_HOST_PASSWORD` `EMAIL_USE_TLS` | Mailtrap defaults | SMTP settings |
| `DEFAULT_FROM_EMAIL` | `no-reply@ticketing.local` | |

Copy `.env.example` to `.env` for local Docker runs.

## Sample cURL Calls

```bash
# Send a confirmation
curl -X POST http://localhost:8005/api/notifications/send/ \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: demo-001" \
  -d '{
    "user_id": 1, "order_id": 100, "type": "ORDER_CONFIRMED",
    "channel": "EMAIL", "recipient": "kalpesh@example.com",
    "payload": {"event_name":"Coldplay","seats":["A1","A2"],"total":5250,"order_id":100}
  }'

# List failed notifications
curl "http://localhost:8005/api/notifications/?status=FAILED"

# Retry a failed one
curl -X POST http://localhost:8005/api/notifications/3/retry/

# Stats
curl http://localhost:8005/api/notifications/stats/
```

## Owner

**Notification Service** – Kalpesh
Part of the Event Ticketing & Seat Reservation system (BITS Scalable Services assignment).
