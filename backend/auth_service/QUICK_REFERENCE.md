# Clean Architecture - Quick Reference

## 📂 Quick File Location Guide

| Need | Location | What's There |
|------|----------|-------------|
| **Core Auth Logic** | `app/application/services.py` | `AuthService` class |
| **2FA Operations** | `app/application/twofa_service.py` | `TwoFAService` class |
| **API Routes** | `app/presentation/api/auth.py` | All endpoints |
| **Wiring Services** | `app/presentation/dependencies.py` | `get_auth_service()`, `get_twofa_service()` |
| **Database Models** | `app/infrastructure/database/models.py` | SQLAlchemy models |
| **Database Logic** | `app/infrastructure/database/repositories.py` | Repository implementations |
| **User Entity** | `app/domain/entities.py` | `User` dataclass |
| **Interface Contracts** | `app/domain/interfaces.py` | `IUserRepository`, etc. |
| **Security** | `app/infrastructure/security/security.py` | Hashing, JWT |
| **Tokens (Redis)** | `app/infrastructure/security/token_store.py` | `RefreshTokenStore` |
| **TOTP Library** | `app/infrastructure/security/totp.py` | `TOTPService` |
| **Email** | `app/infrastructure/email/email.py` | Email services |
| **Data Transfer** | `app/application/dtos.py` | Pydantic schemas |

## 🔑 Key Classes

```python
# Core Services
from app.application.services import AuthService
from app.application.twofa_service import TwoFAService

# Infrastructure
from app.infrastructure.database.repositories import PostgresUserRepository
from app.infrastructure.security.security import ArgonPasswordHasher, JWTTokenGenerator
from app.infrastructure.security.token_store import RefreshTokenStore
from app.infrastructure.security.totp import TOTPService
from app.infrastructure.email.email import get_email_service

# Dependency Injection
from app.presentation.dependencies import (
    get_auth_service,
    get_twofa_service,
    get_refresh_token_store,
    get_token_generator,
)
```

## 🎯 Common Tasks

### Adding a New Endpoint
```python
@router.post("/new-endpoint")
def new_endpoint(
    data: SomeDTO,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = service.some_method(data.field)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
```

### Using TwoFA Service
```python
@router.post("/enable-2fa")
def enable_2fa(
    data: TotpVerifyRequest,
    twofa_service: TwoFAService = Depends(get_twofa_service),
):
    codes = twofa_service.verify_totp_and_enable_2fa(
        data.email, data.secret, data.code
    )
    return {"recovery_codes": codes}
```

### Managing Tokens
```python
token_store = RefreshTokenStore()
token_store.store(hashed_token, user_email, expiry)
record = token_store.get(hashed_token)
token_store.revoke_all_by_user(user_email)
```

### Creating Test User
```python
from app.application.user_util_service import UserUtilService
from app.infrastructure.database.repositories import PostgresUserRepository

db = SessionLocal()
repo = PostgresUserRepository(db)
util = UserUtilService(repo, ArgonPasswordHasher())
test_user = util.create_test_user("test@example.com", "password")
```

## 🧪 Testing Pattern

```python
from app.domain.interfaces import IUserRepository
from app.application.services import AuthService

class FakeUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}
    
    def get_by_email(self, email):
        return self.users.get(email)
    
    def save(self, user):
        self.users[user.email] = user
        return user
    
    # ... implement other methods

# In test
fake_repo = FakeUserRepository()
service = AuthService(fake_repo, None, hasher, tokens, redis)
# Test without database!
```

## 📊 Dependency Flow

```
API Route
  ↓ (depends on)
Application Service (AuthService, TwoFAService)
  ↓ (depends on)
Infrastructure Services (Repositories, Security, Email)
  ↓ (implement)
Domain Interfaces (IUserRepository, IPasswordHasher)
```

## 🔄 Request Lifecycle

```
1. User sends HTTP request to endpoint
2. FastAPI injects dependencies via Depends()
3. Presentation layer gets application services
4. Service calls repository methods (depends on IUserRepository)
5. PostgresUserRepository executes actual DB query
6. Result converted back to domain entity
7. Response sent to user
```

## 💡 Design Principles

| Principle | How It's Applied |
|-----------|------------------|
| **Single Responsibility** | Each service does one thing |
| **Dependency Inversion** | Services depend on interfaces, not implementations |
| **Open/Closed** | Easy to add new implementations without changing existing code |
| **Liskov Substitution** | Can swap PostgresUserRepository for MongoUserRepository seamlessly |
| **Interface Segregation** | Small, focused interfaces |

## ✅ Backward Compatibility

Old code still exists and works:
- `app/api/` - Old routes (deprecated)
- `app/services/` - Old functions (deprecated)
- `app/models/` - Old models (deprecated)
- `app/schemas/` - Still used by API
- `app/utils/` - Still used by some code

Gradual migration is possible - new code uses clean architecture, old code continues to work.

## 🚀 Performance Tips

1. **Dependency Injection happens once per request** - No overhead
2. **Database connections pooled** - SQLAlchemy handles this
3. **Redis caching for tokens** - Fast token verification
4. **No N+1 queries** - Repositories handle loading
5. **Argon2 hashing** - Memory-hard, GPU-resistant

## 📚 Related Documentation

- `CLEAN_ARCHITECTURE_GUIDE.md` - Detailed explanation
- `REFACTORING_SUMMARY.md` - Complete summary of changes

## 🎯 Success Metrics

After this refactoring:
- ✅ Business logic has NO framework dependencies
- ✅ Code is testable without database
- ✅ Easy to swap implementations
- ✅ Clear separation of concerns
- ✅ Maintainable for years
- ✅ Easy to onboard new developers

**That's it! You're now using production-grade clean architecture.** 🎉
