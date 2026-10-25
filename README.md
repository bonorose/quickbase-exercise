# quickbase_interview_1026

Nuxt 4 SPA (Vue 3 + shadcn-vue / reka-ui) + FastAPI (Python 3.14) backend + PostgreSQL 17, orchestrated with Docker Compose.

## Run

```bash
cp .env.example .env   # a ready-to-use local .env is already included
docker compose up --build
```

- Frontend: http://localhost:3000 (redirects to `/login`)
- API: http://localhost:5000
- Swagger UI: http://localhost:5000/docs (use **Authorize** with a token from `POST /api/v1/auth/login`)
- Auth: `POST /api/v1/auth/login` (the only public endpoint), `GET /api/v1/auth/me`
- Health: http://localhost:5000/health
- Items: http://localhost:5000/api/v1/items

Every endpoint except login requires `Authorization: Bearer <token>` (see **Authentication** below).

Seeded dev login: `admin@quickbase.local` / `admin123` (see `db/init/02_seed.sql`).

Both services hot-reload: backend `src/` and the whole frontend folder are bind-mounted.

## Database seed

Everything in `db/init/` is executed by the Postgres entrypoint, in alphabetical order, **only when the data volume is empty** (first start):

- `01_schema.sql` – tables, triggers
- `02_seed.sql` – initial data

To re-run schema + seed from scratch:

```bash
docker compose down -v && docker compose up --build
```

## Layout

```
.
├── docker-compose.yml
├── .env / .env.example
├── db/init/                     # schema + seed, run on first DB start
└── services/backend/
    ├── Dockerfile
    ├── requirements.txt
    └── src/
        ├── main.py              # app factory: middleware, exception handlers, routers
        ├── core/                # config, logging, domain exceptions, security (JWT/bcrypt), openapi
        ├── middlewares/
        │   └── auth.py          # bearer-token check for every request except the public allowlist
        ├── db/                  # async engine + per-request session
        ├── models/              # SQLAlchemy ORM models
        ├── routers/             # HTTP surface: paths, verbs, status codes, query/body params
        │                        #   __init__.py also declares PUBLIC_API_ROUTES
        ├── controllers/         # request schema -> service call -> response schema
        ├── services/            # business rules; raise core.exceptions.DomainError
        ├── repositories/        # all DB access (SQLAlchemy queries, commits)
        ├── schemas/             # grouped by category
        │   ├── auth/            #   request.py (LoginRequest) / response.py (TokenResponse, UserResponse)
        │   ├── items/           #   request.py / response.py
        │   ├── health/          #   response.py
        │   └── common/          #   response.py (ErrorResponse)
        └── dependencies/        # DI wiring per category: session -> repository -> service -> controller
            ├── database.py      #   SessionDep
            ├── auth.py          #   AuthControllerDep, CurrentUserDep
            ├── items.py
            └── health.py
```

### Request flow

```
HTTP -> routers/items.py -> controllers/item_controller.py -> services/item_service.py
     -> repositories/item_repository.py -> PostgreSQL
```

Each layer only talks to the one below it. Services raise `NotFoundError` / `ConflictError`; `main.py` maps any `DomainError` to a JSON error with its status code.

### Authentication

Secure by default, on both sides:

- **Backend:** `middlewares/auth.py` runs before routing on every request. It requires a valid bearer token, loads the user, and puts it on `request.state.user` (read by `CurrentUserDep`). The only exceptions are CORS preflights, the API docs, and `PUBLIC_API_ROUTES` in `routers/__init__.py`, which currently holds just `POST /auth/login`. The OpenAPI schema uses the same list, so Swagger shows a lock on every operation except login.
- **Frontend:** `middleware/auth.global.ts` runs on every navigation and sends signed-out users to `/login?redirect=…`. A page opts out only with `definePageMeta({ public: true })`, and only `pages/login.vue` does. Signed-in users who open a public page are sent home.

### Frontend layers (`services/frontend/app/`)

Same idea as the backend, one direction only:

```
pages/          route views: page meta (layout, middleware) + composition of components
components/     presentational; ui/ = shadcn-vue primitives, plus layout/ auth/ dashboard/
composables/    page controllers (useLoginForm, useDashboard) and orchestration (useAuth)
stores/         Pinia state only (auth session) - no API calls
services/       business logic; map API DTOs -> view models (types/models.ts)
api/            client.ts ($fetch + auth header + 401 handling) and endpoints/*.api.ts
types/api/      requests.ts / responses.ts - mirror backend schemas
plugins/services.ts   DI wiring: client -> endpoints -> services, exposed as $services
middleware/     auth.global.ts - every page requires a session unless `public: true`
```

```
page -> composable -> service -> api endpoint -> api client -> FastAPI
                   \-> store (session state)
```

Pages: `/login` (auth layout, `public: true`) and `/` dashboard (default layout, protected by default).
The JWT is stored in the `qb_auth_token` cookie; any 401 on an authenticated call clears it and returns to `/login`.

Run the frontend on the host instead of Docker: `cd services/frontend && npm install && npm run dev` (uses `services/frontend/.env`).
Production image: `docker build --target prod services/frontend` (static SPA served by nginx).

### Adding a new resource

1. Table + seed rows in `db/init/` (or a new numbered `.sql` file).
2. `models/<name>.py`
3. `schemas/<name>/request.py`, `schemas/<name>/response.py`
4. `repositories/<name>_repository.py` (subclass `BaseRepository`)
5. `services/<name>_service.py`
6. `controllers/<name>_controller.py`
7. `dependencies/<name>.py` (wire repository -> service -> controller)
8. `routers/<name>.py`, include it in `routers/__init__.py`. It is authenticated automatically; add it to `PUBLIC_API_ROUTES` only if it must be public.
9. Frontend: types in `types/api/`, `api/endpoints/<name>.api.ts`, a service, register it in `plugins/services.ts`, then a composable + page.
