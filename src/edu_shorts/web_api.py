from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client


class JobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    audience: str = Field(min_length=1, max_length=200)
    duration: int = Field(default=70, ge=60, le=75)
    source_paths: list[str] = Field(min_length=1, max_length=20)


def _settings(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} 환경변수가 필요합니다.")
    return value


def supabase_admin() -> Client:
    return create_client(_settings("SUPABASE_URL"), _settings("SUPABASE_SERVICE_ROLE_KEY"))


def current_user(authorization: Annotated[str | None, Header()] = None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        user = supabase_admin().auth.get_user(authorization.removeprefix("Bearer ")).user
    except Exception as exc:
        raise HTTPException(status_code=401, detail="로그인 정보를 확인할 수 없습니다.") from exc
    if user is None:
        raise HTTPException(status_code=401, detail="로그인 정보를 확인할 수 없습니다.")
    return {"id": user.id}


app = FastAPI(title="Edu Shorts Studio API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in os.getenv("WEB_ORIGIN", "http://localhost:5173").split(",") if origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/jobs", status_code=202)
def create_job(payload: JobRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    if any(not path.startswith(f"{user['id']}/") for path in payload.source_paths):
        raise HTTPException(status_code=403, detail="자신이 업로드한 원본만 사용할 수 있습니다.")
    client = supabase_admin()
    job_id = str(uuid.uuid4())
    slug = _slugify(payload.title, job_id)
    row = {
        "id": job_id,
        "user_id": user["id"],
        "slug": slug,
        "title": payload.title,
        "audience": payload.audience,
        "duration_seconds": payload.duration,
        "source_paths": payload.source_paths,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client.table("short_jobs").insert(row).execute()
    return {"job_id": job_id, "status": "queued"}


@app.get("/v1/jobs/{job_id}")
def job_status(job_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    client = supabase_admin()
    response = client.table("short_jobs").select("*").eq("id", job_id).eq("user_id", user["id"]).maybe_single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    job = response.data
    if job.get("result_path"):
        signed = client.storage.from_("short-results").create_signed_url(job["result_path"], 3600)
        job["result_url"] = signed.get("signedURL") or signed.get("signedUrl")
    return job


def _slugify(title: str, job_id: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{stem or 'short'}-{job_id[:8]}"
