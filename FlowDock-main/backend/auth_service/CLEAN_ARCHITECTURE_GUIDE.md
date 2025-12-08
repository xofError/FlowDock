# Clean Architecture Refactoring - Auth Service

## ✅ Completed Implementation

Your `auth_service` has been successfully refactored to follow Clean Architecture principles. Here's what was created:

---

## 📁 New Directory Structure

```
backend/auth_service/app/
├── domain/                          # LAYER 1: Core Business Logic (Pure Python)
│   ├── __init__.py
│   ├── entities.py                  # User, Session, RecoveryToken dataclasses
│   └── interfaces.py                # IUserRepository, ISessionRepository, etc.
│
├── application/                     # LAYER 2: Use Cases & Orchestration
│   ├── __init__.py
│   ├── dtos.py                      # Pydantic DTOs (RegisterRequestDTO, etc.)
│   └── services.py                  # AuthService - business logic
│
├── infrastructure/                  # LAYER 3: External Tools & DB
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy ORM (UserModel, etc.)
│   │   └── repositories.py          # PostgresUserRepository, etc.
│   ├── security/
│   │   ├── __init__.py
│   │   └── security.py              # ArgonPasswordHasher, JWTTokenGenerator
│   └── email/                       # (For future email service)
│
├── presentation/                    # LAYER 4: Entry Points
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── auth.py                  # FastAPI routes (refactored)
│   └── dependencies.py              # Dependency injection setup
│
├── api/                             # EXISTING (to keep for now)
├── core/
├── models/                          # EXISTING (can be deprecated)
├── schemas/
├── services/                        # EXISTING (can be deprecated)
├── utils/
├── database.py
└── main.py                          # Updated to use new structure
```

---

## 🔑 Key Concepts

### 1. **Domain Layer** (`domain/`)
**Pure business logic - NO framework dependencies**

- **entities.py**: Dataclasses representing core objects
  - `User`: Email, password hash, verification status, storage limits
  - `Session`: Session tracking
  - `RecoveryToken`: Password reset tokens

- **interfaces.py**: Abstract contracts
  - `IUserRepository`: How to persist users
  - `ISessionRepository`: How to manage sessions
  - `IRecoveryTokenRepository`: How to store recovery tokens
  - `IPasswordHasher`: Password hashing contract
  - `ITokenGenerator`: JWT token generation contract

**Why?** Your business rules are independent of databases and frameworks.

---

### 2. **Application Layer** (`application/`)
**Orchestrates use cases using domain entities and repositories**

- **dtos.py**: Pydantic models for HTTP validation
  - `RegisterRequestDTO`, `LoginRequestDTO`, `TokenResponseDTO`
  - `VerifyEmailOTPRequestDTO`, `TotpSetupResponseDTO`
  - `ResetPasswordRequestDTO`, etc.

- **services.py**: `AuthService` - the orchestrator
  - `register_user()`: Create user, hash password, persist
  - `authenticate_user()`: Verify credentials with rate limiting
  - `verify_email_otp()`: Validate OTP, mark user as verified
  - `request_password_reset()`: Create recovery tokens
  - `confirm_password_reset()`: Verify token, update password
  - `create_tokens()`: Generate JWT and refresh tokens

**Why?** Business logic is DECOUPLED from how data is stored or how APIs work.

---

### 3. **Infrastructure Layer** (`infrastructure/`)
**Concrete implementations of abstractions - actual DB and security code**

- **database/models.py**: SQLAlchemy ORM
  - `UserModel`, `SessionModel`, `RecoveryTokenModel`
  - Maps to PostgreSQL tables

- **database/repositories.py**: Repository implementations
  - `PostgresUserRepository` implements `IUserRepository`
  - Handles conversion between Domain Entities and DB Models
  - Example:
    ```python
    class PostgresUserRepository(IUserRepository):
        def get_by_email(self, email: str) -> Optional[User]:
            db_user = self.db.query(UserModel).filter(...).first()
            return self._to_entity(db_user)  # Convert DB -> Domain
    ```

- **security/security.py**: Implementations
  - `ArgonPasswordHasher` implements `IPasswordHasher`
  - `JWTTokenGenerator` implements `ITokenGenerator`

**Why?** Database and security details are isolated. Want to switch from PostgreSQL to MongoDB? Write a `MongoUserRepository`, change one line in dependency injection.

---

### 4. **Presentation Layer** (`presentation/`)
**HTTP entry point and dependency wiring**

- **dependencies.py**: FastAPI dependency injection setup
  ```python
  def get_auth_service(db: Session = ...) -> AuthService:
      # Wire together all implementations
      user_repo = PostgresUserRepository(db)
      password_hasher = ArgonPasswordHasher()
      token_generator = JWTTokenGenerator()
      return AuthService(user_repo, password_hasher, token_generator, ...)
  ```

- **api/auth.py**: FastAPI routes (clean and simple)
  ```python
  @router.post("/register")
  def register(
      data: RegisterRequest,
      service: AuthService = Depends(get_auth_service)
  ):
      user = service.register_user(data)
      return {"detail": "verification code sent"}
  ```

**Why?** Routes are thin - they just delegate to services. Testing is easy.

---

## 🏗️ The Golden Rule: Dependencies Point Inward

```
            ❌ BAD                    ✅ GOOD
      (Circular Dependency)       (Dependency Injection)

    FastAPI → Service              FastAPI → Interface
    Service → SQLAlchemy           Interface ← Repository
    SQLAlchemy → ?                 Repository → SQLAlchemy
```

Your `AuthService` doesn't import SQLAlchemy or FastAPI. It only knows about:
- Domain entities (`User`, `RecoveryToken`)
- Domain interfaces (`IUserRepository`)
- DTOs for data transfer

---

## 🧪 Why This Matters

### Before (Tightly Coupled)
```python
# Old: Services mixed everything
class AuthService:
    def register(self, email, password):
        db = SessionLocal()  # Direct DB access
        if db.query(User).filter(...).first():  # Tight coupling
            raise Exception()
        user = User(email=email, password=hash(password))
        db.add(user)
        db.commit()  # Hard to test without real DB
```

### After (Clean Architecture)
```python
# New: Service uses abstractions
class AuthService:
    def register_user(self, data: RegisterRequestDTO) -> User:
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("User already exists")
        hashed_pw = self.password_hasher.hash(data.password)
        user = User(id=None, email=data.email, password_hash=hashed_pw)
        return self.user_repo.save(user)  # Repository is injected

# Testing is NOW trivial:
class FakeUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}
    def get_by_email(self, email):
        return self.users.get(email)
    def save(self, user):
        self.users[user.email] = user
        return user

# Test without database
service = AuthService(
    user_repo=FakeUserRepository(),
    password_hasher=...,
    token_generator=...,
)
user = service.register_user(RegisterRequestDTO(...))
assert user.email == "test@example.com"
```

---

## 📋 Next Steps

### 1. **Keep Old Code (For Now)**
The old `app/api`, `app/services`, `app/models` still exist. This allows gradual migration.

### 2. **Implement Remaining Features**
The refactored `app/presentation/api/auth.py` has placeholders for:
- ✅ Register & Email Verification
- ✅ Login & Logout  
- ✅ Password Recovery
- ⚠️ Token Refresh (needs Redis integration)
- ⚠️ TOTP/2FA Setup (needs implementation)
- ⚠️ OAuth Callback (needs service integration)

### 3. **Port Other Endpoints**
When ready, implement the remaining routes by:
1. Adding business logic to `AuthService`
2. Creating the route in `presentation/api/auth.py`
3. Using dependency injection

### 4. **Create Tests**
Now you can easily test with fake repositories:
```python
# tests/test_auth_service.py
def test_register_user():
    fake_repo = FakeUserRepository()
    service = AuthService(fake_repo, ...)
    user = service.register_user(RegisterRequestDTO(...))
    assert user.email == "test@example.com"
```

### 5. **Extend to Other Services**
Apply the same pattern to `media_service`:
```
app/
├── domain/
│   ├── entities.py (File, Share, etc.)
│   └── interfaces.py (IFileRepository, etc.)
├── application/
│   └── services.py (FileService, SharingService)
├── infrastructure/
│   ├── database/repositories.py
│   └── ...
└── presentation/
    └── api/files.py
```

---

## 🎯 Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Testing** | Needs DB + API setup | Pure Python test with fakes |
| **Changing DB** | Edit 50+ files | Write new repository, 1 line change |
| **Business Logic** | Scattered in services | Centralized in `AuthService` |
| **Reusability** | Tied to FastAPI | Can use in CLI, workers, etc. |
| **Clarity** | What does each layer do? | Clear 4-layer structure |
| **Framework Updates** | Ripple through code | Only change `presentation/` layer |

---

## 📚 Architecture Diagram

```
┌─────────────────────────────────────────────┐
│          PRESENTATION LAYER                 │
│  FastAPI Routes → Dependency Injection     │
│  (app/presentation/api/auth.py)            │
└─────────────────────────────────────────────┘
                      ↓ injects
┌─────────────────────────────────────────────┐
│        APPLICATION LAYER                    │
│  AuthService (pure business logic)         │
│  (app/application/services.py)             │
│  - Uses: IUserRepository, IPasswordHasher  │
└─────────────────────────────────────────────┘
                      ↓ uses
┌─────────────────────────────────────────────┐
│         DOMAIN LAYER                        │
│  Entities (User, Session, RecoveryToken)  │
│  Interfaces (IUserRepository, etc.)        │
│  (app/domain/)                             │
└─────────────────────────────────────────────┘
                      ↓ implements
┌─────────────────────────────────────────────┐
│       INFRASTRUCTURE LAYER                  │
│  PostgresUserRepository                    │
│  ArgonPasswordHasher, JWTTokenGenerator    │
│  (app/infrastructure/)                     │
└─────────────────────────────────────────────┘
```

---

## ✨ You're Ready!

Your auth_service is now **resilient, testable, and maintainable**. Each layer is independent, making it:
- Easy to test without databases
- Simple to swap implementations
- Clear where business logic lives
- Prepared for scaling

Happy coding! 🚀
