#!/usr/bin/env python3
"""Rebuild aggregate counts for all availability slots"""

from app import create_app, db
from app.models.availability import AvailabilitySlot, AggregateSlotCount

app = create_app()
with app.app_context():
    # Clear existing aggregates
    print("Clearing existing aggregates...")
    AggregateSlotCount.query.delete()
    
    # Get all unique slot indices
    slot_indices = db.session.query(AvailabilitySlot.slot_index).distinct().all()
    print(f"Found {len(slot_indices)} unique time slots")
    
    # Recalculate aggregates for each slot
    for (slot_index,) in slot_indices:
        available_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=2).count()
        maybe_count = AvailabilitySlot.query.filter_by(slot_index=slot_index, state=1).count()
        
        aggregate = AggregateSlotCount(
            slot_index=slot_index,
            available_count=available_count,
            maybe_count=maybe_count
        )
        db.session.add(aggregate)
    
    db.session.commit()
    print(f"✓ Rebuilt {len(slot_indices)} aggregate counts")
    
    # Show some samples
    print("\nSample aggregate data:")
    samples = AggregateSlotCount.query.limit(10).all()
    for agg in samples:
        print(f"  Slot {agg.slot_index}: {agg.available_count} available, {agg.maybe_count} maybe")
