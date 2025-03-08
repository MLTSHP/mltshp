from tasks import mltshp_task
from models import User


@mltshp_task()
def delete_account(user_id=0, **kwargs):
    """
    This task deletes a user account. This is meant to do the full deletion work of
    related records for a User object that has a deleted flag already set.

    """
    user = User.get('id = %s', user_id)
    if not user or user.is_admin or user.deleted == 0:
        return
    user.delete()
