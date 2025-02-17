from lib.flyingcow import Model, Property


class MigrationState(Model):
    user_id = Property()
    is_migrated = Property()

    @staticmethod
    def has_migration_data(user_id):
        state = MigrationState.get("user_id=%s", user_id)
        if state is None:
            # no state row means this user has nothing to migrate
            return False
        return True

    @staticmethod
    def has_migrated(user_id):
        state = MigrationState.get("user_id=%s", user_id)
        if state is None:
            # no state row means this user has nothing to migrate
            return True

        return state.is_migrated == 1