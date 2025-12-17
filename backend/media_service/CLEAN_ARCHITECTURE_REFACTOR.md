# Clean Architecture Refactoring: Media Service

**Date**: December 2024  
**Status**: Complete  
**Purpose**: Decouple business logic from technology-specific implementations

---

## Executive Summary

The Media Service has been refactored from a monolithic structure with tightly coupled dependencies to **Clean Architecture** following the same patterns used in the Auth Service. This enables:

✅ **Technology Independence**: Replace MongoDB/GridFS with S3 without changing business logic  
✅ **Testability**: Mock interfaces instead of concrete implementations  
✅ **Maintainability**: Clear separation of concerns across 4 distinct layers  
✅ **Extensibility**: Add new encryption, storage, or messaging backends easily  

---

## New Directory Structure

```
backend/media_service/app/
├── domain/                          # Layer 1: Pure Python (NO external dependencies)
│   ├── entities.py                  # File entity (dataclass)
│   └── interfaces.py                # Abstract contracts (IFileRepository, ICryptoService, IEventPublisher)
│
├── application/                     # Layer 2: Business Logic (Orchestration)
│   ├── dtos.py                      # Pydantic schemas (moved from schemas/)
│   └── services.py                  # FileService (pure logic, depends on interfaces)
│
├── infrastructure/                  # Layer 3: Technology Implementations
│   ├── database/
│   │   └── mongo_repository.py      # MongoGridFSRepository implements IFileRepository
│   ├── security/
│   │   └── encryption.py            # AESCryptoService implements ICryptoService
│   └── messaging/
│       └── rabbitmq_publisher.py    # RabbitMQEventPublisher implements IEventPublisher
│
├── presentation/                    # Layer 4: Entry Points & Dependency Injection
│   ├── api/
│   │   └── files.py                 # FastAPI routes (refactored to use injected service)
│   └── dependencies.py              # DI container (get_file_service factory)
│
├── core/
│   └── config.py                    # Configuration (unchanged)
│
├── utils/
│   ├── validators.py                # Validation logic (unchanged)
│   ├── security.py                  # JWT/Token utilities (unchanged)
│   └── crypto.py                    # DEPRECATED - moved to infrastructure/security/encryption.py
│
├── services/                        # Keep for now, but deprecated
│   ├── rabbitmq_service.py          # RabbitMQ connection logic (still used)
│   └── sharing_service.py           # File sharing logic (independent, unchanged)
│
└── api/                             # DEPRECATED - moved to presentation/api/
    └── files.py                     # OLD - DO NOT USE
```

---

## Layer Breakdown

### 1. Domain Layer (`domain/`)

**Purpose**: Define business entities and abstract contracts. Pure Python, NO external dependencies.

**Files**:
- `entities.py`: `File` dataclass representing a file in the system
- `interfaces.py`: Three abstract interfaces

**Key Interfaces**:

```python
class IFileRepository(ABC):
    """Abstract contract for file storage"""
    async def save_file_stream(file: File, stream: AsyncGenerator) -> str
    async def get_file_metadata(file_id: str) -> Optional[File]
    async def get_file_stream(file_id: str) -> Tuple[Optional[File], Optional[AsyncGenerator]]
    async def delete(file_id: str) -> bool
    async def list_by_owner(owner_id: str) -> List[File]

class ICryptoService(ABC):
    """Abstract contract for encryption/decryption"""
    def generate_key_pair() -> Tuple[bytes, bytes]
    async def encrypt_stream(stream, key, nonce) -> AsyncGenerator
    async def decrypt_stream(stream, key, nonce) -> AsyncGenerator
    def wrap_key(file_key: bytes) -> bytes
    def unwrap_key(encrypted_key: bytes) -> bytes

class IEventPublisher(ABC):
    """Abstract contract for event publishing"""
    async def publish_upload(user_id: str, file_id: str, file_size: int)
    async def publish_delete(user_id: str, file_id: str, file_size: int)
    async def publish_download(user_id: str, file_id: str)
```

**Why This Matters**: If you decide to use AWS S3 instead of MongoDB, you only need to create `S3Repository` implementing `IFileRepository`. The business logic (`FileService`) doesn't know the difference.

---

### 2. Application Layer (`application/`)

**Purpose**: Implement business logic without knowing technology details.

**Files**:
- `dtos.py`: Pydantic schemas (moved from `schemas/file.py`)
- `services.py`: `FileService` orchestrator

**FileService Structure**:

```python
class FileService:
    def __init__(
        self,
        repo: IFileRepository,      # Injected
        crypto: ICryptoService,     # Injected
        event_publisher: IEventPublisher  # Injected
    ):
        self.repo = repo
        self.crypto = crypto
        self.publisher = event_publisher

    async def upload_file_encrypted(user_id: str, file: UploadFile):
        """Business logic without technology details"""
        # 1. Validate
        # 2. Generate encryption keys (via crypto service)
        # 3. Create domain entity
        # 4. Save via repository (doesn't know it's GridFS)
        # 5. Publish event (doesn't know it's RabbitMQ)
        return success, file_id, original_size, error
```

**Key Concept**: The service depends on **INTERFACES**, not **IMPLEMENTATIONS**.

---

### 3. Infrastructure Layer (`infrastructure/`)

**Purpose**: Implement abstract contracts using specific technologies.

**Files**:

**Database** (`database/mongo_repository.py`):
- `MongoGridFSRepository` implements `IFileRepository`
- Handles ObjectId conversions
- Manages GridFS upload/download streams
- All MongoDB-specific logic lives here

**Security** (`security/encryption.py`):
- `AESCryptoService` implements `ICryptoService`
- AES-256-CTR encryption
- Key wrapping with master key
- All cryptography logic lives here

**Messaging** (`messaging/rabbitmq_publisher.py`):
- `RabbitMQEventPublisher` implements `IEventPublisher`
- Wraps existing `rabbitmq_service.py`
- All RabbitMQ-specific logic lives here

**Why This Matters**: All "how to do it" code is here. If you swap MongoDB for S3, only `mongo_repository.py` changes.

---

### 4. Presentation Layer (`presentation/`)

**Purpose**: HTTP entry points and dependency injection.

**Files**:

**API** (`api/files.py`):
- Refactored FastAPI routes
- Uses `Depends(get_file_service)` to inject service
- Routes remain unchanged from user perspective

**Dependencies** (`dependencies.py`):
```python
async def get_file_service() -> FileService:
    """FastAPI dependency factory"""
    fs = get_fs()
    repo = MongoGridFSRepository(fs)
    crypto = AESCryptoService()
    publisher = RabbitMQEventPublisher()
    
    return FileService(repo, crypto, publisher)
```

**Usage in Endpoints**:
```python
@router.post("/upload/{user_id}")
async def upload_file(
    file: UploadFile,
    service: FileService = Depends(get_file_service),  # Injected!
):
    success, file_id, size, error = await service.upload_file_encrypted(...)
    ...
```

---

## What Changed

### ❌ Removed

1. **`app/services/file_service.py`** (OLD)
   - Had static methods tightly coupled to GridFS
   - Mixed validation, encryption, storage logic
   - No interfaces or dependency injection

2. **`app/models/file.py`** (OLD)
   - Basic class with to_dict()
   - Replaced by domain entity `File`

3. **`app/schemas/file.py`** (PARTIALLY)
   - Schemas moved to `application/dtos.py`
   - Renamed following convention

### ✅ Added

1. **`app/domain/` (NEW LAYER)**
   - Pure Python entities and interfaces
   - Zero external dependencies

2. **`app/infrastructure/` (NEW LAYER)**
   - Technology-specific implementations
   - GridFS, Encryption, RabbitMQ logic isolated

3. **`app/application/services.py` (REFACTORED)**
   - Real class with `__init__` (not static methods)
   - Dependencies injected via constructor
   - Pure business logic

4. **`app/presentation/dependencies.py` (NEW)**
   - FastAPI dependency injection container
   - Constructs service object graph

5. **`app/presentation/api/files.py` (REFACTORED)**
   - Uses injected `FileService`
   - Cleaner endpoints

### ⚠️ Keep (Unchanged)

- `app/services/rabbitmq_service.py` → Used by infrastructure layer
- `app/services/sharing_service.py` → Independent, unchanged
- `app/utils/validators.py` → Used by application layer
- `app/utils/security.py` → Used by presentation layer
- `app/utils/crypto.py` → Deprecated, replaced by infrastructure/security/encryption.py
- `app/core/config.py` → Configuration (unchanged)
- `app/database.py` → MongoDB connection (unchanged)

---

## Migration Path for Endpoints

### Before (Tightly Coupled)
```python
@router.post("/upload/{user_id}")
async def upload_file(user_id: str, file: UploadFile):
    # Directly calls static method
    success, file_id, size, error = await FileService.upload_encrypted_file(user_id, file)
    # FileService internally calls get_fs() and knows about GridFS
    # Hard to test, hard to swap technologies
```

### After (Dependency Injection)
```python
@router.post("/upload/{user_id}")
async def upload_file(
    user_id: str,
    file: UploadFile,
    service: FileService = Depends(get_file_service),  # Injected!
):
    # Service is pre-configured with all dependencies
    success, file_id, size, error = await service.upload_file_encrypted(user_id, file)
    # FileService doesn't know about GridFS, encryption, or RabbitMQ
    # Easy to test (mock the interfaces), easy to swap backends
```

---

## Dependency Flow

```
Request
  ↓
FastAPI Router (presentation/api/files.py)
  ↓
get_file_service() dependency factory (presentation/dependencies.py)
  ↓
FileService (application/services.py)
  ├→ calls IFileRepository.save_file_stream()
  │   └→ MongoGridFSRepository (infrastructure/database/)
  │
  ├→ calls ICryptoService.generate_key_pair()
  │   └→ AESCryptoService (infrastructure/security/)
  │
  └→ calls IEventPublisher.publish_upload()
      └→ RabbitMQEventPublisher (infrastructure/messaging/)
```

Each layer depends only on abstractions, never on concrete implementations.

---

## Testing

### Before (Hard to Test)
```python
# Can't mock GridFS, would need a real MongoDB
# Can't mock RabbitMQ, would need a real broker
async def test_upload():
    result = await FileService.upload_encrypted_file(user_id, file)
    # Can't isolate business logic
```

### After (Easy to Test)
```python
# Mock the interfaces
class MockRepository(IFileRepository):
    async def save_file_stream(self, file, stream):
        return "mock_file_id"

class MockCrypto(ICryptoService):
    def generate_key_pair(self):
        return b"key", b"nonce"

class MockPublisher(IEventPublisher):
    async def publish_upload(self, user_id, file_id, size):
        pass

# Inject mocks
service = FileService(
    repo=MockRepository(),
    crypto=MockCrypto(),
    event_publisher=MockPublisher()
)

# Test business logic in isolation
result = await service.upload_file_encrypted(user_id, file)
assert result[0] == True
```

---

## Swapping Technologies (Example)

### Scenario: Migrate from MongoDB to AWS S3

**Step 1**: Create new repository
```python
# app/infrastructure/database/s3_repository.py
class S3Repository(IFileRepository):
    def __init__(self, s3_client):
        self.s3 = s3_client
    
    async def save_file_stream(self, file: File, stream: AsyncGenerator) -> str:
        # S3 upload logic
        ...
    # Implement other methods
```

**Step 2**: Update dependency injection
```python
# app/presentation/dependencies.py
async def get_file_service() -> FileService:
    repo = S3Repository(get_s3_client())  # ← Changed
    crypto = AESCryptoService()
    publisher = RabbitMQEventPublisher()
    
    return FileService(repo, crypto, publisher)
```

**Step 3**: Done!
- All endpoints work unchanged
- All business logic works unchanged
- Only the repository swapped

---

## Configuration & Environment

No changes needed. Existing environment variables are used:
- `ENCRYPTION_MASTER_KEY` → `AESCryptoService`
- `MONGO_URL`, `MONGO_DB_NAME` → `MongoGridFSRepository`
- `RABBITMQ_URL`, `RABBITMQ_QUEUE` → `RabbitMQEventPublisher`

---

## Future Enhancements

### 1. Add Caching Layer
```python
class CachedRepository(IFileRepository):
    def __init__(self, repo: IFileRepository, cache: ICache):
        self.repo = repo
        self.cache = cache
    
    async def get_file_metadata(self, file_id):
        cached = await self.cache.get(file_id)
        if cached:
            return cached
        result = await self.repo.get_file_metadata(file_id)
        await self.cache.set(file_id, result)
        return result
```

### 2. Add Logging Decorator
```python
class LoggingRepository(IFileRepository):
    def __init__(self, repo: IFileRepository):
        self.repo = repo
    
    async def save_file_stream(self, file, stream):
        logger.info(f"Saving {file.filename}")
        result = await self.repo.save_file_stream(file, stream)
        logger.info(f"Saved with ID {result}")
        return result
```

### 3. Support Multiple Encryption Algorithms
```python
# Easily switch between AES and ChaCha20
crypto = ChaCha20CryptoService()  # Instead of AESCryptoService()
service = FileService(repo, crypto, publisher)
```

### 4. Async Event Publishing
```python
class AsyncRabbitMQEventPublisher(IEventPublisher):
    # Current implementation is sync, wrapped in async
    # Could be replaced with fully async aiormq
    ...
```

---

## Summary of Principles Applied

| Principle | Implementation |
|-----------|-----------------|
| **Dependency Inversion** | Service depends on interfaces, not implementations |
| **Single Responsibility** | Each class has one reason to change |
| **Open/Closed** | Open for extension (new implementations), closed for modification |
| **Liskov Substitution** | Any IFileRepository implementation works with FileService |
| **Interface Segregation** | Small, focused interfaces (not fat interfaces) |
| **Separation of Concerns** | Clear layers with distinct responsibilities |

---

## Files Changed Summary

| File | Status | Reason |
|------|--------|--------|
| `app/domain/entities.py` | 🆕 Created | Domain entity |
| `app/domain/interfaces.py` | 🆕 Created | Abstract contracts |
| `app/application/dtos.py` | 🆕 Created | DTOs moved here |
| `app/application/services.py` | 🆕 Created | Business logic (refactored) |
| `app/infrastructure/database/mongo_repository.py` | 🆕 Created | MongoDB implementation |
| `app/infrastructure/security/encryption.py` | 🆕 Created | Encryption implementation |
| `app/infrastructure/messaging/rabbitmq_publisher.py` | 🆕 Created | Event publishing implementation |
| `app/presentation/dependencies.py` | 🆕 Created | Dependency injection |
| `app/presentation/api/files.py` | ✏️ Updated | Uses injected service |
| `app/services/file_service.py` | ❌ Deprecated | Replaced by application/services.py |
| `app/models/file.py` | ❌ Deprecated | Replaced by domain/entities.py |
| `app/schemas/file.py` | ⚠️ Partial | Schemas moved to application/dtos.py |
| `app/utils/crypto.py` | ⚠️ Deprecated | Moved to infrastructure/security/encryption.py |

---

## Quick Start

### Testing the Refactored Code

```bash
# Verify imports work
python -c "from app.application.services import FileService; print('✓')"
python -c "from app.domain.entities import File; print('✓')"
python -c "from app.infrastructure.database.mongo_repository import MongoGridFSRepository; print('✓')"

# Run existing tests (should pass unchanged)
pytest backend/media_service/app/
```

### Adding a New Repository Implementation

```python
# app/infrastructure/database/my_storage_repository.py
from app.domain.interfaces import IFileRepository

class MyStorageRepository(IFileRepository):
    async def save_file_stream(self, file, stream):
        # Your implementation
        pass
    
    # Implement other methods...
```

Then update `app/presentation/dependencies.py`:
```python
from app.infrastructure.database.my_storage_repository import MyStorageRepository

async def get_file_service() -> FileService:
    repo = MyStorageRepository()  # ← Use your new implementation
    ...
```

---

## Validation Checklist

✅ All imports resolve without errors  
✅ Dependency injection container builds successfully  
✅ FastAPI endpoints inject service correctly  
✅ Business logic is technology-agnostic  
✅ All interfaces are implemented  
✅ No circular dependencies  
✅ Domain layer has no external dependencies  
✅ Each layer has clear responsibility  
✅ Easy to mock for testing  
✅ Easy to swap implementations  

---

**End of Refactoring Document**
