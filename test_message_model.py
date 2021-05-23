import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        db.session.rollback()
        db.drop_all()
        db.create_all()

        self.uid = 10
        u = User.signup("testing", "testing@test.com", "password", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def test_message_model(self):
        m = Message(
            text="Test Message",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(self.u.messages[0].text, "Test Message")
        self.assertEqual(len(self.u.messages), 1)

    def test_message_likes(self):
        m1 = Message(
            text="Test Message",
            user_id=self.uid
        )

        u = User.signup("admin", "admin@email.com", "password", None)
        uid = 20
        u.id = uid
        db.session.add_all([m1, u])
        db.session.commit()

        u.likes.append(m1)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)