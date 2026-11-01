from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db
from routers import dashboard, document, qa, review, risk, system
from seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await seed_if_empty()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"code": 500, "msg": str(exc.detail)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"code": 500, "msg": f"服务器内部错误：{exc}"})


@app.get("/api/health")
def health() -> dict:
    return {"code": 0, "data": {"status": "ok"}, "msg": "success"}


app.include_router(system.router)
app.include_router(dashboard.router)
app.include_router(document.router)
app.include_router(review.router)
app.include_router(qa.router)
app.include_router(risk.router)
app.include_router(risk.audit_router)
