"""Risk engine unit tests."""

from app.services.analysis.risk_engine import score_chunk
from app.services.analysis.types import CodeChunkState, StaticSignalDict


def _chunk(cid: str = "c1") -> CodeChunkState:
    return CodeChunkState(
        client_chunk_id=cid,
        db_chunk_id="db1",
        file_path="a.py",
        start_line=1,
        end_line=10,
        code="cursor.execute('SELECT %s' % user_input)",
        language="python",
        context_summary=None,
        dependencies=None,
    )


def test_score_increases_with_static_signal() -> None:
    ch = _chunk()
    sig: StaticSignalDict = {
        "chunk_client_id": "c1",
        "chunk_db_id": "db1",
        "type": "sql_injection",
        "confidence": 0.8,
        "location": {"file_path": "a.py", "start_line": 1},
    }
    s = score_chunk(ch, [sig])
    assert s > 0.3


def test_score_respects_threshold_floor() -> None:
    ch = CodeChunkState(
        client_chunk_id="c2",
        db_chunk_id="db2",
        file_path="b.py",
        start_line=1,
        end_line=5,
        code="def hello():\n    return 1\n",
        language="python",
        context_summary=None,
        dependencies=None,
    )
    assert score_chunk(ch, []) < 0.2
