"""Redaction coverage tests."""

from app.services.analysis.redaction import redact_code


def test_redacts_aws_access_key() -> None:
    text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
    out = redact_code(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "****AWS_ACCESS_KEY****" in out


def test_redacts_private_key_block() -> None:
    text = (
        "-----BEGIN PRIVATE KEY-----\n"
        "abcd1234\n"
        "-----END PRIVATE KEY-----\n"
    )
    out = redact_code(text)
    assert "abcd1234" not in out
    assert "****" in out


def test_redacts_connection_string_password() -> None:
    text = "DATABASE_URL=postgres://scanner:supersecret@localhost:5432/scanner"
    out = redact_code(text)
    assert "supersecret" not in out
    assert "postgres://scanner:****@localhost:5432/scanner" in out
