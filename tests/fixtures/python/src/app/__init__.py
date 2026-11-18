from app.dal.users import list_users


def count_users() -> int:
    return len(list_users())
