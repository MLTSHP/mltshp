from models import User, Externalservice, ExternalRelationship
from base import BaseTestCase

class ExternalserviceModelTests(BaseTestCase):
    def setUp(self):
        super(ExternalserviceModelTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.save()
        self.external_service = Externalservice(
                                user_id=self.user.id, 
                                service_id=11616, 
                                screen_name='torrez', 
                                type=Externalservice.TWITTER, 
                                service_key='asdf', 
                                service_secret='qwer')
        self.external_service.save()
            
    def test_get_by_user(self):
        external_service = Externalservice.by_user(self.user, Externalservice.TWITTER)
        
        self.assertEqual(external_service.user_id,           self.external_service.user_id           )
        self.assertEqual(external_service.service_id,        self.external_service.service_id        )
        self.assertEqual(external_service.screen_name,       self.external_service.screen_name       )
        self.assertEqual(external_service.type,              self.external_service.type              )
        self.assertEqual(external_service.service_key,       self.external_service.service_key       )
        self.assertEqual(external_service.service_secret,    self.external_service.service_secret    )
        self.assertEqual(external_service.created_at.strftime("%Y-%m-%d %H:%M:%S"),       self.external_service.created_at        )
        self.assertEqual(external_service.updated_at.strftime("%Y-%m-%d %H:%M:%S"),        self.external_service.updated_at        )
    
    def test_find_mltshp_users(self):
        """
        find_mltshp_users should return all users that are on
        mltshp and also on a user's connected external service
        account.
        
        Create two other users. user2 has an externalservice
        connected, user3 does not. admin follows user2 on twitter, so user2
        should be returned as part of .find_mltshp_users result. When user3 has
        an external service connected, but is not in admin's ExternalRelationship
        graph, he will not be returned.
        """
        user2 = User(name='user2', email='user2@mltshp.com', email_confirmed=1, is_paid=1)
        user2.save()
        user2_service = Externalservice(
                                user_id=user2.id, 
                                service_id=1000,
                                screen_name='user2', 
                                type=Externalservice.TWITTER, 
                                service_key='asdf', 
                                service_secret='qwer')
        user2_service.save()
        user3 = User(name='user3', email='user3@mltshp.com', email_confirmed=1, is_paid=1)
        user3_service = Externalservice(
                                user_id=user2.id, 
                                service_id=2000,
                                screen_name='ephramzerb', 
                                type=Externalservice.TWITTER, 
                                service_key='asdf', 
                                service_secret='qwer')
        user3_service.save()
        user2.save()
        
        # We emulate admin connecting twitter account, and we add a Twitter relationship
        # to user2's twitter account.
        ExternalRelationship.add_relationship(self.user, 1000, Externalservice.TWITTER)
        # we should get user2 back.
        users = self.external_service.find_mltshp_users()
        self.assertEqual(1, len(users))
        self.assertEqual(user2.id, users[0].id)
        
        # now when we add user3, find_mltshp_users includes user3 in the result.
        ExternalRelationship.add_relationship(self.user, 2000, Externalservice.TWITTER)
        users = self.external_service.find_mltshp_users()
        self.assertEqual(2, len(users))
