# Frontend Testing Guide

## Setup

Install dependencies:
```bash
npm install
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- src/hooks/__tests__/useAuth.test.js

# Watch mode
npm test -- --watch
```

## Test Structure

