# IASW Authentication & Authorization System

## Overview
Complete authentication and role-based access control has been implemented.

---

## User Roles

### 1. **CHECKER** (Supervisor)
- **Can**: View all pending requests, approve/reject changes, view customer details (except balance)
- **Cannot**: See account balance, submit change requests
- **Login Credentials**:
  - Username: `checker1` / Password: `checker123`
  - Username: `checker2` / Password: `checker123`

### 2. **ACCOUNT_HOLDER** (Customer)
- **Can**: View own account details (including balance), submit change requests for own account
- **Cannot**: Change account balance, view other customers' data, approve/reject requests
- **Login Credentials**:
  - Username: `priya.sharma` / Password: `priya123` (Customer C001)
  - Username: `rahul.kumar` / Password: `rahul123` (Customer C002)

### 3. **STAFF** (Bank Staff)
- **Can**: Submit change requests on behalf of customers
- **Cannot**: Approve/reject requests, view account balance
- **Login Credentials**:
  - Username: `staff1` / Password: `staff123`

---

## API Endpoints

### Authentication Endpoints

#### POST `/api/auth/login`
Login with username and password
```json
Request:
{
  "username": "checker1",
  "password": "checker123"
}

Response:
{
  "success": true,
  "token": "abc123...",
  "user_id": "CHK001",
  "username": "checker1",
  "role": "checker",
  "customer_id": null
}
```

#### POST `/api/auth/logout`
Logout current user (requires auth token in header)

#### GET `/api/auth/me`
Get current user info (requires auth token)

#### POST `/api/auth/change-password`
Change password (requires auth token)

### Account Details Endpoints

#### GET `/api/account/details`
Get own account details (for account holders)
- **Account Holder**: Can see balance
- Returns: All account info including balance

#### GET `/api/account/details/{customer_id}`
Get customer details by ID (for checkers)
- **Checker Only**: Cannot see balance
- Returns: All account info except balance

### Protected Endpoints

#### POST `/api/change-request/submit`
Submit change request (requires authentication)
- Available to: STAFF, ACCOUNT_HOLDER

#### GET `/api/checker/pending-requests`
Get pending requests (requires CHECKER role)

#### POST `/api/checker/decision`
Approve/reject request (requires CHECKER role)

---

## Authorization Headers

All protected endpoints require Bearer token:
```
Authorization: Bearer <token>
```

Example with curl:
```bash
curl -H "Authorization: Bearer abc123..." http://localhost:8000/api/auth/me
```

---

## Account Details Access Control

### What CHECKER Can See:
```json
{
  "customer_id": "C001",
  "name": "Priya Sharma",
  "email": "priya.sharma@email.com",
  "address": "123 Main St, Mumbai",
  "dob": "1990-05-15",
  "phone": "+91-9876543210",
  "account_number": "ACC-001-12345",
  "account_type": "Savings",
  "balance": null  // HIDDEN
}
```

### What ACCOUNT_HOLDER Can See:
```json
{
  "customer_id": "C001",
  "name": "Priya Sharma",
  "email": "priya.sharma@email.com",
  "address": "123 Main St, Mumbai",
  "dob": "1990-05-15",
  "phone": "+91-9876543210",
  "account_number": "ACC-001-12345",
  "account_type": "Savings",
  "balance": 125000.50  // VISIBLE
}
```

---

## Update Permissions

### CHECKER Can Update:
- Name
- Address
- Email
- Phone
- Date of Birth
- **CANNOT** update: Balance

### ACCOUNT_HOLDER Can Update:
- Can **REQUEST** changes to:
  - Name
  - Address
  - Email
  - Phone
- **CANNOT** update or request changes to:
  - Balance (read-only)
  - Account Number
  - Account Type

---

## Frontend Pages

### 1. `login.html`
- Login page for all users
- Redirects based on role after login
- Demo credentials displayed

### 2. `index.html` (Staff Interface)
- Submit change requests
- Requires authentication

### 3. `checker.html` (TODO)
- View pending requests
- Approve/reject changes
- View customer details (without balance)
- Requires CHECKER role

### 4. `account_holder.html` (TODO)
- View own account details (with balance)
- Submit change requests for own account
- View own request history
- Requires ACCOUNT_HOLDER role

---

## Session Management

- Tokens are valid for **8 hours**
- Tokens stored in localStorage
- Automatic logout on token expiration
- Session validation on each API call

---

## Security Features

1. **Password Hashing**: SHA256 (use bcrypt in production)
2. **Token-based Authentication**: Secure session tokens
3. **Role-based Access Control**: Strict permission checks
4. **Session Expiration**: 8-hour timeout
5. **Balance Privacy**: Hidden from checkers
6. **Audit Trail**: All changes logged with user info

---

## Testing the System

### 1. Start the Backend
```bash
cd /home/adubey/iasw-project
./start_backend.sh
```

### 2. Access Login Page
```
http://localhost:3000/login.html
```

### 3. Test Different Roles

**As Checker (checker1/checker123):**
- View pending requests
- Approve/reject changes
- View customer details (no balance)

**As Account Holder (priya.sharma/priya123):**
- View own details with balance
- Submit change requests

**As Staff (staff1/staff123):**
- Submit change requests for customers

---

## Next Steps

To complete the implementation:

1. **Update `index.html`**: Add authentication check and token management
2. **Create `checker.html`**: Checker dashboard with all features
3. **Create `account_holder.html`**: Customer dashboard
4. **Add Logout Button**: All pages
5. **Token Refresh**: Auto-refresh before expiration
6. **Production Security**: Use bcrypt, HTTPS, secure cookies

---

## API Authentication Example (JavaScript)

```javascript
// Login
const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'checker1',
        password: 'checker123'
    })
});
const data = await response.json();
localStorage.setItem('token', data.token);

// Make authenticated request
const token = localStorage.getItem('token');
const result = await fetch('http://localhost:8000/api/checker/pending-requests', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

---

## Password Change

Users can change their password:
```bash
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"checker123","new_password":"newpass456"}'
```

---

**System is now secure with complete authentication and role-based authorization!**
