# FlowDock

A comprehensive, enterprise-grade file management and sharing platform with end-to-end encryption, multi-device session management, and advanced security features.

## 🎯 Project Overview

FlowDock is a full-stack application designed to securely store, organize, and share files with granular permission controls. It provides a seamless user experience across web and mobile platforms with features like folder hierarchies, public sharing links, virus scanning, and complete encryption of user data.

### Key Highlights
- **End-to-End Encryption**: All files are encrypted using envelope encryption with AES-256
- **Hierarchical File Organization**: Create and manage nested folder structures
- **Public Sharing**: Generate secure public links with password protection and expiration
- **Multi-Device Sessions**: Manage active sessions across multiple devices
- **Activity Logging**: Complete audit trail of all user actions
- **Quota Management**: Track and enforce storage quotas per user
- **Virus Scanning**: Integration with virus scanning for uploaded files
- **JWT Authentication**: Secure token-based authentication with refresh token flow
- **Rate Limiting**: Protection against abuse with configurable rate limiting
- **Role-Based Access Control**: Admin and user roles with specific permissions

---

## 🏗️ Architecture

FlowDock follows a **microservices architecture** with three main services:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│              Single Page Application (SPA)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Nginx Gateway (Reverse Proxy)              │
│            Routes requests to backend services              │
└──────┬───────────────────────────────────────┬──────────────┘
       │                                       │
       │ HTTP/REST                            │ HTTP/REST
       │                                       │
   ┌───▼────────────────────┐    ┌────────────▼──────────────┐
   │  Auth Service          │    │  Media Service           │
   │  ────────────────      │    │  ──────────────          │
   │ • User Management      │    │ • File Upload/Download   │
   │ • JWT Tokens           │    │ • Folder Management      │
   │ • 2FA/TOTP             │    │ • File Encryption        │
   │ • Email Verification   │    │ • Public Sharing         │
   │ • Password Recovery    │    │ • Virus Scanning         │
   │ • Activity Logging     │    │ • Quota Management       │
   │ • OAuth Integration    │    │ • Access Control         │
   └───┬────────────────────┘    └────────────┬──────────────┘
       │                                      │
       └───────────┬────────────────┬─────────┘
                   │                │
           ┌───────▼────────┐  ┌───▼────────────┐
           │   PostgreSQL   │  │   MongoDB      │
           │   (Auth DB)    │  │   (Media DB)   │
           └────────────────┘  └────────────────┘
```

---

## 📁 Project Structure

```
FlowDock/
├── backend/
│   ├── auth_service/                  # Authentication & User Management Service
│   │   ├── app/
│   │   │   ├── application/           # Business logic & services
│   │   │   │   ├── services.py        # Core auth services
│   │   │   │   ├── oauth_service.py   # OAuth integration
│   │   │   │   ├── quota_service.py   # Quota management
│   │   │   │   ├── twofa_service.py   # 2FA/TOTP handling
│   │   │   │   └── user_util_service.py
│   │   │   ├── core/                  # Configuration & constants
│   │   │   ├── domain/                # Domain entities & interfaces
│   │   │   ├── infrastructure/        # Database, email, OAuth clients
│   │   │   ├── presentation/          # API endpoints & dependencies
│   │   │   ├── utils/                 # Security, email, TOTP utilities
│   │   │   └── main.py                # FastAPI application entry point
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── run.sh
│   │
│   ├── media_service/                 # File Management & Storage Service
│   │   ├── app/
│   │   │   ├── application/           # Business logic & services
│   │   │   │   ├── services.py        # File & folder operations
│   │   │   │   ├── public_folder_links_service.py  # Public sharing
│   │   │   │   └── folder_sharing_service.py       # Folder access control
│   │   │   ├── core/                  # Configuration
│   │   │   ├── domain/                # Domain entities (File, Folder, etc.)
│   │   │   ├── infrastructure/        # MongoDB, GridFS, encryption
│   │   │   ├── models/                # Data models
│   │   │   ├── presentation/          # API endpoints
│   │   │   │   ├── api/files.py       # File upload/download endpoints
│   │   │   │   ├── api/folders.py     # Folder CRUD endpoints
│   │   │   │   ├── api/folder_sharing.py
│   │   │   │   ├── api/public_folder_links.py
│   │   │   │   └── api/virus_scan.py
│   │   │   ├── schemas/               # Request/Response schemas
│   │   │   ├── services/              # Additional services
│   │   │   ├── utils/                 # Validators, security
│   │   │   └── main.py                # FastAPI application
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── tests/                     # Unit & integration tests
│   │
│   └── gateway/                       # Nginx Configuration
│       └── nginx.conf                 # Reverse proxy & routing rules
│
├── frontend/
│   └── frontend/
│       ├── src/
│       │   ├── components/            # Reusable UI components
│       │   │   ├── FolderUploadComponent.jsx    # Folder upload handler
│       │   │   ├── FileDetailsModal.jsx         # File metadata display
│       │   │   ├── FolderShareModal.jsx         # Sharing interface
│       │   │   ├── ShareModal.jsx               # Share dialog
│       │   │   └── ProtectedRoute.jsx           # Auth guard
│       │   ├── context/               # React Context for state
│       │   │   └── AuthContext.jsx    # Authentication state
│       │   ├── hooks/                 # Custom React hooks
│       │   │   ├── useAuth.js         # Auth logic
│       │   │   └── useFileOperations.js
│       │   ├── layout/                # Layout components
│       │   │   ├── Header.jsx
│       │   │   ├── LeftNavBar.jsx
│       │   │   ├── TopNavBar.jsx
│       │   │   ├── Footer.jsx
│       │   │   └── MainLayout.jsx
│       │   ├── pages/                 # Page components
│       │   │   ├── dashboard/
│       │   │   │   ├── Dashboard.jsx  # Main file dashboard
│       │   │   │   ├── MyFiles.jsx    # File browser
│       │   │   │   ├── Shared.jsx     # Shared files view
│       │   │   │   ├── PublicLinks.jsx # Public shares
│       │   │   │   ├── Settings.jsx   # User settings
│       │   │   │   └── Trash.jsx      # Trash/deleted files
│       │   │   ├── auth/              # Authentication pages
│       │   │   │   ├── Login.jsx
│       │   │   │   ├── SignUp.jsx
│       │   │   │   ├── TwoFactorAuth.jsx
│       │   │   │   ├── VerifyEmail.jsx
│       │   │   │   ├── PassRecovery.jsx
│       │   │   │   └── OAuthCallback.jsx
│       │   │   ├── PublicFolderBrowser.jsx  # Public folder navigation
│       │   │   ├── Home.jsx
│       │   │   ├── Help.jsx
│       │   │   ├── Terms.jsx
│       │   │   ├── Privacy.jsx
│       │   │   └── AdminUserManagement.jsx
│       │   ├── services/              # API client
│       │   │   └── api.js             # HTTP requests to backend
│       │   ├── resources/             # Static assets
│       │   ├── test/                  # Frontend tests
│       │   ├── App.jsx                # Main app component
│       │   ├── main.jsx               # React entry point
│       │   └── index.css              # Global styles
│       ├── package.json
│       ├── vite.config.js             # Vite configuration
│       ├── vitest.config.js           # Vitest configuration
│       ├── tailwind.config.js         # Tailwind CSS config
│       ├── postcss.config.cjs
│       ├── eslint.config.js
│       ├── Dockerfile
│       └── README.md
│
├── grafana/                           # Monitoring & Dashboards
│   └── provisioning/
│       ├── dashboards/
│       │   ├── flowdock-dashboard.json
│       │   └── dashboards.yml
│       └── datasources/
│           └── prometheus.yml
│
├── UML/                               # Architecture Diagrams
│   ├── Activity Logging.puml
│   ├── Authentication.puml
│   ├── File Delete.puml
│   ├── File Download.puml
│   ├── File Sharing.puml
│   ├── File Upload.puml
│   ├── Folder Management.puml
│   ├── Multi-Device Session Management.puml
│   ├── OTP Generation & Verification.puml
│   ├── Password Recovery.puml
│   ├── Rate-Limit Pipeline.puml
│   ├── Refresh Token Flow.puml
│   ├── TOTP.puml
│   └── Virus Scanning.puml
│
├── docker-compose.yml                # Docker Compose orchestration
├── prometheus.yml                     # Prometheus metrics config
├── nginx.conf                         # Primary Nginx config
└── README.md                          # This file
```

---

## ✨ Features

### 🔐 Security
- **End-to-End Encryption**: AES-256 envelope encryption for all files
- **JWT Authentication**: Bearer token authentication with refresh token flow
- **Two-Factor Authentication**: TOTP (Time-based One-Time Password) support
- **Password Hashing**: bcrypt with salt for secure password storage
- **Session Management**: Track and manage active sessions across devices
- **Rate Limiting**: Configurable rate limits on sensitive endpoints
- **Access Control**: Granular permissions for folders and files

### 📁 File Management
- **File Upload/Download**: Stream-based upload/download with progress tracking
- **Folder Hierarchies**: Create, rename, move, and delete folders with parent-child relationships
- **File Search**: Full-text search across files and folders
- **Virus Scanning**: Integration with virus scanning on upload
- **File Versioning**: Track file history and metadata
- **Encryption Metadata**: Store nonce, key, and encryption status

### 🔗 Sharing & Collaboration
- **Public Links**: Generate secure shareable links with optional passwords
- **Expiring Links**: Set expiration dates for public links
- **Folder Sharing**: Share entire folder hierarchies with specific users
- **Permission Control**: View-only, download, or edit permissions
- **Activity Logging**: Complete audit trail of share events

### 📊 User Management
- **User Registration**: Email verification required
- **Profile Management**: Update profile information and preferences
- **Password Recovery**: Secure password reset via email
- **Quota Management**: Storage quota per user with tracking
- **Admin Dashboard**: User management and system monitoring
- **OAuth Integration**: Support for third-party OAuth providers

### 📱 Multi-Device Support
- **Session Tracking**: See active sessions across devices
- **Device Management**: Remove/revoke sessions from specific devices
- **Responsive UI**: Mobile-friendly interface
- **Adaptive Layout**: Works on desktop, tablet, and mobile

### 📝 Activity & Monitoring
- **Activity Logging**: Track file uploads, downloads, deletions, shares
- **Audit Trail**: Complete history for compliance
- **Prometheus Metrics**: System metrics collection
- **Grafana Dashboards**: Visual monitoring and analytics
- **Error Tracking**: Comprehensive error logging

---

## 🛠️ Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.9+ | Core backend language |
| **Framework** | FastAPI | Modern async web framework |
| **Auth DB** | PostgreSQL | User, session, and auth data |
| **Media DB** | MongoDB | File storage and metadata |
| **Storage** | GridFS (MongoDB) | Large file storage |
| **Encryption** | cryptography library | AES-256 encryption |
| **Authentication** | PyJWT | JWT token handling |
| **Email** | SMTP | Email notifications |
| **Async** | asyncio | Asynchronous operations |
| **Testing** | pytest | Unit and integration tests |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | JavaScript (ES6+) | Frontend language |
| **Framework** | React 18 | UI framework with hooks |
| **Build Tool** | Vite | Fast bundler and dev server |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **HTTP Client** | Fetch API | API communication |
| **Testing** | Vitest | Frontend test framework |
| **Linting** | ESLint | Code quality |
| **State** | React Context | State management |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Application containerization |
| **Orchestration** | Docker Compose | Multi-container orchestration |
| **Reverse Proxy** | Nginx | API gateway and routing |
| **Monitoring** | Prometheus | Metrics collection |
| **Visualization** | Grafana | Metrics dashboard |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local development)
- Node.js 16+ (for frontend development)
- Git

### Quick Start with Docker Compose

1. **Clone the repository**
```bash
git clone <repository-url>
cd FlowDock
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Access the application**
- Frontend: http://localhost
- API: http://localhost/api
- Grafana: http://localhost:3000 (admin/admin)

### Local Development

#### Backend Setup (Auth Service)
```bash
cd backend/auth_service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.sh
```

#### Backend Setup (Media Service)
```bash
cd backend/media_service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.sh
```

#### Frontend Setup
```bash
cd frontend/frontend
npm install
npm run dev
```

---

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/password-recovery` - Initiate password reset
- `POST /api/auth/reset-password` - Complete password reset

### File Endpoints
- `POST /media/upload/{user_id}` - Upload single file
- `POST /media/upload-folder/{user_id}` - Upload folder with structure
- `GET /media/file/{file_id}/download` - Download file
- `DELETE /media/file/{file_id}` - Delete file
- `GET /media/user/{user_id}/content` - List root files and folders
- `PATCH /media/file/{file_id}` - Update file metadata

### Folder Endpoints
- `POST /media/folders/{user_id}` - Create folder
- `GET /media/folders/{folder_id}/contents` - List folder contents
- `PATCH /media/folders/{folder_id}` - Update folder
- `DELETE /media/folders/{folder_id}` - Delete folder
- `POST /media/folders/{folder_id}/move` - Move folder

### Sharing Endpoints
- `POST /media/folders/{folder_id}/share` - Share folder with users
- `GET /media/folders/{folder_id}/shares` - List folder shares
- `DELETE /media/folders/{folder_id}/shares/{share_id}` - Revoke share
- `POST /media/public-links` - Generate public link
- `GET /public/folders/{token}/contents` - Access public folder
- `GET /public/folders/{token}/download-file/{file_id}` - Download from public link

### User Endpoints
- `GET /api/users/{user_id}` - Get user profile
- `PATCH /api/users/{user_id}` - Update user profile
- `GET /api/users/{user_id}/quota` - Get quota info
- `POST /api/users/{user_id}/sessions` - List active sessions
- `DELETE /api/users/{user_id}/sessions/{session_id}` - Revoke session

---

## 🔄 Core Workflows

### File Upload with Structure Preservation
```
User Selects Folder
    ↓
FolderUploadComponent collects files with webkitRelativePath
    ↓
POST /media/upload-folder/ with FormData
    ↓
Backend parses folder structure from paths
    ↓
Creates folder hierarchy in MongoDB
    ↓
Files uploaded to GridFS with folder_id metadata
    ↓
Folder structure preserved in database
```

### End-to-End Encryption Flow
```
User uploads file
    ↓
Generate random AES-256 key and nonce
    ↓
Encrypt file content with AES-256
    ↓
Wrap file key with KEK (Key Encryption Key)
    ↓
Store encrypted file in GridFS
    ↓
Store wrapped key and nonce in metadata
    ↓
User can only decrypt with access to wrapped key
```

### Public Folder Sharing
```
User creates public link
    ↓
Generate secure token
    ↓
Set expiration date and password (optional)
    ↓
Share token with others
    ↓
Recipients access /public/folders/{token}
    ↓
Browse entire folder hierarchy without login
    ↓
Download files from shared link
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend/media_service
pytest tests/

cd backend/auth_service
pytest tests/
```

### Run Frontend Tests
```bash
cd frontend/frontend
npm run test
```

### Test Coverage
```bash
pytest --cov=app tests/
npm run test -- --coverage
```

---

## 📊 Monitoring

### Prometheus Metrics
- Access metrics at: http://localhost:9090
- Metrics available at: `/metrics` endpoint on each service

### Grafana Dashboards
- URL: http://localhost:3000
- Default login: admin/admin
- Pre-configured dashboards:
  - FlowDock Overview
  - Service Health
  - API Performance
  - Error Rates

---

## 🔧 Configuration

### Environment Variables

#### Auth Service (.env)
```
DATABASE_URL=postgresql://user:password@db:5432/flowdock_auth
JWT_SECRET=your-secret-key-here
JWT_EXPIRY=3600
REFRESH_TOKEN_EXPIRY=604800
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Media Service (.env)
```
MONGODB_URL=mongodb://mongo:27017/flowdock_media
AUTH_SERVICE_URL=http://auth_service:8000
ENCRYPTION_KEY=your-kek-key-here
STORAGE_LIMIT=1099511627776  # 1TB in bytes
```

---

## 🐛 Troubleshooting

### Common Issues

**Files not appearing after upload**
- Check MongoDB connection
- Verify folder_id is set in file metadata
- Check GridFS storage space

**Authentication failing**
- Verify JWT_SECRET is consistent
- Check token expiration
- Ensure refresh token endpoint is accessible

**Encryption errors**
- Verify cryptography library is installed
- Check encryption key format
- Review nonce generation

**Performance issues**
- Check MongoDB indexing on folder_id and owner
- Monitor GridFS chunk size
- Review Prometheus metrics in Grafana

---

## 📝 Development Guidelines

### Code Structure
- Follow MVC pattern with domain-driven design
- Separate concerns: presentation, application, infrastructure
- Use dependency injection for testability
- Write comprehensive docstrings

### Database Design
- Use MongoDB for flexible schemas (files, folders)
- Use PostgreSQL for structured data (users, sessions)
- Index frequently queried fields
- Use GridFS for large file storage

### API Design
- RESTful endpoints with proper HTTP methods
- Consistent error response format
- Pagination for list endpoints
- Comprehensive API documentation

### Security Best Practices
- Always validate user input
- Use parameterized queries
- Hash passwords with bcrypt
- Encrypt sensitive data at rest
- Use HTTPS in production
- Implement rate limiting

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Process
- Update README.md with any new features
- Add tests for new functionality
- Follow the existing code style
- Ensure all tests pass
- Update API documentation if needed

---

## 🆘 Support

For support and questions:
- Open an issue on GitHub
- Check existing documentation
- Review UML diagrams for architecture details
- Check logs in Docker containers: `docker logs <container-name>`

---

## 🎯 Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced search with full-text indexing
- [ ] Real-time collaboration features
- [ ] File synchronization across devices
- [ ] Integration with cloud storage providers
- [ ] Advanced reporting and analytics
- [ ] Two-factor authentication via SMS
- [ ] Hardware security key support
- [ ] Advanced backup and disaster recovery

---

## 📞 Contact

For questions or inquiries, please reach out to the development team.

---

**Last Updated**: January 2026
**Version**: 1.0.0
