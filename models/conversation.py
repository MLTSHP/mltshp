from lib.flyingcow import Model, Property
from lib.utilities import utcnow
from tornado.options import options

from . import comment
from . import sharedfile


class Conversation(Model):
    user_id      = Property()
    sharedfile_id= Property()
    muted        = Property(default=0)
    created_at   = Property()
    updated_at   = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Conversation, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
    def mute(self):
        self.muted = 1
        self.save()

    def sharedfile(self):
        """
        Associates sharedfile.
        """
        return sharedfile.Sharedfile.get("id=%s", self.sharedfile_id)

    def relevant_comments(self):
        """
        Returns comments to display for the user's conversation.  Returns
        all comments that aren't deleted.
        """
        return comment.Comment.where('sharedfile_id = %s and deleted = 0', self.sharedfile_id)

    @classmethod
    def for_user(self, user_id, type='all', page=1, per_page=10):
        limit_start = (page-1) * per_page
        filtering_by = ""
        if type == 'myfiles':
            filtering_by = "AND sharedfile.user_id = conversation.user_id"
        elif type == 'mycomments':
            filtering_by = "AND sharedfile.user_id != conversation.user_id"            
        select = """
          SELECT conversation.* from conversation, sharedfile
          WHERE conversation.user_id = %s
            AND conversation.muted = 0
            AND sharedfile.id = conversation.sharedfile_id
            AND sharedfile.deleted = 0
            %s
            ORDER BY sharedfile.activity_at desc
          limit %s, %s
        """ % (user_id, filtering_by, limit_start, per_page)
        conversations =  self.object_query(select)
        return conversations

    @classmethod
    def for_user_count(self, user_id, type='all'):
        filtering_by = ''
        if type == 'myfiles':
            filtering_by = "AND sharedfile.user_id = conversation.user_id"
        elif type == 'mycomments':
            filtering_by = "AND sharedfile.user_id != conversation.user_id"            
        select = """
          SELECT count(conversation.id) as count from conversation, sharedfile
          WHERE conversation.user_id = %s
            AND sharedfile.id = conversation.sharedfile_id
            AND sharedfile.deleted = 0
            AND conversation.muted = 0
            %s
        """ % (user_id, filtering_by)
        result = self.query(select)
        return result[0]['count']
