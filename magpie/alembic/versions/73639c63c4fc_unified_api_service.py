"""unified api service

Revision ID: 73639c63c4fc
Revises: d01af1f2e445
Create Date: 2018-09-27 16:12:02.282830

"""
import os, sys

cur_file = os.path.abspath(__file__)
root_dir = os.path.dirname(cur_file)  # version
root_dir = os.path.dirname(root_dir)  # alembic
root_dir = os.path.dirname(root_dir)  # magpie
root_dir = os.path.dirname(root_dir)  # root
sys.path.insert(0, root_dir)

from alembic import op
from alembic.context import get_context
from magpie.definitions.sqlalchemy_definitions import *
# from magpie.models import Service
from sqlalchemy.sql import table

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = '73639c63c4fc'
down_revision = 'd01af1f2e445'
branch_labels = None
depends_on = None


def upgrade():
    context = get_context()
    if isinstance(context.connection.engine.dialect, PGDialect):
        # add 'sync_type' column if missing
        op.add_column('services', sa.Column('sync_type', sa.UnicodeText(), nullable=True))

        services = table('services',
                         sa.Column('url', sa.UnicodeText()),
                         sa.Column('type', sa.UnicodeText()),
                         sa.Column('sync_type', sa.UnicodeText()),
                         )

        # transfer 'api' service types
        op.execute(services.
                   update().
                   where(services.c.type == op.inline_literal('project-api')).
                   values({'type': op.inline_literal('api'),
                           'url': op.inline_literal(str(services.c.url) + '/api'),
                           'sync_type': op.inline_literal('project-api')
                           })
                   )
        op.execute(services.
                   update().
                   where(services.c.type == op.inline_literal('geoserver-api')).
                   values({'type': op.inline_literal('api'),
                           'sync_type': op.inline_literal('geoserver-api')
                           })
                   )


def downgrade():
    op.drop_column('services', 'sync_type')

    service = table('old_service',
                    sa.Column('url', sa.UnicodeText()),
                    sa.Column('type', sa.UnicodeText()),
                    )

    # transfer 'api' service types
    op.execute(service.
               update().
               where(service.c.type == op.inline_literal('project-api')).
               values({'type': op.inline_literal('project-api'),
                       'url': op.inline_literal(str(service.c.url).rstrip('/api')),
                       })
               )
    op.execute(service.
               update().
               where(service.c.type == op.inline_literal('geoserver-api')).
               values({'type': op.inline_literal('geoserver-api'),
                       })
               )