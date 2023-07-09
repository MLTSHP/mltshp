import test.base
from models import User, Shake, Notification, ShakeManager
from tornado.escape import json_decode

class RequestInvitationTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(RequestInvitationTests, self).setUp()
        self.user = User(name='joe', email='joe@example.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sign_in("joe", "asdfasdf")        
        
        self.manager = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.manager.set_password('asdfasdf')
        self.manager.save()

        self.shake = Shake(user_id=self.manager.id, type='group', title="derp", name='derp')
        self.shake.save()
        
    def test_posting_request_creates_request(self):
        response = self.post_url('/shake/derp/request_invitation?json=1')
        j_response = json_decode(response.body)
        
        self.assertEqual(j_response['status'], 'ok')
        
        no = Notification.all()[0]
        self.assertEqual(no.sender_id, self.user.id)
        self.assertEqual(no.receiver_id, self.manager.id)
        self.assertEqual(no.action_id, self.shake.id)
    
    def test_cannot_request_after_one_already_exists(self):
        response = self.post_url('/shake/derp/request_invitation?json=1')
        j_response = json_decode(response.body)
        self.assertEqual(j_response['status'], 'ok')
        
        response = self.post_url('/shake/derp/request_invitation?json=1')
        j_response = json_decode(response.body)
        self.assertEqual(j_response['status'], 'error')
        
    def test_posting_request_doesnt_recreate_request(self):
        response = self.post_url('/shake/derp/request_invitation?json=1')
        j_response = json_decode(response.body)
        
        self.assertEqual(j_response['status'], 'ok')
        
        no = Notification.all()[0]
        self.assertEqual(no.sender_id, self.user.id)
        self.assertEqual(no.receiver_id, self.manager.id)
        self.assertEqual(no.action_id, self.shake.id)
        
        response = self.post_url('/shake/derp/request_invitation?json=1')
        self.assertEqual(len(Notification.all()), 1)
        
    def test_no_button_shows_when_request_has_been_made(self):
        response = self.post_url('/shake/derp/request_invitation?json=1')
        response = self.fetch_url('/derp')
        self.assertNotIn('/request_invitation', response.body)
    
    def test_shake_manager_gets_notification_created(self):
        response = self.post_url('/shake/derp/request_invitation?json=1')

        n = Notification.get('receiver_id = %s', self.manager.id)
        self.assertEqual(n.sender_id, self.user.id)
        self.assertEqual(n.action_id, self.shake.id)

    def test_shake_accept_request_creates_editor(self):
        self.post_url('/shake/derp/request_invitation?json=1')
        
        self.sign_in("admin", "asdfasdf")
        response = self.post_url('/shake/derp/approve_invitation?json=1', arguments={'user_id':self.user.id})
        
        manager = ShakeManager.get('user_id = %s', self.user.id)
        self.assertTrue(manager)

    def test_shake_accept_request_deletes_notification(self):
        self.post_url('/shake/derp/request_invitation?json=1')
        
        self.sign_in("admin", "asdfasdf")
        response = self.post_url('/shake/derp/approve_invitation?json=1', arguments={'user_id' : self.user.id})
    
        n = Notification.get('receiver_id = %s', self.manager.id)
        self.assertTrue(n.deleted)
        
    def test_shake_accept_request_creates_notification(self):
        self.post_url('/shake/derp/request_invitation?json=1')
        
        self.sign_in("admin", "asdfasdf")
        response = self.post_url('/shake/derp/approve_invitation?json=1', arguments={'user_id' : self.user.id})
    
        n = Notification.get('receiver_id = %s and type=%s', self.manager.id, "invitation_request")
        self.assertTrue(n.deleted)

        n = Notification.get('receiver_id = %s and type=%s', self.user.id, "invitation_approved")
        self.assertTrue(n)
        
        
    def test_shake_decline_request_deletes_notification(self):
        self.post_url('/shake/derp/request_invitation?json=1')
        
        self.sign_in("admin", "asdfasdf")
        response = self.post_url('/shake/derp/decline_invitation?json=1', arguments={'user_id':self.user.id})
    
        manager = ShakeManager.get('user_id = %s', self.user.id)
        self.assertFalse(manager)
    
        n = Notification.get('receiver_id = %s', self.manager.id)
        self.assertTrue(n.deleted)    
        
    def test_already_a_member_do_not_see_request_button(self):
        self.shake.add_manager(self.user)
        
        response = self.fetch_url('/derp')
        self.assertNotIn('join this shake', response.body)
        
