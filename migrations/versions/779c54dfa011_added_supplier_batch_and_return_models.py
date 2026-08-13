"""Added Supplier, Batch and Return models

Revision ID: 779c54dfa011
Revises: 47301886ae39
Create Date: 2026-07-22 23:04:13.084375

"""
from alembic import op
import sqlalchemy as sa

revision = '779c54dfa011'
down_revision = '47301886ae39'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('supplier',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('gstin', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('purchase_return',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('return_date', sa.DateTime(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('inventory_batch',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('purchase_item_id', sa.Integer(), nullable=False),
    sa.Column('purchase_rate', sa.Float(), nullable=False),
    sa.Column('qty_purchased', sa.Integer(), nullable=False),
    sa.Column('qty_remaining', sa.Integer(), nullable=False),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.ForeignKeyConstraint(['purchase_item_id'], ['purchase_item.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('purchase_return_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('return_id', sa.Integer(), nullable=False),
    sa.Column('inventory_batch_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('return_rate', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['inventory_batch_id'], ['inventory_batch.id'], ),
    sa.ForeignKeyConstraint(['return_id'], ['purchase_return.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('invoice_no', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('purchase_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('payment_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))

    op.execute("INSERT INTO supplier (name, phone, email, address, gstin, is_active, created_at) VALUES ('Default Supplier', '0000000000', 'default@example.com', 'N/A', 'N/A', true, CURRENT_TIMESTAMP)")
    op.execute("UPDATE purchase SET supplier_id = (SELECT id FROM supplier ORDER BY id ASC LIMIT 1) WHERE supplier_id IS NULL")
    op.execute("UPDATE purchase SET created_by = (SELECT id FROM \"user\" ORDER BY id ASC LIMIT 1) WHERE created_by IS NULL")

    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('created_by', existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key('fk_purchase_supplier', 'supplier', ['supplier_id'], ['id'])
        batch_op.create_foreign_key('fk_purchase_user', 'user', ['created_by'], ['id'])
        batch_op.drop_column('supplier_name')

    with op.batch_alter_table('purchase_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit_cost', sa.Float(), nullable=True))

    op.execute("UPDATE purchase_item SET unit_cost = cost_price WHERE unit_cost IS NULL")
    
    with op.batch_alter_table('purchase_item', schema=None) as batch_op:
        batch_op.alter_column('unit_cost', existing_type=sa.Float(), nullable=False)
        batch_op.add_column(sa.Column('tax', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('discount', sa.Float(), nullable=True))
        batch_op.drop_column('cost_price')


def downgrade():
    with op.batch_alter_table('purchase_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
        batch_op.drop_column('discount')
        batch_op.drop_column('tax')
        batch_op.drop_column('unit_cost')

    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supplier_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.drop_constraint('fk_purchase_user', type_='foreignkey')
        batch_op.drop_constraint('fk_purchase_supplier', type_='foreignkey')
        batch_op.drop_column('created_by')
        batch_op.drop_column('notes')
        batch_op.drop_column('payment_status')
        batch_op.drop_column('purchase_date')
        batch_op.drop_column('invoice_no')
        batch_op.drop_column('supplier_id')

    op.drop_table('purchase_return_item')
    op.drop_table('inventory_batch')
    op.drop_table('purchase_return')
    op.drop_table('supplier')