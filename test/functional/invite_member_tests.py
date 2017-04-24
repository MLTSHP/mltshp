import test.base
import models
from tornado.escape import json_decode
import os

class InviteMemberTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(InviteMemberTests, self).setUp()
        self.user = models.User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('pass')
        self.user.save()

        #create a shake for admin
        self.shake = models.Shake(user_id=self.user.id, type='group', name='asdf', title='asdf', description='asdf')
        self.shake.save()

        #create three other users
        self.usera = models.User(name='usera', email='usera@example.com', email_confirmed=1, is_paid=1)
        self.usera.set_password('pass')
        self.usera.save()

        self.userb = models.User(name='userb', email='userb@example.com', email_confirmed=1, is_paid=1)
        self.userb.set_password('pass')
        self.userb.save()

        self.sign_in('admin', 'pass')


    def test_creating_an_invitation_notification(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.assertEqual(notification.sender_id, self.user.id)
        self.assertEqual(notification.receiver_id, self.usera.id)
        self.assertEqual(notification.action_id, self.shake.id)
        self.assertTrue(json_decode(response.body)['invitation_status'])
        

    def test_accept_manager_invitation(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification.id})
        manager = models.ShakeManager.get('id = 1 and shake_id=%s', self.shake.id)
        self.assertEqual(manager.user_id, self.usera.id)
        

    def test_accept_manager_invitations_many(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})

        notification = models.Notification.where('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        response = self.fetch_url('/asdf')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification[2].id})
        manager = models.ShakeManager.get('id = 1 and shake_id=%s', self.shake.id)
        self.assertEqual(manager.user_id, self.usera.id)
        
        notifications = models.Notification.where('type=%s', 'invitation')
        for n in notifications:
            self.assertEqual(n.deleted, 1)
        

    def test_decline_manager_notification(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')

        self.sign_in('usera', 'pass')
        response = self.post_url('/account/clear-notification?json=1&type=single&id=%s' % (notification.id))
        
        notification = models.Notification.get('type=%s and deleted=1', 'invitation')
        self.assertEqual(notification.sender_id, self.user.id)
        self.assertEqual(notification.receiver_id, self.usera.id)
        self.assertEqual(notification.action_id, self.shake.id)
        
    
    def test_manager_can_upload_to_shake(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification.id})
        
        response = self.upload_test_file(shake_id=self.shake.id)

        ssf = models.Shakesharedfile.get('shake_id=%s', self.shake.id)
        self.assertTrue(ssf)
        sf = models.Sharedfile.get('id = %s', ssf.sharedfile_id)
        self.assertEqual(sf.user_id, self.usera.id)

    
    def test_non_manager_cannot_upload_to_shake(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification.id})
        
        self.sign_in('userb', 'pass')
        response = self.upload_test_file(shake_id=self.shake.id)
        ssfs = models.Shakesharedfile.where("shake_id = %s", self.shake.id)
        self.assertFalse(ssfs)
    
    def test_manager_quit_shake(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification.id})

        shma = models.ShakeManager.get('shake_id = %s and user_id = %s', self.shake.id, self.usera.id)
        self.assertEqual(shma.deleted, 0)
        self.post_url('/shake/asdf/quit')
        shma = models.ShakeManager.get('shake_id = %s and user_id = %s', self.shake.id, self.usera.id)
        self.assertEqual(shma.deleted, 1)
        
    def test_editor_remove_manager(self):
        response = self.post_url('/shake/asdf/invite?json=1', arguments={'name' : 'usera'})
        notification = models.Notification.get('type=%s', 'invitation')
        self.sign_in('usera', 'pass')
        self.post_url('/shake/asdf/accept-invitation', arguments={'id':notification.id})

        shma = models.ShakeManager.get('shake_id = %s and user_id = %s', self.shake.id, self.usera.id)
        self.assertEqual(shma.deleted, 0)
        self.sign_in('admin', 'pass')
        self.post_url('/shake/asdf/members/remove', arguments={'user_id':self.usera.id})
        shma = models.ShakeManager.get('shake_id = %s and user_id = %s', self.shake.id, self.usera.id)
        self.assertEqual(shma.deleted, 1)
        
