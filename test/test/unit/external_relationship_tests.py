from models import User, ExternalRelationship
from .base import BaseTestCase


class ExternalRelationshipTests(BaseTestCase):

    def test_add_relationship(self):
        """
        ExternalRelationship.add_relationship should correctly save a new entry.
        If a duplicate entry is passed in, no errors are thrown and no new entries are saved.
        """
        user = User(name='example',email='example@example.com', email_confirmed=1, is_paid=1)
        user.save()

        ExternalRelationship.add_relationship(user, '1000', ExternalRelationship.TWITTER)
        all_relationships = ExternalRelationship.all()
        self.assertEqual(1, len(all_relationships))
        self.assertEqual(user.id, all_relationships[0].user_id)
        self.assertEqual(1000, all_relationships[0].service_id)
        self.assertNotEqual(None, all_relationships[0].created_at)
        self.assertNotEqual(None, all_relationships[0].updated_at)

        ExternalRelationship.add_relationship(user, '1000', ExternalRelationship.TWITTER)
        self.assertEqual(1, len(all_relationships))
        