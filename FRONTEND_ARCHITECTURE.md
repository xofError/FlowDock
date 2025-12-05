# Frontend Architecture Guide

## Overview
The frontend is a React application built with Vite, featuring authentication flows and file management UI.

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx               # Entry point
│   ├── App.jsx                # Root component with routing
│   ├── index.css              # Global styles
│   │
│   ├── pages/                 # Page components (route views)
│   │   └── auth/              # Authentication flow pages
│   │       ├── Login.jsx      # Login page
│   │       ├── SignUp.jsx     # Registration page
│   │       ├── VerifyEmail.jsx # Email verification
│   │       ├── TwoFactorAuth.jsx # 2FA setup/verification
│   │       ├── PassRecovery.jsx # Password recovery initiation
│   │       ├── PassRecoverVerify.jsx # Verify recovery token
│   │       └── ResetPassword.jsx # Reset password page
│   │
│   ├── components/            # Reusable UI components
│   │   ├── forms/             # Form components
│   │   │   ├── LoginForm.jsx
│   │   │   ├── SignUpForm.jsx
│   │   │   └── ...
│   │   ├── common/            # Shared components
│   │   │   ├── Header.jsx
│   │   │   ├── Button.jsx
│   │   │   ├── Input.jsx
│   │   │   ├── Modal.jsx
│   │   │   └── ...
│   │   └── layout/            # Layout components
│   │       ├── Sidebar.jsx
│   │       └── Footer.jsx
│   │
│   ├── layout/                # Layout wrappers
│   │   └── MainLayout.jsx     # Main app layout
│   │
│   ├── services/              # API client services (create these)
│   │   ├── api.js             # Axios/fetch client setup
│   │   ├── authService.js     # Auth API calls
│   │   └── mediaService.js    # File API calls
│   │
│   ├── hooks/                 # Custom React hooks (create these)
│   │   ├── useAuth.js         # Auth state management
│   │   ├── useApi.js          # API request handling
│   │   └── ...
│   │
│   ├── context/               # React Context API (create these)
│   │   ├── AuthContext.jsx    # Auth state/provider
│   │   └── UserContext.jsx    # User state/provider
│   │
│   ├── utils/                 # Utility functions (create these)
│   │   ├── validation.js      # Form validators
│   │   ├── constants.js       # App constants
│   │   ├── localStorage.js    # Storage utilities
│   │   └── formatters.js      # Data formatters
│   │
│   ├── resources/
│   │   ├── fonts/
│   │   │   └── fonts.css
│   │   ├── icons/             # Icon components/SVGs
│   │   └── images/            # Static images
│   │
│   └── App.css
│
├── public/                    # Static assets
├── Dockerfile                 # Production container
├── .dockerignore              # Docker ignore rules
├── package.json               # Dependencies
├── vite.config.js             # Vite configuration
├── index.html                 # HTML template
├── eslint.config.js           # ESLint configuration
├── postcss.config.cjs         # PostCSS configuration (Tailwind)
├── tailwind.config.js         # Tailwind CSS configuration
└── README.md
```

## Key Technologies

- **React 18**: UI library
- **Vite**: Build tool and dev server
- **React Router DOM**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **ESLint**: Code quality

## Recommended Additions

### State Management
```bash
npm install zustand  # or Redux/Jotai/Recoil
```

### API Client
```bash
npm install axios
```

### Form Handling
```bash
npm install react-hook-form zod
```

### HTTP Client
```bash
npm install fetch-api  # Already using native fetch
```

## Page & Component Organization

### Auth Flow Pages (`src/pages/auth/`)

1. **Login.jsx**
   - Email/username and password input
   - "Remember me" checkbox
   - "Forgot password" link
   - OAuth integration (optional)
   - Redirects to 2FA if enabled

2. **SignUp.jsx**
   - Email, username, password inputs
   - Password strength indicator
   - Terms & conditions checkbox
   - Redirects to email verification

3. **VerifyEmail.jsx**
   - OTP input (6-digit code)
   - Resend code functionality
   - Expiration countdown
   - Redirects to dashboard on success

4. **TwoFactorAuth.jsx**
   - TOTP setup (display QR code)
   - Backup codes display
   - TOTP verification input
   - Enable/disable 2FA option

5. **PassRecovery.jsx**
   - Email input
   - Submit recovery request
   - Confirmation message

6. **PassRecoverVerify.jsx**
   - Recovery token + OTP verification
   - New password input
   - Password strength validation

7. **ResetPassword.jsx**
   - Old password input
   - New password input
   - Confirmation password input

### Common Components (`src/components/common/`)

Should include:
- **Button.jsx** - Styled button component
- **Input.jsx** - Reusable input field
- **Modal.jsx** - Modal dialog
- **Alert.jsx** - Alert/toast notifications
- **Spinner.jsx** - Loading indicator
- **Card.jsx** - Card layout component

### Form Components (`src/components/forms/`)

Should include:
- **LoginForm.jsx** - Login form logic
- **SignUpForm.jsx** - Registration form logic
- **PasswordResetForm.jsx** - Reset form logic
- **OTPInput.jsx** - OTP verification component

## API Integration Examples

### Authentication Service (port 8000)

```javascript
// services/authService.js
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

export const authService = {
  login: (email, password) => 
    fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    }).then(r => r.json()),
  
  signup: (username, email, password) => 
    fetch(`${API_URL}/auth/signup`, {
      method: 'POST',
      body: JSON.stringify({ username, email, password })
    }).then(r => r.json()),
  
  verifyEmail: (token) =>
    fetch(`${API_URL}/auth/verify-email`, {
      method: 'POST',
      body: JSON.stringify({ token })
    }).then(r => r.json()),
  
  setup2FA: () =>
    fetch(`${API_URL}/auth/2fa/setup`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json()),
};
```

### Media Service (port 8001)

```javascript
// services/mediaService.js
const API_URL = process.env.VITE_MEDIA_API_URL || 'http://localhost:8001';

export const mediaService = {
  uploadFile: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return fetch(`${API_URL}/files/upload`, {
      method: 'POST',
      body: formData,
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json());
  },
  
  listFiles: () =>
    fetch(`${API_URL}/files`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json()),
  
  shareFile: (fileId, options) =>
    fetch(`${API_URL}/files/${fileId}/share`, {
      method: 'POST',
      body: JSON.stringify(options),
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json()),
};
```

## Routing Structure

```javascript
// App.jsx
import { Routes, Route, Navigate } from 'react-router-dom';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" />} />
      
      {/* Auth Routes (Public) */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/2fa" element={<TwoFactorAuth />} />
      <Route path="/pass-recovery" element={<PassRecovery />} />
      <Route path="/pass-recovery-verify" element={<PassRecoverVerify />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      
      {/* Protected Routes */}
      {/* Add Dashboard, FileManager, etc. */}
    </Routes>
  );
}
```

## Authentication Flow

### Login Flow
```
1. User enters credentials on Login page
2. Frontend calls POST /auth/login
3. Backend returns JWT token
4. Frontend stores token (localStorage/sessionStorage)
5. If 2FA enabled → redirect to TwoFactorAuth
6. If 2FA disabled → redirect to Dashboard
7. Subsequent requests include Authorization header
```

### Signup Flow
```
1. User fills signup form
2. Frontend calls POST /auth/signup
3. Backend sends verification email
4. User redirected to VerifyEmail page
5. User enters OTP from email
6. Frontend calls POST /auth/verify-email
7. Backend marks email as verified
8. Redirect to Dashboard or prompt 2FA setup
```

## Best Practices

### Component Development
- ✅ Use functional components with hooks
- ✅ Separate UI logic from business logic
- ✅ Create reusable components
- ✅ Use props for configuration
- ✅ Handle loading and error states

### State Management
- ✅ Use Context API for global state
- ✅ Use useState for local component state
- ✅ Use useReducer for complex state
- ✅ Avoid prop drilling with Context

### Performance
- ✅ Lazy load routes with React.lazy()
- ✅ Memoize expensive components (React.memo)
- ✅ Use useCallback for callbacks
- ✅ Optimize re-renders with proper keys

### Security
- ✅ Store JWT in secure httpOnly cookies (preferred)
- ✅ Or use sessionStorage (not localStorage for sensitive data)
- ✅ Include token in Authorization header
- ✅ Handle token expiration gracefully
- ✅ Validate input on frontend (and backend)

### Error Handling
- ✅ Display user-friendly error messages
- ✅ Log errors for debugging
- ✅ Handle network failures
- ✅ Implement retry logic where appropriate

## Environment Variables

Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_MEDIA_API_URL=http://localhost:8001
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Development Commands

```bash
# Install dependencies
npm install

# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Build Docker image
docker build -t flowdock-frontend .

# Run in Docker
docker run -p 5173:5173 flowdock-frontend
```

## TODO: Next Steps

- [ ] Create API service layer (`services/`)
- [ ] Implement custom hooks (`hooks/`)
- [ ] Set up Context API for auth state (`context/`)
- [ ] Create reusable components (`components/common/`)
- [ ] Create form components with validation
- [ ] Add loading and error handling
- [ ] Implement token refresh mechanism
- [ ] Add protected route wrapper
- [ ] Set up error boundary
- [ ] Add logging/monitoring
- [ ] Create unit tests
