# HR-Plus

> Enterprise-grade hiring platform for modern organizations

[![CI](https://github.com/your-org/hr-plus/workflows/CI/badge.svg)](https://github.com/your-org/hr-plus/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

HR-Plus is a full-cycle enterprise hiring platform that serves two distinct audiences through separate, optimized frontends:

- **External Candidates** — Public career site for job discovery, applications, and tracking
- **Internal Staff** — Comprehensive recruiting dashboard for recruiters, hiring managers, interviewers, and HR admins

---

## ✨ Features

### For Candidates
- 🔍 Advanced job search with filters and semantic search
- 📝 Profile builder with resume parsing
- 📱 Application tracking dashboard
- 📅 Self-service interview scheduling
- 💬 In-app messaging with recruiters
- 📊 Application status timeline

### For Recruiters & Hiring Teams
- 📋 Requisition management with approval workflows
- 🎯 Kanban-style pipeline board with drag-and-drop
- 👥 Candidate sourcing and talent pools
- 🗓️ Interview scheduling with calendar integration
- ⭐ Structured scorecards and evaluations
- 💼 Offer management with e-signature
- 📈 Analytics and reporting dashboards
- 🔐 Role-based access control (RBAC)
- 🌐 SSO/SAML integration for enterprise auth

### Compliance & Security
- 🔒 GDPR-compliant with data export/deletion
- 📊 EEO/OFCCP reporting
- 🔐 Field-level encryption for sensitive data
- 📝 Comprehensive audit logging
- ✅ WCAG 2.1 AA accessibility

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Public Career Site  │  Internal Dashboard              │
│  (Next.js SSR/SSG)   │  (Next.js CSR/SSR)              │
├─────────────────────────────────────────────────────────┤
│                  Django REST API                         │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Celery  │  Elasticsearch      │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

#### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (internal), custom components (public)
- **State Management:** React Query + Zustand
- **Forms:** Zod validation

#### Backend
- **Framework:** Django 5+ with Django REST Framework
- **Language:** Python 3.12+
- **Database:** PostgreSQL 16+ with pgvector
- **Cache/Queue:** Redis 7
- **Task Queue:** Celery + Celery Beat
- **Search:** Elasticsearch 8
- **Storage:** S3-compatible (AWS S3 / MinIO)
- **Real-time:** Django Channels (WebSocket)

#### Infrastructure
- **Containerization:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry, Prometheus, Grafana

---

## 📋 Prerequisites

- **Docker Desktop** (for infrastructure services)
- **Python 3.12+** (for Django backend)
- **Node.js 20+** (for Next.js frontends)
- **Git**

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/hr-plus.git
cd hr-plus
```

### 2. Copy Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure any necessary settings (the defaults work for local development).

### 3. Start Infrastructure Services

```bash
chmod +x start-dev.sh
./start-dev.sh
```

This script will:
- Start PostgreSQL, Redis, Elasticsearch, MinIO, and Mailpit in Docker
- Run Django migrations
- Check for a superuser (prompts to create one if missing)

### 4. Start Application Servers

**Terminal 1 — Django Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py runserver
```

Django API will be available at: **http://localhost:8000**

**Terminal 2 — Public Career Site (optional):**
```bash
cd apps/public-careers
npm install
npm run dev
```

Public site will be available at: **http://localhost:3000**

**Terminal 3 — Internal Dashboard (optional):**
```bash
cd apps/internal-dashboard
npm install
npm run dev
```

Internal dashboard will be available at: **http://localhost:3001**

### 5. Access the Application

- **Django Admin:** http://localhost:8000/admin
- **API Documentation:** http://localhost:8000/api/docs/
- **OpenAPI Schema:** http://localhost:8000/api/schema/
- **Public Career Site:** http://localhost:3000
- **Internal Dashboard:** http://localhost:3001
- **Email Viewer (Mailpit):** http://localhost:8025
- **MinIO Console:** http://localhost:9001 (admin/minioadmin)

---

## 📁 Project Structure

```
hr-plus/
├── backend/                    # Django API
│   ├── apps/                   # Django applications
│   │   ├── accounts/           # User models, auth, SSO
│   │   ├── applications/       # Application pipeline
│   │   ├── candidates/         # Candidate profiles
│   │   ├── communications/     # Email, notifications
│   │   ├── compliance/         # GDPR, EEO, audit logs
│   │   ├── core/               # Shared utilities
│   │   ├── interviews/         # Scheduling, scorecards
│   │   ├── jobs/               # Requisitions, postings
│   │   └── ...
│   ├── config/                 # Django settings
│   └── requirements/           # Python dependencies
├── apps/
│   ├── public-careers/         # Public-facing career site
│   ├── internal-dashboard/     # Staff recruiting dashboard
│   └── shared/                 # Shared components/utilities
├── docker/                     # Dockerfiles
├── .github/workflows/          # CI/CD pipelines
├── docker-compose.yml          # Development infrastructure
├── CLAUDE.md                   # AI development guidelines
└── README.md                   # This file
```

---

## 🧪 Testing

### Backend (Django)

```bash
cd backend

# Run all tests with coverage
pytest -v --cov=apps --cov-report=html

# Run specific app tests
pytest apps/applications/tests/ -v

# Run with specific markers
pytest -m "not slow" -v
```

Coverage report will be generated in `backend/htmlcov/index.html`.

### Frontend

```bash
# Public Career Site
cd apps/public-careers
npm test
npm run test:coverage

# Internal Dashboard
cd apps/internal-dashboard
npm test
npm run test:e2e  # Playwright E2E tests
```

### Run All Tests

```bash
# From project root
npm run test:frontend
cd backend && pytest
```

---

## 🔧 Development Workflow

### Type Synchronization

After modifying Django models or serializers, regenerate TypeScript types:

```bash
npm run sync-types
```

This runs:
1. `python manage.py spectacular --file schema.yml` (generates OpenAPI schema)
2. `npx openapi-typescript schema.yml -o apps/shared/types/api.ts` (generates TS types)

### Code Quality

**Backend (Python):**
```bash
cd backend
ruff check .              # Lint
ruff format .             # Format
mypy apps/                # Type check
```

**Frontend (TypeScript):**
```bash
npm run lint --workspaces        # Lint all apps
npm run type-check --workspaces  # Type check all apps
```

### Database Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Seed Development Data

```bash
cd backend
python manage.py seed_data
```

This creates sample departments, users, jobs, and applications for testing.

---

## 🚢 Deployment

### Production Build

```bash
# Build all frontend apps
npm run build:all

# Collect Django static files
cd backend
python manage.py collectstatic --noinput
```

### Docker Production

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Ensure production environment variables are set:

- Set `DJANGO_DEBUG=False`
- Use strong `DJANGO_SECRET_KEY`
- Configure production database (`DATABASE_URL`)
- Set up proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- Enable SSL/HSTS settings
- Configure S3 for file storage
- Set up Sentry for error tracking

See `.env.example` for full list of required variables.

---

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** — AI development guidelines and architecture rules
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** — Comprehensive project plan and roadmap
- **[hr-platform-scope.md](hr-platform-scope.md)** — Detailed product requirements and scope
- **[API Documentation](http://localhost:8000/api/docs/)** — Interactive API docs (when running)

---

## 🔐 Security

- **Field-level encryption** for PII (phone, SSN, salary)
- **RBAC** with granular permissions per module
- **Audit logging** for all data access and modifications
- **CSRF, XSS, SQL injection** protection (Django/Next.js built-in)
- **HttpOnly, Secure cookies** for session management
- **CSP headers** with nonces for XSS prevention
- **Rate limiting** on authentication endpoints
- **Dependency scanning** via `pip-audit` and `npm audit`

### Reporting Security Issues

Please report security vulnerabilities to: security@hrplus.com

Do not open public GitHub issues for security concerns.

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow coding standards:**
   - Python: PEP 8, use `ruff` for linting/formatting
   - TypeScript: ESLint + Prettier configs
   - Max 300 lines per file, 50 lines per function
3. **Write tests** for new features (80%+ coverage required)
4. **Update documentation** if adding/changing features
5. **Run all checks** before submitting:
   ```bash
   # Backend
   cd backend
   ruff check . && ruff format --check . && pytest

   # Frontend
   npm run lint --workspaces
   npm run type-check --workspaces
   npm run test:frontend
   ```
6. **Commit convention:** `type(scope): description`
   - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
   - Example: `feat(applications): add bulk reject functionality`
7. **Submit a Pull Request** with a clear description

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
- [Elasticsearch](https://www.elastic.co/)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/your-org/hr-plus/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/hr-plus/discussions)
- **Email:** support@hrplus.com

---

<div align="center">
  <strong>Built with ❤️ for better hiring</strong>
  <br>
  <sub>© 2026 HR-Plus. All rights reserved.</sub>
</div>
