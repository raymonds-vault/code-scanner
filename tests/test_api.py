"""API and analysis integration tests."""

import pytest

from app.core.database import AsyncSessionLocal
from app.repositories import scan_repo
from app.services.scan_service import run_analysis_job


@pytest.mark.asyncio
async def test_run_analysis_completes() -> None:
    async with AsyncSessionLocal() as session:
        scan = await scan_repo.create_scan(
            session, metadata={"test": True}, client_request_id=None
        )
        await scan_repo.add_chunks(
            session,
            scan,
            [
                (
                    "chunk-1",
                    "vuln.py",
                    1,
                    20,
                    "import os\nos.system(request.args.get('c'))\n",
                    "python",
                    None,
                    None,
                ),
            ],
        )
        await session.commit()
        scan_id = scan.id

    await run_analysis_job(scan_id)

    async with AsyncSessionLocal() as session:
        s = await scan_repo.get_scan(session, scan_id, with_findings=True)
        assert s is not None
        assert s.status == "completed"
        assert s.progress == 1.0
        assert len(s.findings or []) >= 1


def test_post_scan_returns_id(client) -> None:
    body = {
        "chunks": [
            {
                "id": "c1",
                "file_path": "x.py",
                "start_line": 1,
                "end_line": 5,
                "code": "print(1)",
                "language": "python",
            }
        ],
        "metadata": {},
    }
    r = client.post("/api/v1/scan", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["status"] == "pending"


def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["database_status"] == "healthy"
