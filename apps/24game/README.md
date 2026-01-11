# 24 Game (FastAPI + Jinja2 + HTMX)
## Layout
- `main.py`: FastAPI entrypoint
- `apps/24game`: templates and static assets

## Run locally
1. Install dependencies: `fastapi`, `uvicorn`
2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
3. Open: `http://127.0.0.1:8000/24game/`

## Notes
- Route prefix is defined by `APP_SLUG` and `BASE_PATH` in `main.py`.
- Static assets are served from `apps/24game/apps/24game`.
