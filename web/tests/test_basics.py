"""Basic db and app tests"""

import unittest
from flask import current_app
from app import create_app, db


class BasicsTestCase(unittest.TestCase):
    """Tests if app is running and db is creating"""

    def setUp(self):
        self.backend = create_app('testing')
        self.backend_context = self.backend.app_context()
        self.backend_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.backend_context.pop()

    def test_app_exists(self):
        """Check create_app is operating correctly"""
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        """Check testing is operating correctly"""
        self.assertTrue(current_app.config['TESTING'])
