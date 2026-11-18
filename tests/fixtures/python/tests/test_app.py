from app import count_users


def test_count_users_starts_empty() -> None:
    assert count_users() == 0
