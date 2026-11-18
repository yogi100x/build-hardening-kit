from services.api.health import health


def test_health_reports_ok() -> None:
    assert health() == {"status": "ok"}
