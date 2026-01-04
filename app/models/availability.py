from app import db
from datetime import datetime
from sqlalchemy import event, Index, select, func

class AvailabilitySlot(db.Model):
    """Availability slot model - 30 minute time slots"""
    __tablename__ = 'availability_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_index = db.Column(db.Integer, nullable=False)  # Unix timestamp / 1800
    state = db.Column(db.Integer, nullable=False, default=0)  # 0=Unavailable, 1=Maybe, 2=Available
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on user_id and slot_index
    __table_args__ = (
        db.UniqueConstraint('user_id', 'slot_index', name='unique_user_slot'),
        Index('idx_slot_index', 'slot_index'),
        Index('idx_user_slot', 'user_id', 'slot_index'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'slot_index': self.slot_index,
            'state': self.state,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AvailabilitySlot user_id={self.user_id} slot={self.slot_index} state={self.state}>'


class AggregateSlotCount(db.Model):
    """Aggregate counts for heatmap view"""
    __tablename__ = 'aggregate_slot_counts'
    
    slot_index = db.Column(db.Integer, primary_key=True)
    available_count = db.Column(db.Integer, default=0)
    maybe_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'slot_index': self.slot_index,
            'available_count': self.available_count,
            'maybe_count': self.maybe_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AggregateSlotCount slot={self.slot_index} available={self.available_count} maybe={self.maybe_count}>'


def update_aggregate_count(slot_index):
    """Recalculate aggregate counts for a specific slot"""
    available_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=2).count()
    maybe_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=1).count()
    
    aggregate = db.session.get(AggregateSlotCount, slot_index)
    if aggregate:
        aggregate.available_count = available_count
        aggregate.maybe_count = maybe_count
        aggregate.updated_at = datetime.utcnow()
    else:
        aggregate = AggregateSlotCount(
            slot_index=slot_index,
            available_count=available_count,
            maybe_count=maybe_count
        )
        db.session.add(aggregate)


# Event listeners to update aggregate counts
@event.listens_for(AvailabilitySlot, 'after_insert')
@event.listens_for(AvailabilitySlot, 'after_update') 
@event.listens_for(AvailabilitySlot, 'after_delete')
def receive_after_change(mapper, connection, target):
    """Update aggregate immediately after availability change"""
    # Use connection-level queries to count within the same transaction
    availability_table = AvailabilitySlot.__table__
    aggregate_table = AggregateSlotCount.__table__
    
    # Count available (state=2)
    available_result = connection.execute(
        select(func.count()).select_from(availability_table).where(
            availability_table.c.slot_index == target.slot_index,
            availability_table.c.state == 2
        )
    )
    available_count = available_result.scalar()
    
    # Count maybe (state=1)
    maybe_result = connection.execute(
        select(func.count()).select_from(availability_table).where(
            availability_table.c.slot_index == target.slot_index,
            availability_table.c.state == 1
        )
    )
    maybe_count = maybe_result.scalar()
    
    # Check if aggregate exists
    check_result = connection.execute(
        select(aggregate_table.c.slot_index).where(
            aggregate_table.c.slot_index == target.slot_index
        )
    )
    exists = check_result.fetchone() is not None
    
    # Update or insert aggregate
    if exists:
        connection.execute(
            aggregate_table.update().where(
                aggregate_table.c.slot_index == target.slot_index
            ).values(
                available_count=available_count,
                maybe_count=maybe_count,
                updated_at=datetime.utcnow()
            )
        )
    else:
        connection.execute(
            aggregate_table.insert().values(
                slot_index=target.slot_index,
                available_count=available_count,
                maybe_count=maybe_count
            )
        )
