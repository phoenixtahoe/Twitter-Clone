"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):

    def setUp(self):
        db.session.rollback()
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "test1@email.com", "password", None)
        uid1 = 10
        u1.id = uid1

        u2 = User.signup("test2", "test2@email.com", "password", None)
        uid2 = 20
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()


    def test_user_model(self):
        u = User(
            email="user@test.com",
            username="user",
            password="password"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_valid_signup(self):
        u_test = User.signup("test", "admin@test.com", "password", None)
        uid = 30
        u_test.id = uid
        db.session.commit()

        u_test = User.query.get(uid)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "test")
        self.assertEqual(u_test.email, "admin@test.com")
        self.assertNotEqual(u_test.password, "password")
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid = User.signup(None, "invalid@test.com", "invalid", None)
        uid = 99999
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid = User.signup("invalid", None, "invalid", None)
        uid = 99999
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError):
            User.signup("invalid", "invalid@email.com", "", None)
        
        with self.assertRaises(ValueError):
            User.signup("invalid", "invalid@email.com", None, None)

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("invalid", "invalid"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "invalid"))
