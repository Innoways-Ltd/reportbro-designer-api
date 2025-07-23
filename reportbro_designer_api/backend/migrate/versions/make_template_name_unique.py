"""Make template_name unique

Revision ID: make_template_name_unique
Revises: 
Create Date: 2023-07-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'make_template_name_unique'
down_revision = None  # Update this to match your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create a unique index on template_name and project
    op.create_unique_constraint(
        "uq_templates_template_name_project", 
        "templates", 
        ["template_name", "project"]
    )


def downgrade():
    # Remove the unique constraint
    op.drop_constraint(
        "uq_templates_template_name_project",
        "templates",
        type_="unique"
    )
