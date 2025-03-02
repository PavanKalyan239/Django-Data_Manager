# DataManager

**DataManager** is a Django REST Framework (DRF) application designed to manage users, accounts, and asynchronous data synchronization to external endpoints. It provides a secure, scalable API with features like user authentication, account management, data handling, advanced log querying, rate limiting, and performance optimization using Celery and Redis.

## Table of Contents
- [Features](#features)
  - [Users App](#users-app)
  - [Accounts App](#accounts-app)
  - [Destinations App](#destinations-app)
- [Why Celery and Redis?](#why-celery-and-redis)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Celery and Redis Locally](#running-celery-and-redis-locally)
- [Executing the Code](#executing-the-code)
- [API Endpoints](#api-endpoints)
- [Swagger API Documentation](#swagger-api-documentation)
- [Implementation Notes](#implementation-notes)

## Features

### Users App
The `users` app manages user authentication, registration, and invitations.

- **User Registration:**
  - Endpoint: `POST /users/register/`
  - Registers a new user with an email and password, creating an associated account and assigning the "Admin" role.
  - Example: `{"email": "user@example.com", "password": "pass123"}`
- **User Login:**
  - Endpoint: `POST /users/login/`
  - Authenticates a user and returns a token for API access.
  - Example: `{"email": "user@example.com", "password": "pass123"}`
- **User Logout:**
  - Endpoint: `POST /users/logout/`
  - Invalidates the user’s token (requires authentication).
- **Invite Users:**
  - Endpoint: `POST /users/invite/`
  - Allows admins to invite users to an account, assigning a role (e.g., "Normal user").
  - Example: `{"email": "newuser@example.com", "account_id": 1}`
- **User Management:**
  - List: `GET /users/` (admins see all, others see self; filterable by email).
  - Update: `PUT /users/<id>/` (admins edit any, users edit self).

### Accounts App
The `accounts` app handles account creation and membership management.

- **Account Management:**
  - Create/List: `GET/POST /accounts/` (admin-only).
    - Example POST: `{"name": "My Account"}`
  - Update/Delete: `GET/PUT/DELETE /accounts/<id>/` (admins manage, members view).
- **Membership Management:**
  - Endpoint: `GET/POST /accounts/<account_id>/members/` (admin-only).
    - Example POST: `{"user": 2, "role": 2}` (adds user ID 2 as "Normal user").
  - Roles: "Admin" (full control), "Normal user" (limited access).

### Destinations App
The `destinations` app manages data synchronization, destinations, and logs.

- **Data Handler:**
  - Endpoint: `POST /server/incoming_data/`
  - Receives JSON data, validates `CL-X-TOKEN` (account-specific UUID), and sends it to destinations asynchronously via Celery.
  - Rate-limited to 5 requests/second per user using DRF throttling.
  - Example: `{"key": "value"}` with headers `CL-X-TOKEN` and `Authorization`.
- **Destination Management:**
  - Create/List: `GET/POST /accounts/<account_id>/destinations/` (admins create, members list).
    - Example POST: `{"url": "https://httpbin.org/post", "http_method": "POST", "headers": {"Content-Type": "application/json"}}`
  - Update/Delete: `GET/PUT/DELETE /destinations/<id>/` (admins manage, members view/update).
- **Log Management:**
  - Endpoint: `GET /accounts/<account_id>/logs/`
  - Retrieves logs with advanced filtering: `status`, `event_id`, `destination_id`, `received_timestamp__gte`, `received_timestamp__lte`.
  - Example: `/accounts/5/logs/?status=success&destination_id=1`
  - Cached for 5 minutes with dynamic keys for performance.

## Why Celery and Redis?
- **Celery:**
  - **Purpose:** Handles asynchronous data sending to destinations, decoupling it from the API response cycle.
  - **Why:** Ensures fast API responses (e.g., `/server/incoming_data/` returns immediately), supports retries on failure, and scales for multiple destinations.
  - **Implementation:** Uses `send_to_destination` task to process HTTP requests to destination URLs.
- **Redis:**
  - **Purpose:** Serves as Celery’s message broker (task queue) and Django’s cache backend.
  - **Why:** Provides fast, in-memory storage for task queuing and caching querysets (e.g., logs, destinations), boosting performance.
  - **Implementation:** Configured as `CELERY_BROKER_URL` and `CACHES['default']`.

## Setup Instructions

### Prerequisites
- **Python 3.8+**
- **Redis Server**: Download from [redis.io](https://redis.io/docs/install/install-redis/) or use a Windows port like Memurai from [memurai.com](https://www.memurai.com/). Run via CMD.
- **Git** (optional)
- **Virtual Environment** (recommended)

### Installation
1. **Clone or Download:**
   ```bash
   git clone https://github.com/PavanKalyan239/Django.git
   cd data_manager
   ```

## Running Celery and Redis Locally

### Start Redis Server:
```bash
redis-server
```
Verify Redis is running:
```bash
redis-cli ping  # Should return "PONG"
```

### Run Celery Worker:
```bash
celery -A data_manager worker -l info --pool=solo
```
(Use `--pool=solo` to ensure compatibility with Windows.)

### Start Django Server:
```bash
python manage.py runserver
```

## Executing the Code

### Register a User:
```bash
curl -X POST -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"password\":\"pass123\"}" http://127.0.0.1:8000/users/register/
```

### Login (Get Token):
```bash
curl -X POST -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\",\"password\":\"pass123\"}" http://127.0.0.1:8000/users/login/
```
Copy the token and id from the response.

### Get CL-X-TOKEN (App Secret Token):
```bash
curl -X GET -H "Authorization: Token <your-token>" http://127.0.0.1:8000/accounts/{id}/
```
Copy the app_secret_token(CL-X-TOKEN) from the response

### Send Data:
```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Token <your-token>" -H "CL-X-TOKEN: <app_secret_token>" -d "{\"key\":\"value\"}" http://127.0.0.1:8000/server/incoming_data/
```
_Get `<app_secret_token>` from the Account model (e.g., via shell: `Account.objects.get(id=5).app_secret_token`)._

## API Endpoints

### Users:
- `POST /users/register/` - Register a new user.
- `POST /users/login/` - Login and get token.
- `POST /users/logout/` - Logout (authenticated).
- `POST /users/invite/` - Invite user to account (admin).
- `GET /users/` - List users (admin or self).
- `PUT /users/<id>/` - Update user (admin or self).

### Accounts:
- `GET/POST /accounts/` - List/create accounts (admin).
- `GET/PUT/DELETE /accounts/<id>/` - View/update/delete account (admin or member).
- `GET/POST /accounts/<account_id>/members/` - List/add members (admin).

### Swagger API Documentation
For detailed API documentation, visit:
[Swagger Docs](http://127.0.0.1:8000/api/docs/#/)


### Implementation Notes
- **Apps:**  
  - `users`, `accounts`, and `destinations` modularize functionality.  
- **Authentication:**  
  - Token-based authentication using `rest_framework.authtoken`.  
- **Asynchronous Tasks:**  
  - Celery with Redis handles non-blocking data sync to external destinations.  
- **Caching:**  
  - Redis-backed caching optimizes performance with dynamic key invalidation.  
- **Filtering:**  
  - Advanced log queries with `status`, `event_id`, `destination_id`, and timestamp filters.  
- **Rate Limiting:**  
  - DRF `UserRateThrottle` limits requests to **5 per second per user**.  
- **API Documentation:**  
  - Auto-generated via `drf-spectacular` at `/api/docs/`.  
- **Development Setup:**  
  - Built with iterative optimization, Windows-compatible Celery (`--pool=solo`). 

---
