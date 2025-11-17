from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple, List
import logging
import math
from ..models.ref_patient_allocation_model import RefPatientAllocation
from ..models.processed_events_model import ProcessedEvent
from ..schemas.ref_patient_allocation import RefPatientAllocationCreate, RefPatientAllocationUpdate, RefPatientAllocationDelete
from ..services.idempotency_service import IdempotencyService

logger = logging.getLogger(__name__)

def create_ref_patient_allocation(
    db: Session,
    allocation: RefPatientAllocationCreate,
    correlation_id: str,
    created_by: str
) -> Tuple[RefPatientAllocation, bool]:
    """
    Create a new patient allocation with idempotency protection.
    
    Args:
        db: Database session
        allocation: Patient allocation data to create
        correlation_id: Correlation ID from outbox service for deduplication
        created_by: User/service creating the allocation
        
    Returns:
        Tuple of (RefPatientAllocation, was_duplicate: bool)
        
    Raises:
        ValueError: If allocation with same ID already exists (business logic error)
        Exception: For database or other errors
    """
    
    def create_operation():
        # Check if allocation already exists - this is a business rule violation for CREATE
        existing = db.query(RefPatientAllocation).filter(RefPatientAllocation.id == allocation.id).first()
        if existing:
            raise ValueError(f"Patient allocation with ID {allocation.id} already exists. Use update operation instead.")
        
        logger.info(f"Creating new patient allocation {allocation.id} for patient {allocation.patient_id}")
        
        # Use raw SQL for IDENTITY INSERT to handle specific ID
        query = text("""
            SET IDENTITY_INSERT [REF_PATIENT_ALLOCATION] ON;
            
            INSERT INTO [REF_PATIENT_ALLOCATION] (
                id, active, isDeleted, patientId, doctorId, gameTherapistId, supervisorId, 
                caregiverId, tempDoctorId, tempCaregiverId,
                created_date, modified_date, created_by_id, modified_by_id
            ) VALUES (
                :id, :active, :isDeleted, :patientId, :doctorId, :gameTherapistId, :supervisorId,
                :caregiverId, :tempDoctorId, :tempCaregiverId,
                :created_date, :modified_date, :created_by_id, :modified_by_id
            );
            
            SET IDENTITY_INSERT [REF_PATIENT_ALLOCATION] OFF;
        """)
        
        params = {
            "id": allocation.id,
            "active": allocation.active,
            "isDeleted": allocation.is_deleted or "0",
            "patientId": allocation.patient_id,
            "doctorId": allocation.doctor_id,
            "gameTherapistId": allocation.game_therapist_id,
            "supervisorId": allocation.supervisor_id,
            "caregiverId": allocation.caregiver_id,
            "tempDoctorId": allocation.temp_doctor_id,
            "tempCaregiverId": allocation.temp_caregiver_id,
            "created_date": allocation.created_date,
            "modified_date": allocation.modified_date,
            "created_by_id": created_by,
            "modified_by_id": created_by,
        }
        
        db.execute(query, params)
        db.flush()
        
        # Return the created allocation
        created_allocation = db.query(RefPatientAllocation).filter(RefPatientAllocation.id == allocation.id).first()
        if not created_allocation:
            raise Exception(f"Failed to create patient allocation {allocation.id}")
            
        return created_allocation
    
    # Use IdempotencyService for deduplication
    try:
        result, was_duplicate = IdempotencyService.process_idempotent(
            db=db,
            correlation_id=correlation_id,
            event_type="PATIENT_ALLOCATION_CREATED",
            aggregate_id=str(allocation.id),
            processed_by=f"activity_service_{created_by}",
            operation=create_operation
        )
        
        if was_duplicate:
            # Return existing allocation for duplicate events
            existing_allocation = db.query(RefPatientAllocation).filter(RefPatientAllocation.id == allocation.id).first()
            logger.info(f"Duplicate create event for patient allocation {allocation.id}, returning existing")
            return existing_allocation, True
        
        db.commit()
        logger.info(f"Successfully created patient allocation {allocation.id} for patient {allocation.patient_id}")
        return result, False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating patient allocation {allocation.id}: {str(e)}")
        raise

def update_ref_patient_allocation(
    db: Session,
    allocation_id: str,
    allocation_update: RefPatientAllocationUpdate,
    correlation_id: str,
    skip_duplicate_check: bool = False
) -> Tuple[Optional[RefPatientAllocation], bool]:
    """
    Update an existing patient allocation with idempotency protection.
    
    Args:
        db: Database session
        allocation_id: ID of allocation to update
        allocation_update: Fields to update (includes modified_date and modified_by_id)
        correlation_id: Correlation ID from outbox service for deduplication
        skip_duplicate_check: If True, bypass idempotency check (for sync events)
        
    Returns:
        Tuple of (RefPatientAllocation or None, was_duplicate: bool)
        None if allocation not found
        
    Raises:
        Exception: For database or other errors
    """
    
    def update_operation():
        # Find the allocation to update
        db_allocation = db.query(RefPatientAllocation).filter(
            RefPatientAllocation.id == allocation_id,
            RefPatientAllocation.isDeleted == "0"
        ).first()
        
        if not db_allocation:
            logger.warning(f"Patient allocation {allocation_id} not found for update")
            return None
        
        logger.debug(f"Updating patient allocation {allocation_id}")
        
        # Update only the fields that were provided
        update_data = allocation_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # Map schema field names to model field names
            if field == 'patient_id':
                setattr(db_allocation, 'patientId', value)
            elif field == 'doctor_id':
                setattr(db_allocation, 'doctorId', value)
            elif field == 'game_therapist_id':
                setattr(db_allocation, 'gameTherapistId', value)
            elif field == 'supervisor_id':
                setattr(db_allocation, 'supervisorId', value)
            elif field == 'caregiver_id':
                setattr(db_allocation, 'caregiverId', value)
            elif field == 'temp_doctor_id':
                setattr(db_allocation, 'tempDoctorId', value)
            elif field == 'temp_caregiver_id':
                setattr(db_allocation, 'tempCaregiverId', value)
            elif field == 'is_deleted':
                setattr(db_allocation, 'isDeleted', value)
            elif field == 'modified_date':
                setattr(db_allocation, 'modified_date', value)
            elif field == 'modified_by_id':
                setattr(db_allocation, 'modified_by_id', value)
            elif hasattr(db_allocation, field) and field != 'id':  # Never update ID
                setattr(db_allocation, field, value)
        
        db.flush()
        return db_allocation
    
    # Use IdempotencyService for deduplication (unless skipped for sync events)
    try:
        if skip_duplicate_check:
            logger.info(f"Skipping duplicate check for patient allocation {allocation_id} (sync event)")
            # Execute update directly without idempotency check
            result = update_operation()
            was_duplicate = False
            
            # Still record the event for tracking, but don't check for duplicates
            try:
                IdempotencyService.record_processed_event(
                    db=db,
                    correlation_id=correlation_id,
                    event_type="PATIENT_ALLOCATION_UPDATED",
                    aggregate_id=allocation_id,
                    processed_by=f"activity_service_{allocation_update.modified_by_id}_sync"
                )
            except Exception as e:
                logger.warning(f"Failed to record sync event (non-critical): {str(e)}")
        else:
            result, was_duplicate = IdempotencyService.process_idempotent(
                db=db,
                correlation_id=correlation_id,
                event_type="PATIENT_ALLOCATION_UPDATED",
                aggregate_id=allocation_id,
                processed_by=f"activity_service_{allocation_update.modified_by_id}",
                operation=update_operation
            )
        
        if was_duplicate:
            # Return current state for duplicate events
            existing_allocation = db.query(RefPatientAllocation).filter(
                RefPatientAllocation.id == allocation_id,
                RefPatientAllocation.isDeleted == "0"
            ).first()
            logger.info(f"Duplicate update event for patient allocation {allocation_id}, returning current state")
            return existing_allocation, True
        
        if result is None:
            logger.warning(f"Patient allocation {allocation_id} not found for update")
            db.commit()  # Commit the idempotency record even if allocation not found
            return None, False
        
        db.commit()
        logger.debug(f"Successfully updated patient allocation {allocation_id}")
        return result, False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating patient allocation {allocation_id}: {str(e)}")
        raise

def delete_ref_patient_allocation(
    db: Session,
    allocation_id: str,
    allocation_delete: RefPatientAllocationDelete,
    correlation_id: str,
    skip_duplicate_check: bool = False
) -> Tuple[Optional[RefPatientAllocation], bool]:
    """
    Soft delete a patient allocation with idempotency protection.
    
    Args:
        db: Database session
        allocation_id: ID of allocation to delete
        allocation_delete: Delete data including timestamp and user info
        correlation_id: Correlation ID from outbox service for deduplication
        skip_duplicate_check: If True, bypass idempotency check (for sync events)
        
    Returns:
        Tuple of (RefPatientAllocation or None, was_duplicate: bool)
        None if allocation not found
        
    Raises:
        Exception: For database or other errors
    """
    
    def delete_operation():
        # Find the allocation to delete
        db_allocation = db.query(RefPatientAllocation).filter(RefPatientAllocation.id == allocation_id).first()
        
        if not db_allocation:
            logger.warning(f"Patient allocation {allocation_id} not found for deletion")
            return None
        
        if db_allocation.isDeleted == "1":
            logger.info(f"Patient allocation {allocation_id} already deleted")
            return db_allocation
        
        logger.info(f"Soft deleting patient allocation {allocation_id}")
        
        # Perform soft delete using schema data
        db_allocation.isDeleted = "1"
        db_allocation.modified_by_id = allocation_delete.modified_by_id
        db_allocation.modified_date = allocation_delete.modified_date
        
        db.flush()
        return db_allocation
    
    # Use IdempotencyService for deduplication
    try:
        result, was_duplicate = IdempotencyService.process_idempotent(
            db=db,
            correlation_id=correlation_id,
            event_type="PATIENT_ALLOCATION_DELETED",
            aggregate_id=allocation_id,
            processed_by=f"activity_service_{allocation_delete.modified_by_id}",
            operation=delete_operation
        )
        
        if was_duplicate:
            # Return current state for duplicate events
            existing_allocation = db.query(RefPatientAllocation).filter(RefPatientAllocation.id == allocation_id).first()
            logger.info(f"Duplicate delete event for patient allocation {allocation_id}, returning current state")
            return existing_allocation, True
        
        if result is None:
            logger.warning(f"Patient allocation {allocation_id} not found for deletion")
            db.commit()  # Commit the idempotency record even if allocation not found
            return None, False
        
        db.commit()
        logger.info(f"Successfully deleted patient allocation {allocation_id}")
        return result, False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting patient allocation {allocation_id}: {str(e)}")
        raise

def get_ref_patient_allocation_by_id(db: Session, allocation_id: str) -> Optional[RefPatientAllocation]:
    """
    Get a single patient allocation by ID.
    
    Args:
        db: Database session
        allocation_id: Allocation ID to find
        
    Returns:
        RefPatientAllocation if found, None otherwise
    """
    return db.query(RefPatientAllocation).filter(
        RefPatientAllocation.id == allocation_id,
        RefPatientAllocation.isDeleted == "0"
    ).first()


def get_ref_patient_allocation_by_patient_id(db: Session, patient_id: int) -> Optional[RefPatientAllocation]:
    """
    Get a patient allocation by patient ID (returns active allocation).
    
    Args:
        db: Database session
        patient_id: Patient ID to find allocation for
        
    Returns:
        RefPatientAllocation if found, None otherwise
    """
    return db.query(RefPatientAllocation).filter(
        RefPatientAllocation.patientId == patient_id,
        RefPatientAllocation.active == "Y",
        RefPatientAllocation.isDeleted == "0"
    ).first()


def get_ref_patient_allocations(
    db: Session,
    page_no: int = 0,
    page_size: int = 10,
    patient_id: Optional[int] = None,
    active: Optional[str] = None
) -> Tuple[List[RefPatientAllocation], int, int]:
    """
    Get paginated list of patient allocations with optional filters.
    
    Args:
        db: Database session
        page_no: Page number (0-based)
        page_size: Number of items per page
        patient_id: Optional patient ID filter
        active: Optional active status filter ("Y" or "N")
        
    Returns:
        Tuple of (allocations_list, total_records, total_pages)
    """
    # Base query - only non-deleted allocations
    query = db.query(RefPatientAllocation).filter(RefPatientAllocation.isDeleted == "0")
    
    # Apply filters
    if patient_id is not None:
        query = query.filter(RefPatientAllocation.patientId == patient_id)
    
    if active in ["Y", "N"]:
        query = query.filter(RefPatientAllocation.active == active)
    
    # Count total records with same filters
    count_query = db.query(func.count(RefPatientAllocation.id)).filter(RefPatientAllocation.isDeleted == "0")
    
    if patient_id is not None:
        count_query = count_query.filter(RefPatientAllocation.patientId == patient_id)
    if active in ["Y", "N"]:
        count_query = count_query.filter(RefPatientAllocation.active == active)
    
    total_records = count_query.scalar()
    total_pages = math.ceil(total_records / page_size) if page_size > 0 else 1
    
    # Apply pagination and get results
    offset = page_no * page_size
    allocations = query.order_by(RefPatientAllocation.id.asc()).offset(offset).limit(page_size).all()
    
    return allocations, total_records, total_pages


def check_patient_allocation_exists(db: Session, allocation_id: str) -> bool:
    """
    Check if a patient allocation exists (including deleted ones).
    
    Args:
        db: Database session
        allocation_id: Allocation ID to check
        
    Returns:
        True if allocation exists, False otherwise
    """
    count = db.query(func.count(RefPatientAllocation.id)).filter(
        RefPatientAllocation.id == allocation_id
    ).scalar()
    
    return count > 0


def get_idempotency_stats(db: Session) -> dict:
    """Get statistics about processed events for monitoring."""
    return IdempotencyService.get_processing_stats(db)


def cleanup_old_processed_events(db: Session, older_than_days: int = 30) -> int:
    """Clean up old processed events - should be run periodically."""
    return IdempotencyService.cleanup_old_events(db, older_than_days)


def is_event_already_processed(db: Session, correlation_id: str) -> bool:
    """Check if a specific correlation_id was already processed."""
    return IdempotencyService.is_already_processed(db, correlation_id)
