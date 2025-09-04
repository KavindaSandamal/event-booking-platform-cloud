# Event Ticket Booking Platform

A microservices-based event ticket booking platform built with FastAPI, React, and modern cloud technologies.

## 🏗️ Architecture

### Microservices
- **Auth Service**: JWT authentication and user management
- **Catalog Service**: Event management and listing
- **Booking Service**: Booking creation and management
- **Payment Service**: Payment processing
- **Worker Service**: Background task processing
- **Frontend**: React SPA

### Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React 18 + Vite
- **Database**: PostgreSQL
- **Cache**: Redis
- **Message Queue**: RabbitMQ
- **Containerization**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)

### Running the Application

1. **Clone the repository**
   ```bash
   git clone https://github.com/KavindaSandamal/event-booking-platform.git
   cd event-booking-platform
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Auth Service: http://localhost:8001
   - Catalog Service: http://localhost:8002
   - Booking Service: http://localhost:8003
   - Payment Service: http://localhost:8004
   - pgAdmin: http://localhost:5050

## 📋 Demo Flow

1. **Register/Login**: Create an account or login
2. **Browse Events**: View available events in the catalog
3. **Book Event**: Select seats and create a booking
4. **Payment**: Complete payment for the booking
5. **View Bookings**: Check your booking history

## 🔧 Development

### Local Development Setup

1. **Start dependencies only**
   ```bash
   docker compose up -d postgres redis rabbitmq pgadmin
   ```

2. **Run services locally**
   ```bash
   # Auth Service
   cd services/auth
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001

   # Catalog Service
   cd services/catalog
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8002

   # Booking Service
   cd services/booking
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8003

   # Payment Service
   cd services/payment
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8004
   ```

3. **Run Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### API Documentation
- Auth Service: http://localhost:8001/docs
- Catalog Service: http://localhost:8002/docs
- Booking Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for password security
- **CORS Configuration**: Cross-origin security
- **Input Validation**: Pydantic schemas for data validation

## 🔄 Asynchronous Communication

- **RabbitMQ**: Message queue for background processing
- **Worker Service**: Handles async tasks like email notifications
- **Redis**: Caching and session management

## 📊 Database Design

- **PostgreSQL**: Primary relational database
- **Redis**: Caching layer and session storage
- **SQLAlchemy**: ORM for database operations

## 🐳 Containerization

- **Docker**: All services containerized
- **Docker Compose**: Local development orchestration
- **Multi-stage builds**: Optimized production images

## 📁 Project Structure

```
event-booking-platform/
├── services/
│   ├── auth/           # Authentication service
│   ├── catalog/        # Event catalog service
│   ├── booking/        # Booking management service
│   ├── payment/        # Payment processing service
│   └── worker/         # Background task worker
├── frontend/           # React frontend application
├── docker-compose.yml  # Service orchestration
├── env.example         # Environment variables template
└── README.md          # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
