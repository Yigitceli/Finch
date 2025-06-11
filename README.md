# Finch - Bitcoin Price Service

A robust microservice that fetches Bitcoin prices from CoinGecko API, stores them in a PostgreSQL database, and serves client requests through a Redis caching layer.

## 🚀 Features

- Real-time Bitcoin price fetching from CoinGecko API
- Efficient caching with Redis
- Persistent storage with PostgreSQL
- RESTful API endpoints
- Docker support
- Environment-based configuration
- Comprehensive error handling
- Rate limiting protection
- Comprehensive test suite

## 🏗 Architecture

### Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Container**: Docker
- **API**: CoinGecko Public API

### Design Decisions

1. **Database Choice (PostgreSQL)**
   - Relational database chosen for:
     - Strong data consistency
     - ACID compliance
     - Efficient time-series data querying
     - Built-in timestamp handling
     - Mature ecosystem and tooling
   - Schema designed for:
     - Efficient price history queries
     - Easy data aggregation
     - Future extensibility

2. **Caching Strategy**
   - Redis chosen for:
     - In-memory performance
     - Built-in TTL support
     - Atomic operations
     - Pub/Sub capabilities (for future scaling)
   - Cache TTLs:
     - Current price: 5 minutes
   - Cache invalidation on new price updates

3. **API Design**
   - RESTful principles
   - Clear error responses
   - Rate limiting protection
   - Proper HTTP status codes
   - Consistent response format

## 🛠 Setup

### Prerequisites

- Docker
- Docker Compose
- Python 3.9+ (for local development)

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=bitcoin_prices
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API
COINGECKO_API_URL=https://api.coingecko.com/api/v3
CURRENT_PRICE_CACHE_TTL=300
```

### Running with Docker

1. Build and start the containers:
```bash
docker-compose up -d
```

2. The service will be available at:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - PgAdmin: http://localhost:5050

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## 📚 API Documentation

### Endpoints

#### 1. Get Current Bitcoin Price
```http
GET /api/v1/bitcoin/current-price
```

Response:
```json
{
    "price_usd": 50000.0,
    "timestamp": "2024-03-19T14:30:00Z",
    "source": "coingecko"
}
```

#### 2. Get Bitcoin Price History
```http
GET /api/v1/bitcoin/price-history?start_time={start_time}&end_time={end_time}
```

Parameters:
- `start_time`: ISO 8601 timestamp (UTC)
- `end_time`: ISO 8601 timestamp (UTC)

Response:
```json
{
    "prices": [
        {
            "price_usd": 50000.0,
            "timestamp": "2024-03-19T14:30:00Z",
            "source": "coingecko"
        }
    ]
}
```

### Error Responses

```json
{
    "detail": "Error message"
}
```

Common HTTP Status Codes:
- 200: Success
- 400: Bad Request
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Testing

The project includes a comprehensive test suite covering various scenarios:

### Unit Tests
- Current Price Tests:
  - Successful price fetching
  - Rate limit handling
  - Network error handling
  - Invalid response handling

- Historical Prices Tests:
  - Empty result handling
  - Single record retrieval
  - Multiple records retrieval
  - Timezone-aware datetime handling

### Database Tests
- Connection error handling
- Transaction error handling

### API Tests
- Endpoint success scenarios
- Error handling
- Input validation

### Running Tests

To run the test suite:

```bash
cd docker
docker-compose -f docker-compose.test.yml up --build
```

The test suite uses:
- pytest for test execution
- pytest-asyncio for async test support
- pytest-cov for code coverage reporting
- Mock for mocking external dependencies

## Error Handling

The API handles various error scenarios:

- `CoinGeckoRateLimitError`: When API rate limit is exceeded
- `CoinGeckoNetworkError`: When there are network issues
- `CoinGeckoInvalidResponseError`: When API response is invalid
- `CoinGeckoUnknownSymbolError`: When cryptocurrency symbol is unknown
- `DatabaseError`: When database operations fail