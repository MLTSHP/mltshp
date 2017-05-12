from tornado.web import UIModule
import models.shake
from tornado.options import options


class Pagination(UIModule):
    def render(self, object_count=1, current_page=1, url_format='', per_page=10, \
        adjacent=2):
        current_page = int(current_page)
        
        if object_count <= per_page:
            num_pages = 1
        else:
            diff = object_count % per_page
            num_pages = object_count / per_page
            if diff > 0:
                num_pages += 1
        
        previous_link = None
        if current_page > 1:
            previous_link = url_format % (current_page - 1)
        
        next_link = None
        if current_page < num_pages:
            next_link = url_format % (current_page + 1)
        
        pages = self.chunk_pages(num_pages=num_pages, current_page=current_page, \
            adjacent=adjacent)
        
        return self.render_string("uimodules/pagination.html", \
            pages=pages, current_page=current_page, previous_link=previous_link, \
            next_link=next_link, num_pages=num_pages, url_format=url_format)

    def chunk_pages(self, num_pages=1, current_page=1, adjacent=2):
        max_pages_display = (adjacent * 2) + 1 + 4
        mylist = range(1,num_pages+1)
        if num_pages < max_pages_display:
            return mylist

        adjacent = 2
        middle_chunk_size = (adjacent * 2) + 1
        one_sided_chunk_size = middle_chunk_size + 2

        pages = []
        # if low page #, only split out the end.
        if current_page <= middle_chunk_size:
            for i in range(one_sided_chunk_size):
                pages.append(mylist.pop(0))
            pages = pages + ['...', mylist.pop(-2), mylist.pop()]

        # if page # is in middle, split out beginning and end
        elif current_page > middle_chunk_size and current_page < num_pages - middle_chunk_size:
            start_pop = current_page - (adjacent + 1)
            for i in range(middle_chunk_size):
                pages.append(mylist.pop(start_pop))
            pages = [1,2,'...'] + pages + ['...', mylist.pop(-2), mylist.pop()]

        # high page #, only split out beginning
        else:
            for i in range(one_sided_chunk_size):
                pages.insert(0, mylist.pop())
            pages = [mylist.pop(0), mylist.pop(0), '...'] + pages
        return pages


class Image(UIModule):
    def render(self, sharedfile, current_user=None, list_view=False, show_attribution_in_title=True, shake=None, filtering=None):
        can_delete = sharedfile.can_delete(current_user)
        can_edit = sharedfile.can_edit(current_user)
        can_favor = sharedfile.can_favor(current_user)
        can_unfavor = sharedfile.can_unfavor(current_user)
        # prevent unconfirmed users from being able to create shake content
        can_save = sharedfile.can_save(current_user) and current_user.email_confirmed == 1

        sharedfile_user = sharedfile.user()
        sourcefile = sharedfile.sourcefile()
        attribution = {
            'name' : sharedfile_user.name,
            'thumbnail_url' : sharedfile_user.profile_image_url(),
            'path' : '/user/%s' % sharedfile_user.name
        }
        if show_attribution_in_title and hasattr(sharedfile, 'shake_id'):
            shake = models.shake.Shake.get("id = %s", sharedfile.shake_id)
            if shake:
                attribution = {
                    'name' : shake.display_name(),
                    'thumbnail_url' : shake.thumbnail_url(),
                    'path' : shake.path()
                }

        # Check if image is NSFW.  We do the check here because we have ready
        # access to sharedfile's user.  A micro-optimization, that shouldn't
        # matter once there is a request-level query cache in place.
        is_nsfw = False
        if sharedfile_user.nsfw == 1:
            is_nsfw = True
        if sourcefile.nsfw == 1:
            is_nsfw = True

        # minimum height is used for the NSFW cover.
        min_height = 90
        width, height = sourcefile.width_constrained_dimensions(555)
        if height > 170:
            min_height = height - 80

        #is this user's content filter on
        hide_nsfw = True
        if filtering is not None:
            hide_nsfw = filtering
        else:
            if current_user:
                if current_user.show_naked_people == 1:
                    hide_nsfw = False
                else:
                    hide_nsfw = True
            else:
                nsfw_mode = self.handler.get_secure_cookie('nsfw')
                if nsfw_mode == '1':
                    hide_nsfw = False
                else:
                    hide_nsfw = True

        # Used for determining the type of "save this" button
        has_multiple_shakes = False
        if current_user:
            has_multiple_shakes = current_user.has_multiple_shakes()

        if can_save:
            has_saved = current_user.saved_sharedfile(sharedfile)
        else:
            has_saved = False

        # Can only remove from shake if user is shake owner.
        # Currently option only applies to list view.
        can_remove_from_shake = False
        if shake and shake.is_owner(current_user) and not options.readonly:
            can_remove_from_shake = True

        # Only in a list view do we pull in comments inline.
        comments = []
        if list_view:
            comments = sharedfile.comments()

        can_comment = False
        if current_user and current_user.email_confirmed == 1 and not options.readonly:
            can_comment = True

        can_autoplay = False
        if current_user and not current_user.disable_autoplay == 1:
            # TODO: check to see if user is on a mobile device. if so, prevent
            # autoplay in any case.
            can_autoplay = True

        return self.render_string("uimodules/image.html", current_user=current_user,
            list_view=list_view, sharedfile=sharedfile, can_edit=can_edit,
            can_favor=can_favor, can_unfavor=can_unfavor, can_delete=can_delete, can_comment=can_comment,
            can_save=can_save, show_attribution_in_title=show_attribution_in_title, has_saved=has_saved,
            sharedfile_user=sharedfile.user(), shake=shake, can_remove_from_shake=can_remove_from_shake,
            comments=comments, expanded=False, has_multiple_shakes=has_multiple_shakes,
            attribution=attribution, is_nsfw=is_nsfw, min_height=min_height, hide_nsfw=hide_nsfw,
            sized_width=width, sized_height=height, sourcefile=sourcefile,
            can_autoplay=can_autoplay)


class ImageMedium(UIModule):
    def render(self, sharedfile):
        sharedfile_user = sharedfile.user()
        return self.render_string("uimodules/image-medium.html", sharedfile=sharedfile, \
            sharedfile_user=sharedfile_user)

class ShakeFollow(UIModule):
    def render(self, follow_user=None, follow_shake=None, current_user=None, 
               avatar_size=48, extended=False, post_name_text=""):
        if follow_user:
            shake = follow_user.shake()
        else:
            shake = follow_shake
        if current_user:
            can_unfollow = current_user.has_subscription_to_shake(shake)
            can_follow = not can_unfollow
        else:
            can_unfollow = can_follow = None
        return self.render_string("uimodules/shake-follow.html", follow_user=follow_user, \
            current_user=current_user, shake=shake, avatar_size=avatar_size, can_follow=can_follow, \
            can_unfollow=can_unfollow, extended=extended, post_name_text=post_name_text)


class NotificationInvitations(UIModule):
    """
    Acccepts a list of notifications, an individual notification or None.
    """
    def render(self, notifications=[]):
        if notifications == None:
            return ''
        if isinstance(notifications, list):
            single = False
        else:
            notifications = [notifications]
            single = True
        return self.render_string("uimodules/notification-invitations.html", notifications=notifications, single=single)


class NotificationInvitationRequest(UIModule):
    """
    Acccepts a list of notifications. Also accepts an on_shake_page flag
    that denotes that the Notification is rendering on the individual
    shake page, where the display is slightly different.
    """
    def render(self, notifications=[], on_shake_page=False):
        return self.render_string("uimodules/notification-invitation-request.html", 
                                   notifications=notifications, on_shake_page=on_shake_page)

class NotificationInvitationApproved(UIModule):
    """
    Acccepts a list of notifications.
    """
    def render(self, notifications=[]):
        return self.render_string("uimodules/notification-invitation-approved.html", notifications=notifications)


class FunFormField(UIModule):
    def render(self, field_type='text', name='', label='', value='', css_class=''):
        if value == None:
            value = ''
        return self.render_string("uimodules/fun-form-field.html", field_type=field_type, \
            name=name, label=label, value=value, css_class=css_class)

class ShakeDropdown(UIModule):
    """
    Accepts a User object to render shake drop down list.
    """
    def render(self, current_user=None):
        group_shake = None
        can_create_shake = False
        if not current_user:
            return ''
        group_shakes = current_user.shakes(include_managed=True, include_only_group_shakes=True)
        can_create_shake = current_user.can_create_shake()
        return self.render_string("uimodules/shake-dropdown.html", current_user=current_user, \
            group_shakes=group_shakes, can_create_shake=can_create_shake)

class UserCounts(UIModule):
    def render(self, user):
        return self.render_string("uimodules/user-counts.html", user=user)
