# TISS Healthcare API

Healthcare API for generating TISS XML files according to Brazilian standards.

## Features

- Health Insurance Management
- Provider & Professional Management  
- Patient Management
- Claims Processing
- TISS XML Generation with XSD Validation
- API Key Authentication
- Rate Limiting
- Comprehensive Request/Response Logging
- Enhanced Error Handling
- RESTful API with FastAPI
- MySQL Database with SQLAlchemy
- **Automatic API Documentation (Swagger UI)**
- **Comprehensive Unit Testing Suite**

## Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic + XML Schema (XSD)
- **Authentication**: API Key-based
- **Testing**: pytest + pytest-asyncio
- **Documentation**: FastAPI Auto-generated (OpenAPI/Swagger)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tiss-healthcare-api
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Edit .env with your database credentials
   # Required variables:
   # - DATABASE_URL
   # - API_KEYS
   # - SECRET_KEY
   ```

5. **Setup database**
   ```bash
   # Create MySQL database
   mysql -u root -p -e "CREATE DATABASE tiss_healthcare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   
   # Run database schema (optional - tables are auto-created)
   mysql -u root -p tiss_healthcare < database_schema.sql
   ```

6. **Start the application**
   ```bash
   python main.py
   ```

   The API will be available at:
   - **API Base URL**: http://localhost:8000
   - **Swagger UI Documentation**: http://localhost:8000/docs
   - **ReDoc Documentation**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

## API Documentation

### Interactive Documentation

The API provides automatic, interactive documentation through:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer
  - Test endpoints directly from the browser
  - Request/response examples
  - Authentication support

- **ReDoc**: http://localhost:8000/redoc
  - Clean, responsive documentation
  - Better for sharing with stakeholders

### API Endpoints

#### Health Insurance Management
- `GET /api/health-insurance/` - List health insurance companies
- `POST /api/health-insurance/` - Create new health insurance company
- `GET /api/health-insurance/{id}` - Get health insurance details
- `PUT /api/health-insurance/{id}` - Update health insurance company
- `DELETE /api/health-insurance/{id}` - Delete health insurance company

#### Provider Management
- `GET /api/providers/` - List healthcare providers
- `POST /api/providers/` - Create new provider
- `GET /api/providers/{id}` - Get provider details
- `PUT /api/providers/{id}` - Update provider
- `DELETE /api/providers/{id}` - Delete provider

#### Patient Management
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create new patient
- `GET /api/patients/{id}` - Get patient details
- `PUT /api/patients/{id}` - Update patient
- `DELETE /api/patients/{id}` - Delete patient

#### Claims Management
- `GET /api/claims/` - List claims
- `POST /api/claims/` - Create new claim
- `GET /api/claims/{id}` - Get claim details
- `PUT /api/claims/{id}` - Update claim
- `DELETE /api/claims/{id}` - Delete claim

#### TISS XML Operations
- `GET /api/claims/{id}/xml` - Generate TISS XML for claim
- `GET /api/claims/{id}/xml/download` - Download TISS XML file
- `POST /api/claims/validate-xml` - Validate XML content
- `GET /api/claims/{id}/validate` - Validate claim XML
- `GET /api/schema-info` - Get XSD schema information

### Authentication

All API endpoints require authentication via API key. Include your API key in the request headers:

```bash
# Using X-API-Key header (recommended)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/claims/

# Using Authorization header
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/claims/
```

### Request/Response Examples

#### Create a Patient
```bash
curl -X POST "http://localhost:8000/api/patients/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "cpf": "123.456.789-00",
    "birth_date": "1990-01-01",
    "address": "Rua das Flores, 123",
    "phone": "+55 11 99999-9999",
    "email": "joao.silva@email.com"
  }'
```

#### Generate TISS XML
```bash
curl -X GET "http://localhost:8000/api/claims/1/xml" \
  -H "X-API-Key: your-api-key"
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/tiss_healthcare
SQL_DEBUG=False

# Application Configuration
APP_NAME=TISS Healthcare API
APP_VERSION=1.0.0
DEBUG=True
SECRET_KEY=your-secret-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Configuration
ALLOWED_ORIGINS=["*"]

# XML Generation
XML_OUTPUT_DIR=generated_xml
TISS_VERSION=3.05.00

# Authentication
API_KEYS=your-api-key-1,your-api-key-2

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## Testing

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/ -m "not integration"

# XML generation tests
python -m pytest tests/ -m "xml"

# Authentication tests
python -m pytest tests/ -m "auth"

# Use the helper script
python run_tests.py
```

### Test Coverage
```bash
python -m pytest --cov=. --cov-report=html
```

## Project Structure

```
├── api/                    # API endpoints and routes
│   ├── routes/            # Route handlers
│   └── middleware/        # Custom middleware
├── models/                 # Database models
├── schemas/               # Pydantic schemas
├── services/              # Business logic
├── middleware/            # Authentication, logging, error handling
├── tests/                 # Comprehensive test suite
│   ├── test_auth.py       # Authentication tests
│   ├── test_claims.py     # Claims management tests
│   ├── test_patients.py   # Patient management tests
│   ├── test_xml.py        # XML generation tests
│   └── conftest.py        # Test fixtures
├── schemas/               # XSD schema files
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── pytest.ini           # pytest configuration
└── README.md            # This file
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed

2. **Database Connection Issues**
   - Verify MySQL is running
   - Check database credentials in `.env`
   - Ensure database exists

3. **Authentication Errors**
   - Verify API key is set in `.env`
   - Check API key format in request headers
   - Ensure rate limits haven't been exceeded

4. **XML Generation Issues**
   - Check XSD schema files in `schemas/` directory
   - Verify claim data is complete
   - Check file permissions for output directory

### Logs

The API provides comprehensive logging:
- Request/response logs
- Database operation logs
- XML generation logs
- Error logs with stack traces

Check logs in the configured log file or console output.

## Development

### Adding New Endpoints

1. Create route handler in `api/routes/`
2. Add Pydantic schemas in `schemas/`
3. Update database models if needed
4. Add tests in `tests/`
5. Update API documentation

### Running in Development Mode

```bash
# Enable debug mode
export DEBUG=True

# Start with auto-reload
python main.py
```

## Production Deployment

### Environment Setup
- Set `DEBUG=False`
- Use strong `SECRET_KEY`
- Configure production database
- Set appropriate CORS origins
- Enable HTTPS

### Process Management
```bash
# Using systemd (Linux)
sudo systemctl enable tiss-api
sudo systemctl start tiss-api

# Using supervisor
supervisorctl start tiss-api
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Add your license information here]

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test examples in `tests/`
- Check the troubleshooting section above 