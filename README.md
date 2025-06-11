# Bitcoin Price API

A FastAPI-based service that provides Bitcoin price data from CoinGecko API with caching and database storage.

## Features

- Real-time Bitcoin price fetching from CoinGecko API
- Historical price data storage in PostgreSQL
- Redis caching for improved performance
- Rate limiting handling
- Error handling for network issues and API errors
- Comprehensive test suite

## Design Decisions

### Why FastAPI?
- Modern, high-performance web framework for building APIs
- Built-in async support for better performance
- Automatic API documentation with OpenAPI/Swagger
- Type hints and validation with Pydantic
- Easy to test and maintain

### Database Choice: PostgreSQL
- **Why Relational over NoSQL:**
  - Structured data with clear relationships
  - ACID compliance for data integrity
  - Strong consistency requirements for financial data
  - Complex queries and time-based filtering
  - Mature ecosystem and tooling

- **Schema Design:**
  ```sql
  CREATE TABLE bitcoin_prices (
      id SERIAL PRIMARY KEY,
      price_usd DECIMAL NOT NULL,
      timestamp TIMESTAMP NOT NULL,
      source VARCHAR(50) NOT NULL
  );
  ```
  - `price_usd`: Decimal for precise price storage
  - `timestamp`: For time-series analysis
  - `source`: Track data origin
  - Indexes on timestamp for efficient range queries

### Caching Strategy
- **Redis as Cache Layer:**
  - In-memory performance
  - Built-in TTL support
  - Atomic operations
  - Pub/Sub for cache invalidation

- **TTL Configuration:**
  - Current price: 1 minute (frequent updates)
  - Historical prices: 5 minutes (less frequent changes)
  - Configurable via environment variables

### Error Handling Strategy
- Custom exception hierarchy
- Consistent error response format
- Proper HTTP status codes
- Detailed error messages
- Rate limit handling with Retry-After

## API Documentation

### Current Price Endpoint
```http
GET /api/v1/bitcoin/current-price
```

**Response:**
```json
{
    "price_usd": 50000.00,
    "timestamp": "2024-02-20T12:00:00Z",
    "source": "coingecko"
}
```

**Error Responses:**
```json
{
    "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```
```json
{
    "detail": "Network error: Connection refused"
}
```

### Historical Prices Endpoint
```http
GET /api/v1/bitcoin/historical-prices?start_time=2024-02-19T00:00:00Z&end_time=2024-02-20T00:00:00Z
```

**Response:**
```json
[
    {
        "price_usd": 50000.00,
        "timestamp": "2024-02-19T23:00:00Z",
        "source": "coingecko"
    },
    {
        "price_usd": 49900.00,
        "timestamp": "2024-02-19T22:00:00Z",
        "source": "coingecko"
    }
]
```

**Error Responses:**
```json
{
    "detail": "Invalid date format. Use ISO 8601 format."
}
```
```json
{
    "detail": "Database error: Connection refused"
}
```

## Environment Configuration

### Required Environment Variables
```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=bitcoin_prices
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=database_url

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# Cache TTL (in seconds)
CURRENT_PRICE_CACHE_TTL=60

# API Settings
API_RATE_LIMIT=50

# PGADMIN
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
```

### Environment-specific Configurations
- Development: Local development settings
- Test: Test environment with mock services
- Production: Production-ready configuration

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL
- Redis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a `.env` file in the project root with the required variables

3. Build and start the services:
```bash
cd docker
docker-compose up --build
```

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

### Integration Tests
- Database Integration:
  - Real database connection testing
  - Transaction handling
  - Data persistence verification
  - Schema migration testing
  - Connection pool management

- Cache Integration:
  - Redis connection testing
  - Cache hit/miss scenarios
  - Cache invalidation
  - TTL verification
  - Cache key generation

- API Integration:
  - End-to-end price fetching flow
  - Database storage verification
  - Cache interaction verification
  - Error propagation
  - Rate limit handling with real API

### Database Tests
- Connection error handling
- Transaction error handling
- Migration testing
- Data integrity verification

### API Tests
- Endpoint success scenarios
- Error handling
- Input validation
- Response format verification

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
- Docker Compose for isolated test environment
- PostgreSQL for test database
- Redis for test cache

### Test Environment
The test environment is configured with:
- Isolated PostgreSQL database
- Isolated Redis instance
- Automatic database migrations
- Clean database state between tests
- Configurable test settings via environment variables

### Test Coverage
Current test coverage includes:
- Core business logic
- Database operations
- Cache operations
- API endpoints
- Error handling
- Configuration management

## Error Handling

The API handles various error scenarios:

- `CoinGeckoRateLimitError`: When API rate limit is exceeded
- `CoinGeckoNetworkError`: When there are network issues
- `CoinGeckoInvalidResponseError`: When API response is invalid
- `CoinGeckoUnknownSymbolError`: When cryptocurrency symbol is unknown
- `DatabaseError`: When database operations fail