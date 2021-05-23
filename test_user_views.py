import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):

    def setUp(self):
        db.session.rollback()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.u0 = User.signup(username="test0", email="test0@test.com", password="password", image_url=None)
        self.u0.id = 10

        self.u1 = User.signup("test1", "test1@test.com", "password", None)
        self.u1.id = 20

        self.u2 = User.signup("test2", "test2@test.com", "password", None)
        self.u2.id = 30

        self.u3 = User.signup("test3", "test3@test.com", "password", None)
        self.u4 = User.signup("test4", "test4@test.com", "password", None)

        db.session.commit()

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test0", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@test0", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.u0.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test0", str(resp.data))

    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.u0.id)
        m2 = Message(text="Eating some lunch", user_id=self.u0.id)
        m3 = Message(id=1111, text="likable warble", user_id=self.u1.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.u0.id, message_id=1111)

        db.session.add(l1)
        db.session.commit()

    def test_add_like(self):
        m = Message(id=2222, text="The earth is round", user_id=self.u1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u0.id

            resp = c.post("/messages/2222/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==2222).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.u0.id)

    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.u0.id)

        l = Likes.query.filter(Likes.user_id==self.u0.id and Likes.message_id==m.id).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u0.id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u0.id)
        f2 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.u0.id)
        f3 = Follows(user_being_followed_id=self.u0.id, user_following_id=self.u1.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_show_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u0.id

            resp = c.get(f"/users/{self.u0.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertNotIn("@test3", str(resp.data))
            self.assertNotIn("@test4", str(resp.data))

    def test_show_followers(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u0.id

            resp = c.get(f"/users/{self.u0.id}/followers")

            self.assertIn("@test1", str(resp.data))
            self.assertNotIn("@test2", str(resp.data))
            self.assertNotIn("@test3", str(resp.data))
            self.assertNotIn("@test4", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.u0.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.u0.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
