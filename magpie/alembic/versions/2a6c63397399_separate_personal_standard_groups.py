"""separate personal standard groups

Revision ID: 2a6c63397399
Revises: 9fd4589cc82c
Create Date: 2018-05-23 17:17:51.205891

"""
import os, sys
cur_file = os.path.abspath(__file__)
root_dir = os.path.dirname(cur_file)    # version
root_dir = os.path.dirname(root_dir)    # alembic
root_dir = os.path.dirname(root_dir)    # magpie
root_dir = os.path.dirname(root_dir)    # root
sys.path.insert(0, root_dir)

from alembic import op
from alembic.context import get_context
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.orm import sessionmaker
from magpie import models
import register_default_group as def_grp

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = '2a6c63397399'
down_revision = '9fd4589cc82c'
branch_labels = None
depends_on = None

# OLD/NEW values must be different
OLD_GROUP_USERS = 'user'
NEW_GROUP_USERS = 'users'
OLD_GROUP_ADMIN = 'admin'
NEW_GROUP_ADMIN = 'administrators'
OLD_USER_USERS = OLD_GROUP_USERS
OLD_USER_ADMIN = OLD_GROUP_ADMIN


def get_users_groups(db_session):
    # fetch current db users and groups
    all_users = db_session.query(models.User)
    all_groups = db_session.query(models.Group)
    old_user_admin = [user for user in all_users if user.user_name == OLD_USER_ADMIN]
    old_user_users = [user for user in all_users if user.user_name == OLD_USER_USERS]
    old_group_admin = [group for group in all_groups if group.group_name == OLD_GROUP_ADMIN]
    old_group_users = [group for group in all_groups if group.group_name == OLD_GROUP_USERS]
    new_group_admin = [group for group in all_groups if group.group_name == NEW_GROUP_ADMIN]
    new_group_users = [group for group in all_groups if group.group_name == NEW_GROUP_USERS]

    # return found or None
    return old_user_admin[0] if len(old_user_admin) > 0 else None, \
           old_user_users[0] if len(old_user_users) > 0 else None, \
           old_group_admin[0] if len(old_group_admin) > 0 else None, \
           old_group_users[0] if len(old_group_users) > 0 else None, \
           new_group_admin[0] if len(new_group_admin) > 0 else None, \
           new_group_users[0] if len(new_group_users) > 0 else None


def upgrade_migrate(old_group, old_user, new_group, new_name, db_session):
    """
    Migrates a user and its personal user-group to a standard group.
    Reassigns the user references to link to the new standard group.
    """

    if new_group is None and old_group is not None:
        # just rename the group, no need to adjust references
        old_group.group_name = new_name
    elif new_group is None and old_group is None:
        # create missing group, no group reference to modify
        new_group = models.Group(group_name=new_name)
        db_session.add(new_group)
    elif new_group is not None and old_group is not None:
        # both groups exist, must transfer references
        for usr_grp in db_session.query(models.UserGroup):
            if usr_grp.group_id == old_group.id:
                usr_grp.group_id = new_group.id

    # remove not required 'user-group'
    if old_user is not None:
        for usr_grp in db_session.query(models.UserGroup):
            if usr_grp.user_id == old_user.id:
                db_session.delete(usr_grp)
        db_session.delete(old_user)


def downgrade_migrate(old_group, old_user, new_group, old_name, db_session):
    """
    Migrates a standard group back to the original user and corresponding personal user-group.
    Reassigns the user references to link to the old personal group.
    """

    if old_group is None:
        # create missing group
        old_group = models.Group(group_name=old_name)
        db_session.add(old_group)
    if old_group is not None and new_group is not None:
        # transfer user-group references
        all_usr_grp = db_session.query(models.UserGroup)
        for usr_grp in all_usr_grp:
            if usr_grp.group_id == new_group.id:
                usr_grp.group_id = old_group.id

    if new_group is not None:
        db_session.delete(new_group)

    if old_user is None:
        old_user = models.User(user_name=old_name, email='{}@mail.com'.format(old_name))
        db_session.add(old_user)
        usr_grp = models.UserGroup(group_id=old_group.id, user_id=old_user.id)
        db_session.add(usr_grp)


def clean_user_groups(db_session):
    """
    Ensures that each user is the only one pointing to it's corresponding personal user-group.
    Invalid user references are dropped.
    """

    all_users = db_session.query(models.User)
    all_groups = db_session.query(models.Group)
    all_usr_grp = db_session.query(models.UserGroup)

    all_usr_dict = dict([(usr.id, usr.user_name) for usr in all_users])
    all_grp_dict = dict([(grp.id, grp.group_name) for grp in all_groups])

    for usr_grp in all_usr_grp:
        # delete any missing user/group references (pointing to nothing...)
        if usr_grp.user_id not in all_usr_dict.keys() or usr_grp.group_id not in all_grp_dict.keys():
            db_session.delete(usr_grp)
            continue
        # delete any user/personal-group reference of different names
        grp_name = all_grp_dict[usr_grp.group_id]
        usr_name = all_usr_dict[usr_grp.user_id]
        is_personal_group = usr_name in all_grp_dict.values()
        if is_personal_group and grp_name != usr_name:
            db_session.delete(usr_grp)


def upgrade():
    context = get_context()
    session = Session(bind=op.get_bind())
    if isinstance(context.connection.engine.dialect, PGDialect):
        old_usr_a, old_usr_u, old_grp_a, old_grp_u, new_grp_a, new_grp_u = get_users_groups(session)
        upgrade_migrate(old_grp_a, old_usr_a, new_grp_a, NEW_GROUP_ADMIN, session)
        upgrade_migrate(old_grp_u, old_usr_u, new_grp_u, NEW_GROUP_USERS, session)
        clean_user_groups(session)
        def_grp.init_admin(session)
        def_grp.init_anonymous(session)
        def_grp.init_user_group(session)
        session.commit()


def downgrade():
    context = get_context()
    session = Session(bind=op.get_bind())
    if isinstance(context.connection.engine.dialect, PGDialect):
        old_usr_a, old_usr_u, old_grp_a, old_grp_u, new_grp_a, new_grp_u = get_users_groups(session)
        downgrade_migrate(old_grp_a, old_usr_a, new_grp_a, OLD_GROUP_ADMIN, session)
        downgrade_migrate(old_grp_u, old_usr_u, new_grp_u, OLD_GROUP_USERS, session)
        session.commit()
