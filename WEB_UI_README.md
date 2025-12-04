# New Web UI for PDFMathTranslate

## Overview

This is the new multi-user web interface for PDFMathTranslate with authentication and modern design.

## Features

✨ **Multi-User System**
- Username + password authentication
- User-specific configurations and API keys
- Admin user management
- Secure session management with JWT

🎨 **Modern Design**
- Glassmorphism effects
- Vibrant gradients and smooth animations
- Responsive layout
- Dark theme optimized

📁 **File Upload (Page 1)**
- Drag-and-drop file upload
- URL input support
- Real-time progress tracking
- Translation history


⚙️ **Settings (Page 2)**
- User password management
- Translation service configuration
- Model settings and API keys
- Advanced translation options
- User management (admin only)

## Quick Start

### 1. Install Dependencies

The new dependencies are already included in `pyproject.toml`:
- `bcrypt` - Password hashing
- `PyJWT` - Session token management
- `fastapi` - Web API framework
- `uvicorn` - ASGI server

Install or update:
```bash
pip install -e .
```

### 2. Start the Web UI

**Option 1: Using command line flag**
```bash
pdf2zh --gui --web-ui
```

**Option 2: Using environment variable**
```bash
export PDF2ZH_WEB_UI=1  # Linux/Mac
set PDF2ZH_WEB_UI=1     # Windows
pdf2zh --gui
```

### 3. Access the Web UI

Open your browser and navigate to:
```
http://localhost:7860
```

### 4. First-Time Setup

On first run, you'll be prompted to create an admin account:
1. Enter a username (minimum 3 characters)
2. Enter a password (minimum 6 characters)
3. Click "Create Admin Account"

## Usage

### For Regular Users

1. **Login**: Use your username and password to log in
2. **Upload**: Go to the Upload page to translate PDFs
   - Drag and drop a PDF file, or
   - Enter a URL to a PDF file
3. **Settings**: Configure your translation preferences
   - Select translation service
   - Enter API keys
   - Set source and target languages
   - Adjust advanced options

### For Administrators

Admins have additional capabilities:

1. **User Management**: Create and delete user accounts
2. **View All Users**: See all registered users and their details

## Architecture

### Backend

- **`auth.py`**: Multi-user authentication with bcrypt and JWT
- **`web_api.py`**: FastAPI REST API server
  - Authentication endpoints
  - File upload and translation
  - Settings management
  - User management (admin)

### Frontend

- **`static/login.html`**: Login and initial setup page
- **`static/upload.html`**: File upload and translation page
- **`static/settings.html`**: User settings and configuration
- **`static/css/style.css`**: Modern design system
- **`static/js/api.js`**: API client
- **`static/js/auth.js`**: Authentication utilities

### Data Storage

- **`data/users.db`**: SQLite database for users and sessions
- **`data/users/{username}/`**: User-specific data directories
  - `uploads/`: Uploaded PDF files
  - `outputs/`: Translated PDF files
  - `settings.json`: User settings
  - `history.json`: Translation history

## Security Features

🔒 **Password Security**
- Bcrypt hashing with salt
- Minimum password length enforcement
- Password change requires current password

🔑 **Session Management**
- JWT-based tokens
- 24-hour session expiration
- Automatic session cleanup

🛡️ **Data Isolation**
- Each user has isolated configuration
- API keys stored per-user
- No cross-user data access

## Switching Between UIs

### Use New Web UI (default with --web-ui)
```bash
pdf2zh --gui --web-ui
```

### Use Original Gradio UI
```bash
pdf2zh --gui
```

Both UIs can coexist. The original Gradio UI remains available as a fallback.

## API Endpoints

### Authentication
- `POST /api/auth/setup` - Initial admin setup
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/register` - Register new user (admin)
- `GET /api/auth/users` - List users (admin)
- `DELETE /api/auth/users/{username}` - Delete user (admin)

### Translation
- `POST /api/upload` - Upload PDF file
- `POST /api/translate` - Start translation
- `GET /api/translate/status/{task_id}` - Check translation status
- `GET /api/translate/history` - Get translation history
- `GET /api/translate/download/{task_id}` - Download translated file

### Settings
- `GET /api/settings` - Get user settings
- `POST /api/settings` - Update user settings
- `POST /api/settings/password` - Change password
- `POST /api/settings/reset` - Reset settings to default

## Troubleshooting

### Port Already in Use

Change the port in your config or use:
```bash
pdf2zh --gui --web-ui --server-port 8080
```

### Cannot Access from Other Devices

The server binds to `0.0.0.0` by default, so it should be accessible from other devices on your network at `http://<your-ip>:7860`

### Forgot Admin Password

Delete the database and restart:
```bash
rm data/users.db
pdf2zh --gui --web-ui
```

This will trigger the initial setup again.

## Development

### Project Structure
```
pdf2zh_next/
├── auth.py              # Authentication system
├── web_api.py           # FastAPI server
├── static/              # Frontend files
│   ├── index.html       # Redirect to login
│   ├── login.html       # Login/setup page
│   ├── upload.html      # File upload page
│   ├── settings.html    # Settings page
│   ├── css/
│   │   └── style.css    # Design system
│   └── js/
│       ├── api.js       # API client
│       └── auth.js      # Auth utilities
└── data/                # User data (created at runtime)
    ├── users.db         # User database
    └── users/           # User directories
        └── {username}/
            ├── uploads/
            ├── outputs/
            ├── settings.json
            └── history.json
```

## Future Enhancements

- [ ] Email-based password reset
- [ ] Two-factor authentication
- [ ] User roles and permissions
- [ ] Translation queue management
- [ ] Batch translation support
- [ ] API rate limiting
- [ ] Audit logging

## License

Same as PDFMathTranslate - AGPL-3.0
