# Clean Architecture - Migration Guide

## How to Add New Features or Migrate Endpoints

This guide shows how to add a new endpoint following the Clean Architecture pattern.

---

## Example: Implementing User Profile Update

Let's say you want to add an endpoint to update user profile.

### Step 1: Add Domain Entity Property

Check if `User` entity has the field in `app/domain/entities.py`:

```python
@dataclass
class User:
    id: Optional[UUID]
    email: str
    password_hash: str
    full_name: Optional[str] = None  # ✅ Already here
    # ... other fields
```

If not, add it.

---

### Step 2: Add DTO in Application Layer

In `app/application/dtos.py`:

```python
class UpdateProfileRequestDTO(BaseModel):
    """DTO for updating user profile."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UpdateProfileResponseDTO(BaseModel):
    """DTO for profile update response."""
    id: str
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
```

---

### Step 3: Add Business Logic to Service

In `app/application/services.py`, add method to `AuthService`:

```python
class AuthService:
    # ... existing methods ...

    def update_user_profile(self, user_id: UUID, data: UpdateProfileRequestDTO) -> User:
        """Update user profile information."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Update fields
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone_number is not None:
            user.phone_number = data.phone_number

        # Persist changes
        return self.user_repo.update(user)
```

**Note:** The service doesn't know about HTTP or databases. It only uses the repository interface.

---

### Step 4: Add Route in Presentation Layer

In `app/presentation/api/auth.py`:

```python
from app.utils.security import decode_token

def get_current_user_id(token: str = Header(None)) -> UUID:
    """Extract user ID from JWT token."""
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token_gen = JWTTokenGenerator()
    payload = token_gen.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return UUID(payload["sub"])


@router.put("/profile")
def update_profile(
    data: UpdateProfileRequestDTO,
    user_id: UUID = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service),
):
    """Update user profile."""
    try:
        user = service.update_user_profile(user_id, data)
        return UpdateProfileResponseDTO(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Pattern Summary

```
REQUEST
  ↓
presentation/api/auth.py
  - Receive HTTP request
  - Parse DTO
  - Call service method
  - Convert domain entity to response DTO
  - Return HTTP response
  ↓
application/services.py (AuthService)
  - Business logic
  - Use repositories (don't know they're Postgres)
  - Use password_hasher, token_generator
  - Return domain entity
  ↓
infrastructure/database/repositories.py (PostgresUserRepository)
  - Execute SQL queries
  - Convert DB model ↔ domain entity
  - Return domain entity
  ↓
RESPONSE
```

---

## Testing Your New Endpoint

Create `tests/test_auth_service.py`:

```python
from app.domain.entities import User
from app.domain.interfaces import IUserRepository
from app.application.dtos import UpdateProfileRequestDTO
from app.application.services import AuthService
from uuid import UUID
from unittest.mock import Mock


class FakeUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}
    
    def save(self, user):
        self.users[user.id] = user
        return user
    
    def get_by_id(self, user_id):
        return self.users.get(user_id)
    
    def update(self, user):
        self.users[user.id] = user
        return user
    
    # ... other methods


def test_update_profile():
    # Setup
    fake_repo = FakeUserRepository()
    
    # Create a test user
    test_user = User(
        id=UUID('12345678-1234-5678-1234-567812345678'),
        email="test@example.com",
        password_hash="hashed",
        full_name="Old Name",
    )
    fake_repo.save(test_user)
    
    # Create service with fake repo
    service = AuthService(
        user_repo=fake_repo,
        recovery_token_repo=Mock(),
        password_hasher=Mock(),
        token_generator=Mock(),
        redis_service=Mock(),
    )
    
    # Execute
    update_data = UpdateProfileRequestDTO(full_name="New Name")
    updated_user = service.update_user_profile(test_user.id, update_data)
    
    # Assert
    assert updated_user.full_name == "New Name"
    assert updated_user.email == "test@example.com"
    print("✅ Test passed!")


if __name__ == "__main__":
    test_update_profile()
```

Run with: `python -m pytest tests/test_auth_service.py`

---

## Checklist for Adding New Endpoints

- [ ] **Domain Layer**: Does the entity need new fields?
- [ ] **Application Layer**: Add DTOs for request/response
- [ ] **Application Layer**: Add business logic method to service
- [ ] **Infrastructure Layer**: Do repositories need new methods?
- [ ] **Presentation Layer**: Add the route using dependency injection
- [ ] **Tests**: Write tests using fake repositories
- [ ] **Documentation**: Update this guide if pattern differs

---

## Common Mistakes to Avoid

❌ **DON'T** import SQLAlchemy in the service layer
```python
# BAD
class AuthService:
    def __init__(self, db: Session):  # Direct DB access
        self.db = db
        user = self.db.query(User).filter(...)  # Tight coupling
```

✅ **DO** inject a repository
```python
# GOOD
class AuthService:
    def __init__(self, user_repo: IUserRepository):  # Abstraction
        self.user_repo = user_repo
        user = self.user_repo.get_by_email(email)  # Loose coupling
```

---

❌ **DON'T** put business logic in routes
```python
# BAD
@router.post("/register")
def register(data):
    if User.query.filter(...).first():  # Logic in route
        raise Exception()
```

✅ **DO** delegate to service
```python
# GOOD
@router.post("/register")
def register(data, service = Depends(get_auth_service)):
    user = service.register_user(data)  # Logic in service
```

---

❌ **DON'T** let infrastructure leak into domain
```python
# BAD
from sqlalchemy import Column
class User:  # Domain entity
    id = Column(UUID(...))  # SQLAlchemy in domain!
```

✅ **DO** keep domain pure
```python
# GOOD
@dataclass
class User:  # Domain entity (pure Python)
    id: Optional[UUID]
    email: str
```

---

## Still Have Questions?

Refer to the main guide: `CLEAN_ARCHITECTURE_GUIDE.md`
