"""Test User Password Hashing"""
import unittest
import time
from app import create_app, db
from app.models import User


class UserModelTestCase(unittest.TestCase):
    """User password hash testing"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        """Test password is being set"""
        user = User(password='cat')
        self.assertTrue(user.password_hash is not None)

    def test_no_password_getter(self):
        """Test you can't grab the password"""
        user = User(password='cat')
        with self.assertRaises(AttributeError):
            # pylint: disable=pointless-statement
            user.password

    def test_password_verification(self):
        """Test it is actually the password"""
        user = User(password='cat')
        self.assertTrue(user.verify_password('cat'))
        self.assertFalse(user.verify_password('dog'))

    def test_password_salts_are_random(self):
        """Test hashing is different every password"""
        user1 = User(password='cat')
        user2 = User(password='cat')
        self.assertTrue(user1.password_hash != user2.password_hash)

    def test_valid_confirmation_token(self):
        """Test that the confirmation token is working correctly"""
        user = User(password='cat')
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        self.assertTrue(user.confirm(token))

    def test_invalid_confirmation_token(self):
        """Test that an invalid confirmation token can't confirm an account"""
        user1 = User(password='cat')
        user2 = User(password='dog')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        token = user1.generate_confirmation_token()
        self.assertFalse(user2.confirm(token))

    def test_expired_confirmation_token(self):
        """Test that the token will expire"""
        user = User(password='cat')
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(user.confirm(token))

    def test_valid_reset_token(self):
        """Test that reset token is working correctly"""
        user = User(password='meow')
        db.session.add(user)
        db.session.commit()
        token = user.generate_reset_token()
        self.assertTrue(user.reset_password(token, 'woof'))
        self.assertTrue(user.verify_password('woof'))

    def test_invalid_reset_token(self):
        """Test that an invalid reset token won't reset the password"""
        user1 = User(password='meow')
        user2 = User(password='woof')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        token = user1.generate_reset_token()
        self.assertFalse(user2.reset_password(token, 'elephant'))
        self.assertFalse(user2.reset_password('not_token', 'elephant'))
        self.assertTrue(user2.verify_password('woof'))
