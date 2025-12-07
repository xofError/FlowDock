# Architecture Classes Reference

## 📦 All New Classes Created

### Domain Layer

#### `app/domain/entities.py`

```python
@dataclass
class User:
    """Core user entity - represents a user in the system"""
    id: Optional[UUID]
    email: str
    password_hash: str
    full_name: Optional[str]
    # ... other fields

@dataclass
class Session:
    """Session entity - represents a user session/login"""
    id: Optional[UUID]
    user_id: UUID
    refresh_token_hash: Optional[str]
    # ... other fields

@dataclass
class RecoveryToken:
    """Recovery token entity - for password reset and recovery codes"""
    id: Optional[UUID]
    user_id: UUID
    token: str
    method: str  # "email", "recovery_code", etc.
    # ... other fields
```

#### `app/domain/interfaces.py`

```python
class IUserRepository(ABC):
    """Abstract contract for user persistence"""
    def get_by_email(self, email: str) -> Optional[User]: pass
    def get_by_id(self, user_id: UUID) -> Optional[User]: pass
    def save(self, user: User) -> User: pass
    def update(self, user: User) -> User: pass

class IRecoveryTokenRepository(ABC):
    """Abstract contract for recovery token persistence"""
    def create(self, token: RecoveryToken) -> RecoveryToken: pass
    def get_valid_by_user_and_token(self, user_id: UUID, token: str) -> Optional[RecoveryToken]: pass
    def mark_as_used(self, token_id: UUID) -> None: pass

class IPasswordHasher(ABC):
    """Abstract contract for password hashing"""
    def hash(self, password: str) -> str: pass
    def verify(self, password: str, hashed: str) -> bool: pass

class ITokenGenerator(ABC):
    """Abstract contract for JWT token generation"""
    def create_access_token(self, user_id: UUID) -> str: pass
    def create_refresh_token(self, user_id: UUID) -> tuple[str, str, object]: pass
    # ... other methods
```

### Application Layer

#### `app/application/services.py`

```python
class RedisService:
    """Service for Redis operations (caching, rate limiting, OTP storage)"""
    def __init__(self)
    def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool
    def set_otp(self, email: str, otp: str, expires_in_seconds: int) -> None
    def get_otp(self, email: str) -> Optional[str]
    def delete_otp(self, email: str) -> None

class AuthService:
    """Core authentication service"""
    def __init__(self, user_repo, recovery_token_repo, password_hasher, token_generator, redis_service)
    
    # Registration
    def register_user(self, data: RegisterRequestDTO) -> User
    
    # Email OTP
    def generate_email_otp(self, email: str) -> str
    def verify_email_otp(self, email: str, otp: str) -> User
    
    # Authentication
    def authenticate_user(self, email: str, password: str) -> User
    def create_tokens(self, user_id) -> tuple[str, str, datetime]
    
    # Password Recovery
    def request_password_reset(self, email: str) -> RecoveryToken
    def verify_password_reset_token(self, email: str, token: str) -> bool
    def confirm_password_reset(self, email: str, token: str, new_password: str) -> User
```

#### `app/application/twofa_service.py`

```python
class TwoFAService:
    """Service for two-factor authentication operations"""
    def __init__(self, user_repo, recovery_token_repo, totp_service=None)
    
    # TOTP Setup
    def initiate_totp_setup(self, email: str) -> tuple[str, str]
    def verify_totp_and_enable_2fa(self, email: str, totp_secret: str, totp_code: str, recovery_code_count: int=10) -> list[str]
    
    # TOTP Verification
    def verify_totp_code(self, email: str, totp_code: str) -> bool
    
    # Recovery Codes
    def verify_and_use_recovery_code(self, email: str, code: str) -> bool
    
    # Admin
    def disable_totp(self, email: str) -> User
```

#### `app/application/user_util_service.py`

```python
class UserUtilService:
    """Utility service for user operations"""
    def __init__(self, user_repo, password_hasher)
    def create_test_user(self, email: str="test@example.com", password: str="password") -> User
    def mark_user_verified(self, email: str) -> User
```

#### `app/application/dtos.py`

```python
# Input DTOs
class RegisterRequestDTO(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str]

class VerifyEmailOTPRequestDTO(BaseModel):
    email: EmailStr
    token: str

# ... 15+ more DTOs

# Output DTOs
class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    totp_required: bool

class UserResponseDTO(BaseModel):
    id: str
    email: str
    verified: bool
    twofa_enabled: bool
```

### Infrastructure Layer

#### `app/infrastructure/database/models.py`

```python
class UserModel(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"
    id: UUID
    email: str
    password_hash: str
    # ... all user fields

class SessionModel(Base):
    """SQLAlchemy Session model"""
    __tablename__ = "sessions"
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    # ... session fields

class RecoveryTokenModel(Base):
    """SQLAlchemy RecoveryToken model"""
    __tablename__ = "recovery_tokens"
    id: UUID
    user_id: UUID
    token: str
    # ... recovery token fields
```

#### `app/infrastructure/database/repositories.py`

```python
class PostgresUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository"""
    def __init__(self, db: Session)
    def get_by_email(self, email: str) -> Optional[User]
    def get_by_id(self, user_id: UUID) -> Optional[User]
    def save(self, user: User) -> User
    def update(self, user: User) -> User
    @staticmethod
    def _to_entity(db_user: UserModel) -> User

class PostgresRecoveryTokenRepository(IRecoveryTokenRepository):
    """PostgreSQL implementation of recovery token repository"""
    def __init__(self, db: Session)
    def create(self, token: RecoveryToken) -> RecoveryToken
    def get_valid_by_user_and_token(self, user_id: UUID, token: str) -> Optional[RecoveryToken]
    def mark_as_used(self, token_id: UUID) -> None

class PostgresSessionRepository(ISessionRepository):
    """PostgreSQL implementation of session repository"""
    def __init__(self, db: Session)
    def create(self, session: SessionEntity) -> SessionEntity
    def get_by_id(self, session_id: UUID) -> Optional[SessionEntity]
    def update(self, session: SessionEntity) -> SessionEntity
    def revoke_all_by_user(self, user_id: UUID) -> None
```

#### `app/infrastructure/security/security.py`

```python
class ArgonPasswordHasher(IPasswordHasher):
    """Argon2 password hashing implementation"""
    def hash(self, password: str) -> str
    def verify(self, password: str, hashed: str) -> bool

class JWTTokenGenerator(ITokenGenerator):
    """JWT token generation and validation"""
    def _ensure_jwt_secret(self) -> None
    def create_access_token(self, user_id: UUID) -> str
    def decode_access_token(self, token: str) -> Optional[Dict]
    def create_refresh_token(self, user_id: UUID) -> Tuple[str, str, datetime]
    def verify_refresh_token(self, token: str, stored_hash: str) -> bool
    @staticmethod
    def _hash_token(token: str) -> str
```

#### `app/infrastructure/security/token_store.py`

```python
class RefreshTokenStore:
    """Redis-based refresh token storage"""
    def __init__(self, redis_client: redis.Redis=None)
    def store(self, hashed_token: str, user_email: str, expiry: datetime) -> None
    def get(self, hashed_token: str) -> Optional[Dict]
    def revoke(self, hashed_token: str) -> None
    def revoke_all_by_user(self, user_email: str) -> None
    def is_blacklisted(self, hashed_token: str) -> bool
```

#### `app/infrastructure/security/totp.py`

```python
class TOTPService:
    """TOTP (Time-based One-Time Password) service for 2FA"""
    @staticmethod
    def generate_secret() -> str
    @staticmethod
    def verify(totp_secret: str, code: str, window: int=1) -> bool
    @staticmethod
    def get_provisioning_uri(email: str, totp_secret: str, app_name: str="FlowDock") -> str
```

#### `app/infrastructure/email/email.py`

```python
class IEmailService(ABC):
    """Abstract interface for email sending"""
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> bool

class SMTPEmailService(IEmailService):
    """SMTP email service implementation"""
    def __init__(self, smtp_host: str=None, smtp_port: int=None, ...)
    def send(self, to: str, subject: str, body: str) -> bool

class ConsoleEmailService(IEmailService):
    """Console email service for development"""
    def send(self, to: str, subject: str, body: str) -> bool

def get_email_service() -> IEmailService:
    """Factory function to get appropriate email service"""
```

### Presentation Layer

#### `app/presentation/dependencies.py`

```python
# Database
def get_db() -> Session

# Repositories
def get_user_repository(db: Session) -> PostgresUserRepository
def get_recovery_token_repository(db: Session) -> PostgresRecoveryTokenRepository

# Security
def get_password_hasher() -> ArgonPasswordHasher
def get_token_generator() -> JWTTokenGenerator
def get_totp_service() -> TOTPService
def get_refresh_token_store() -> RefreshTokenStore

# Services
def get_redis_service() -> RedisService
def get_email_service()
def get_auth_service(db, user_repo, recovery_token_repo, password_hasher, token_generator, redis_service) -> AuthService
def get_twofa_service(db, user_repo, recovery_token_repo, totp_service) -> TwoFAService
def get_user_util_service(db, user_repo, password_hasher) -> UserUtilService
```

#### `app/presentation/api/auth.py`

```python
# Endpoints using dependency injection
@router.post("/register")
def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service))

@router.post("/verify-email")
def verify_email(data: VerifyEmailOTPRequest, service: AuthService = Depends(get_auth_service))

@router.post("/login")
def login(data: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service), ...)

@router.post("/logout")
def logout(response: Response, ...)

@router.post("/refresh")
def refresh(response: Response, ...)

@router.post("/totp/setup")
def totp_setup(data: TotpSetupRequest, twofa_service: TwoFAService = Depends(get_twofa_service))

@router.post("/totp/verify")
def totp_verify(data: TotpVerifyRequest, twofa_service: TwoFAService = Depends(get_twofa_service))

@router.post("/forgot-password")
def forgot_password(data: RequestPasswordReset, service: AuthService = Depends(get_auth_service), ...)

@router.get("/verify-reset-token")
def verify_reset_token(token: str, email: str, service: AuthService = Depends(get_auth_service))

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, service: AuthService = Depends(get_auth_service))
```

## 📊 Class Hierarchy

```
Domain Layer (Abstract)
├── User (entity)
├── Session (entity)
├── RecoveryToken (entity)
├── IUserRepository (interface)
├── IRecoveryTokenRepository (interface)
├── IPasswordHasher (interface)
└── ITokenGenerator (interface)

Infrastructure Layer (Concrete)
├── PostgresUserRepository → implements IUserRepository
├── PostgresRecoveryTokenRepository → implements IRecoveryTokenRepository
├── PostgresSessionRepository → implements ISessionRepository
├── UserModel (ORM)
├── SessionModel (ORM)
├── RecoveryTokenModel (ORM)
├── ArgonPasswordHasher → implements IPasswordHasher
├── JWTTokenGenerator → implements ITokenGenerator
├── RefreshTokenStore (Redis wrapper)
├── TOTPService (TOTP library wrapper)
├── SMTPEmailService → implements IEmailService
└── ConsoleEmailService → implements IEmailService

Application Layer (Business Logic)
├── AuthService → uses all repositories and security services
├── TwoFAService → uses user repo and TOTP service
├── UserUtilService → uses user repo and password hasher
└── RedisService (cache/OTP management)

Presentation Layer (HTTP)
├── Dependencies (DI setup)
└── Routes (API endpoints using services)
```

## 🔗 Dependency Injection Map

```
API Route
  ├── depends on → AuthService
  │                 ├── depends on → IUserRepository (injected: PostgresUserRepository)
  │                 ├── depends on → IRecoveryTokenRepository (injected: PostgresRecoveryTokenRepository)
  │                 ├── depends on → IPasswordHasher (injected: ArgonPasswordHasher)
  │                 ├── depends on → ITokenGenerator (injected: JWTTokenGenerator)
  │                 └── depends on → RedisService
  │
  ├── depends on → TwoFAService
  │                 ├── depends on → IUserRepository (injected: PostgresUserRepository)
  │                 ├── depends on → IRecoveryTokenRepository (injected: PostgresRecoveryTokenRepository)
  │                 └── depends on → TOTPService
  │
  ├── depends on → RefreshTokenStore
  │
  └── depends on → IEmailService (injected: SMTPEmailService or ConsoleEmailService)
```

## 📈 Method Flow Example: Login

```
@router.post("/login")
login(data, response, service, twofa_service, token_store, token_gen)
  │
  ├─→ service.authenticate_user(email, password)
  │    └─→ AuthService.authenticate_user()
  │         ├─→ RedisService.check_rate_limit()
  │         ├─→ IUserRepository.get_by_email(email)
  │         │    └─→ PostgresUserRepository.get_by_email()
  │         │         └─→ UserModel query
  │         └─→ IPasswordHasher.verify()
  │              └─→ ArgonPasswordHasher.verify()
  │
  ├─→ twofa_service.verify_totp_code() [if 2FA enabled]
  │    └─→ TOTPService.verify()
  │
  ├─→ token_store.revoke_all_by_user() [enforce single session]
  │    └─→ RefreshTokenStore.revoke_all_by_user()
  │
  ├─→ token_gen.create_access_token()
  │    └─→ JWTTokenGenerator.create_access_token()
  │
  ├─→ token_gen.create_refresh_token()
  │    └─→ JWTTokenGenerator.create_refresh_token()
  │
  └─→ token_store.store()
       └─→ RefreshTokenStore.store() [to Redis]
```

## ✅ Complete Reference

Now you have a complete reference of all classes, their responsibilities, and how they connect. This architecture enables:

- **Easy testing** - Swap real services for fakes
- **Easy changes** - Modify one implementation without touching others
- **Easy debugging** - Follow the data flow through layers
- **Easy documentation** - Each class has one clear purpose

Happy coding! 🚀
