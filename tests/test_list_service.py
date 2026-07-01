from datetime import datetime, timezone

import pytest

from app import create_app
from extensions import db
from models import GroceryList, Item, User
from services import list_service


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_purchase_all_items_preserves_existing_purchase_attribution(app):
    with app.app_context():
        maya = User(username="maya", email="maya@example.com")
        leo = User(username="leo", email="leo@example.com")
        priya = User(username="priya", email="priya@example.com")
        db.session.add_all([maya, leo, priya])
        db.session.flush()

        grocery_list = GroceryList(name="Weekly Shop", created_by=maya.id)
        db.session.add(grocery_list)
        db.session.flush()

        purchased_at = datetime(2026, 7, 1, tzinfo=timezone.utc)
        already_purchased = [
            Item(
                list_id=grocery_list.id,
                name="Milk",
                added_by=maya.id,
                is_purchased=True,
                purchased_by=leo.id,
                purchased_at=purchased_at,
            ),
            Item(
                list_id=grocery_list.id,
                name="Olive Oil",
                added_by=leo.id,
                is_purchased=True,
                purchased_by=priya.id,
                purchased_at=purchased_at,
            ),
        ]
        unpurchased = [
            Item(list_id=grocery_list.id, name="Bananas", added_by=maya.id),
            Item(list_id=grocery_list.id, name="Pasta", added_by=maya.id),
            Item(list_id=grocery_list.id, name="Sourdough", added_by=maya.id),
        ]
        db.session.add_all(already_purchased + unpurchased)
        db.session.commit()

        original_purchase_users = {
            item.id: item.purchased_by for item in already_purchased
        }

        count = list_service.purchase_all_items(grocery_list.id, maya.id)

        items = Item.query.filter_by(list_id=grocery_list.id).all()
        assert count == 3
        assert len(items) == 5
        assert all(item.is_purchased for item in items)

        for item in already_purchased:
            db.session.refresh(item)
            assert item.purchased_by == original_purchase_users[item.id]
