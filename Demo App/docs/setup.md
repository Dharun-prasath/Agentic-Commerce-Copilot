# Setup & Configuration

## Environment Variables

The Demo App backend requires an `.env` file in the `Demo App/backend` directory.

```env
# Server
PORT=8000
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-jwt-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/demo_db

# External Integrations
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Frontend URL for CORS
FRONTEND_URL=http://localhost:5173
```

## Running the Application

There is a unified startup script provided at the root of the project: `start.py`.

This Python script uses `subprocess` to launch both the backend API and the frontend Vite server concurrently.

```bash
cd "Agentic-Commerce-Copilot/Demo App"
python3 start.py
```

### Backend Only (Manual)
```bash
cd "Demo App/backend"
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Only (Manual)
```bash
cd "Demo App/frontend"
npm install
npm run dev
```
