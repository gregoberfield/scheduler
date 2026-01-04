from app import db
from datetime import datetime
from sqlalchemy import event, Index

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


# Track slots that need aggregate updates
_pending_aggregate_updates = set()

def update_aggregate_count(slot_index):
    """Recalculate aggregate counts for a specific slot"""
    available_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=2).count()
    maybe_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=1).count()
    
    aggregate = db.session.query(AggregateSlotCount).get(slot_index)
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
def mark_slot_for_aggregate_update(mapper, connection, target):
    """Mark slot for aggregate update after changes"""
    _pending_aggregate_updates.add(target.slot_index)


@event.listens_for(db.Session, 'after_flush')
def update_aggregates_after_flush(session, flush_context):
    """Update all marked aggregates after flush"""
    global _pending_aggregate_updates
    if _pending_aggregate_updates:
        # Update all pending aggregates
        for slot_index in _pending_aggregate_updates:
            update_aggregate_count(slot_index)
        # Clear the pending set
        _pending_aggregate_updates = set()
