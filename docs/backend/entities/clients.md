# Clients API - Product Requirements Document

## Overview

The Clients API is a core component of the SWiS case management system that provides comprehensive client lifecycle management for community services organizations serving NZ children and families. This API enables practitioners to manage client information, track client statuses, and integrate with the broader case management workflow.

## Business Context

### Purpose
- Enable secure storage and retrieval of client personal information
- Support client intake and onboarding processes
- Facilitate client search and matching capabilities
- Integrate with referral and service episode management
- Maintain compliance with NZ privacy and healthcare regulations

### Key Stakeholders
- **Primary Users**: Social workers, counsellors, case managers
- **Secondary Users**: Administrative staff, supervisors
- **System Integrations**: Referral system, episode management, assessments

## Data Architecture

### Core Client Entity
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    status_code VARCHAR(50) NOT NULL,
    primary_language_code VARCHAR(10),
    pronoun_code VARCHAR(20),
    sex VARCHAR(10), -- 'male', 'female', 'intersex', 'unknown'
    interpreter_needed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    
    CONSTRAINT fk_client_status 
        FOREIGN KEY (status_code) REFERENCES client_statuses(code),
    CONSTRAINT fk_client_language 
        FOREIGN KEY (primary_language_code) REFERENCES languages(code),
    CONSTRAINT fk_client_pronoun 
        FOREIGN KEY (pronoun_code) REFERENCES pronouns(code),
    CONSTRAINT fk_client_sex 
        FOREIGN KEY (sex) REFERENCES sex_values(code)
);

-- Performance indexes
CREATE INDEX idx_clients_name ON clients(last_name, first_name);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_phone ON clients(phone);
CREATE INDEX idx_clients_status ON clients(status_code);
CREATE INDEX idx_clients_dob ON clients(date_of_birth);
CREATE INDEX idx_clients_search ON clients USING gin(to_tsvector('english', first_name || ' ' || last_name || ' ' || COALESCE(email, '')));
```

### Reference Data Tables
```sql
-- Client status reference
CREATE TABLE client_statuses (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER,
    color_hex VARCHAR(7)
);

-- Language reference  
CREATE TABLE languages (
    code VARCHAR(10) PRIMARY KEY, -- ISO 639-1 + region: 'en-NZ', 'mi-NZ'
    name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER
);

-- Pronoun reference
CREATE TABLE pronouns (
    code VARCHAR(20) PRIMARY KEY, -- 'he-him', 'she-her', 'they-them'
    display_text VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER
);

-- Sex reference
CREATE TABLE sex_values (
    code VARCHAR(10) PRIMARY KEY, -- 'male', 'female', 'intersex', 'unknown'
    name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER
);
```

## API Specification

### Base URL
`https://api.swis.com/v1/` (Production)
`http://localhost:8000/api/v1/` (Development)

### Authentication
All endpoints require JWT Bearer token authentication:
```
Authorization: Bearer <jwt_token>
```

### Endpoints Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/clients/` | List clients with filtering/search |
| POST | `/clients/` | Create new client |
| GET | `/clients/{id}` | Get client details |
| PATCH | `/clients/{id}` | Update client (partial) |
| PUT | `/clients/{id}` | Update client (full) |
| DELETE | `/clients/{id}` | Soft delete client |
| GET | `/clients/search` | Advanced client search |
| GET | `/reference-data/` | Get all dropdown data |

### 1. List Clients

**Endpoint**: `GET /clients/`

**Query Parameters**:
- `status`: Filter by status code (e.g., `active`, `inactive`)
- `language`: Filter by language code (e.g., `en-NZ`, `mi-NZ`)
- `interpreter_needed`: Filter by boolean (`true`, `false`)
- `created_since`: ISO date - clients created since date
- `updated_since`: ISO date - clients updated since date
- `limit`: Pagination limit (default: 50, max: 200)
- `offset`: Pagination offset (default: 0)
- `ordering`: Sort field (`first_name`, `last_name`, `created_at`, `-updated_at`)

**Response Example**:
```json
{
  "count": 1247,
  "next": "/api/v1/clients/?limit=50&offset=50",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "Jane",
      "last_name": "Smith",
      "date_of_birth": "1985-05-15",
      "email": "jane.smith@example.com",
      "phone": "+64 21 123 4567",
      "status": {
        "code": "active",
        "name": "Active"
      },
      "primary_language": {
        "code": "en-NZ",
        "name": "English (New Zealand)"
      },
      "pronoun": {
        "code": "she-her",
        "display_text": "She/Her"
      },
      "sex": {
        "code": "female",
        "name": "Female"
      },
      "interpreter_needed": false,
      "full_name": "Jane Smith",
      "created_at": "2024-01-15T08:30:00Z",
      "updated_at": "2024-03-20T14:22:00Z"
    }
  ]
}
```

### 2. Create Client

**Endpoint**: `POST /clients/`

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-03-15",
  "email": "john.doe@example.com",
  "phone": "+64 9 555 0123",
  "status_code": "active",
  "primary_language_code": "en-NZ",
  "pronoun_code": "he-him",
  "sex": "male",
  "interpreter_needed": false
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-03-15",
  "email": "john.doe@example.com",
  "phone": "+64 9 555 0123",
  "status": {
    "code": "active",
    "name": "Active"
  },
  "primary_language": {
    "code": "en-NZ",
    "name": "English (New Zealand)"
  },
  "pronoun": {
    "code": "he-him",
    "display_text": "He/Him"
  },
  "sex": {
    "code": "male",
    "name": "Male"
  },
  "interpreter_needed": false,
  "full_name": "John Doe",
  "created_at": "2024-12-15T09:15:30Z",
  "updated_at": "2024-12-15T09:15:30Z"
}
```

### 3. Get Client Details

**Endpoint**: `GET /clients/{id}`

**Response Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-05-15",
  "email": "jane.smith@example.com",
  "phone": "+64 21 123 4567",
  "status": {
    "code": "active",
    "name": "Active",
    "description": "Client is currently receiving services"
  },
  "primary_language": {
    "code": "en-NZ",
    "name": "English (New Zealand)",
    "native_name": "English"
  },
  "pronoun": {
    "code": "she-her",
    "display_text": "She/Her"
  },
  "sex": {
    "code": "female",
    "name": "Female"
  },
  "interpreter_needed": false,
  "full_name": "Jane Smith",
  "created_at": "2024-01-15T08:30:00Z",
  "updated_at": "2024-03-20T14:22:00Z",
  "created_by": {
    "id": "user-123",
    "name": "Sarah Wilson"
  },
  "updated_by": {
    "id": "user-456", 
    "name": "Mike Chen"
  }
}
```

### 4. Update Client

**Endpoint**: `PATCH /clients/{id}` (partial update)
**Endpoint**: `PUT /clients/{id}` (full update)

**PATCH Request Example**:
```json
{
  "email": "jane.smith.updated@example.com",
  "phone": "+64 21 987 6543",
  "sex": "female"
}
```

**Response** (200 OK): Returns updated client object

### 5. Delete Client

**Endpoint**: `DELETE /clients/{id}`

**Response**: 204 No Content

**Note**: This performs a soft delete by setting `status_code` to `deleted` and `deleted_at` timestamp.

### 6. Search Clients

**Endpoint**: `GET /clients/search`

**Query Parameters**:
- `q`: Search term (searches first_name, last_name, email, phone)
- `status`: Filter by status code
- `language`: Filter by language code
- `interpreter_needed`: Filter by boolean
- `age_min`: Minimum age in years
- `age_max`: Maximum age in years
- `limit`: Results limit (default: 20, max: 100)

**Response Example**:
```json
{
  "query": "jane smith",
  "count": 3,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "phone": "+64 21 123 4567",
      "status": {
        "code": "active",
        "name": "Active"
      },
      "full_name": "Jane Smith",
      "match_score": 0.95
    }
  ]
}
```

### 7. Reference Data

**Endpoint**: `GET /reference-data/`

**Response Example**:
```json
{
  "client_statuses": [
    {
      "code": "active",
      "name": "Active",
      "description": "Currently receiving services"
    },
    {
      "code": "inactive",
      "name": "Inactive", 
      "description": "Not currently active"
    }
  ],
  "languages": [
    {
      "code": "en-NZ",
      "name": "English (New Zealand)",
      "native_name": "English"
    },
    {
      "code": "mi-NZ",
      "name": "Te Reo Māori",
      "native_name": "Te Reo Māori"
    }
  ],
  "pronouns": [
    {
      "code": "he-him",
      "display_text": "He/Him"
    },
    {
      "code": "she-her",
      "display_text": "She/Her"
    },
    {
      "code": "they-them",
      "display_text": "They/Them"
    }
  ],
  "sex_values": [
    {
      "code": "male",
      "name": "Male"
    },
    {
      "code": "female",
      "name": "Female"
    },
    {
      "code": "intersex",
      "name": "Intersex"
    },
    {
      "code": "unknown",
      "name": "Unknown"
    }
  ],
  "cache_expires_at": "2024-12-15T15:30:00Z"
}
```

## Request/Response Schemas

### Client Input Schema (POST/PUT/PATCH)
```json
{
  "type": "object",
  "properties": {
    "first_name": {"type": "string", "maxLength": 100, "minLength": 1},
    "last_name": {"type": "string", "maxLength": 100, "minLength": 1},
    "date_of_birth": {"type": "string", "format": "date"},
    "email": {"type": "string", "format": "email", "maxLength": 255},
    "phone": {"type": "string", "maxLength": 50},
    "status_code": {"type": "string", "maxLength": 50},
    "primary_language_code": {"type": "string", "maxLength": 10},
    "pronoun_code": {"type": "string", "maxLength": 20},
    "sex": {"type": "string", "enum": ["male", "female", "intersex", "unknown"]},
    "interpreter_needed": {"type": "boolean"}
  },
  "required": ["first_name", "last_name", "date_of_birth", "status_code"]
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Invalid email format"],
      "date_of_birth": ["Date cannot be in the future"]
    },
    "request_id": "req_550e8400e29b41d4a716446655440000"
  }
}
```

### Error Codes
- `VALIDATION_ERROR` (400): Input validation failed
- `CLIENT_NOT_FOUND` (404): Client ID does not exist
- `DUPLICATE_EMAIL` (409): Email already exists
- `INVALID_REFERENCE` (400): Invalid status/language/pronoun code
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): User lacks required permissions
- `RATE_LIMITED` (429): Too many requests

## Business Rules

### Data Validation Rules
1. **Names**: Must be 1-100 characters, no leading/trailing whitespace
2. **Email**: Must be valid format, unique across all clients
3. **Date of Birth**: Must be valid date, not in future, reasonable age limits (0-120 years)
4. **Phone**: Must match NZ phone number patterns when provided
5. **Sex**: Must be one of: 'male', 'female', 'intersex', 'unknown'
6. **Reference Codes**: Must exist and be active in reference tables

### Business Logic Rules
1. **Duplicate Prevention**: Same first_name + last_name + date_of_birth triggers warning
2. **Soft Delete**: Deletion sets status to 'deleted', preserves data for audit
3. **Status Transitions**: Certain status changes may require additional validation
4. **Contact Information**: At least one of email or phone must be provided

## Performance Requirements

### Response Time Targets
- Standard CRUD operations should be optimized for user experience
- Search functionality should provide timely results
- Reference data should be efficiently cached

### Scalability Targets
- Support large client databases (100,000+ records)
- Handle multiple concurrent users effectively
- Maintain system responsiveness under load

## Security Requirements

### Authentication & Authorization
- JWT bearer token authentication required
- Role-based access control (RBAC)
- Scoped permissions (read/write/delete clients)
- Audit trail for all operations

### Data Protection
- Encrypt sensitive fields at rest (email, phone, address)
- TLS 1.3 for all API communications
- PII data anonymization for logs
- GDPR/Privacy Act 2020 compliance

## Testing Requirements

### Test Coverage Areas
1. **Unit Tests**: Business logic, validation rules (>90% coverage)
2. **Integration Tests**: Database operations, API endpoints
3. **Performance Tests**: Load testing, stress testing
4. **Security Tests**: Authentication, authorization, injection attacks
5. **Compliance Tests**: Privacy regulations, audit requirements

### Test Data Requirements
- Diverse demographic test clients
- Edge cases (missing fields, boundary values)
- Invalid data scenarios
- Load testing with 50,000+ test clients

## Monitoring & Observability

### Metrics to Track
- API response times (p50, p95, p99)
- Error rates by endpoint
- Authentication failures
- Database query performance
- Cache hit rates

### Logging Requirements
- Structured JSON logs
- Request/response correlation IDs
- User action audit logs
- Performance metrics
- Error stack traces (sanitized)

## Future Considerations

### Planned Enhancements
- Advanced search with fuzzy matching
- Client photo/document management
- Integration with external identity verification
- Multi-language client interfaces
- Advanced analytics and reporting

### Scalability Roadmap
- Implement Redis caching layer
- Consider read replicas for reporting
- Evaluate CDC (Change Data Capture) for real-time sync
- Plan for multi-tenant architecture
