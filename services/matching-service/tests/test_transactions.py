"""Integration tests validating transactional behaviour."""

from sqlalchemy import text

import pytest

from src.storage import count_rows, create_user
from src.storage.database import transaction_scope
from src.storage.models import User


def test_transaction_scope_rolls_back_on_error():
    """Ensure the transactional context rolls back on raised exceptions."""

    user_one = create_user(
        User(
            id=None,
            email="rollback1@example.com",
            full_name="Rollback One",
            preferences=["ai"],
        )
    )
    user_two = create_user(
        User(
            id=None,
            email="rollback2@example.com",
            full_name="Rollback Two",
            preferences=["cloud"],
        )
    )

    with pytest.raises(RuntimeError):
        with transaction_scope() as session:
            session.execute(
                text(
                    """
                    INSERT INTO swipes (user_id, target_id, action, created_at)
                    VALUES (:user_id, :target_id, 'like', timezone('UTC', now()))
                    """
                ),
                {"user_id": user_one.id, "target_id": user_two.id},
            )
            raise RuntimeError("force rollback")

    assert count_rows("swipes") == 0
