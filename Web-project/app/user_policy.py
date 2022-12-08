from flask_login import current_user
ADMIN_ROLE_ID = 1
MODERATOR_ROLE_ID = 2

def is_admin():
    return current_user.role_id == ADMIN_ROLE_ID

def is_moderator():
    return current_user.role_id == MODERATOR_ROLE_ID

class UsersPolicy:
    def __init__(self, record=None):
        self.record = record

    @property
    def show(self):
        is_showing_user = current_user.id == self.record.id
        return is_admin() or is_showing_user or is_moderator()

    def edit(self):
        return is_admin() or is_moderator()

    def new(self):
        return is_admin()

    def delete(self):
        return is_admin()