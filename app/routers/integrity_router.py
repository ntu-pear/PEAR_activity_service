from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db
from app.models.activity_model import Activity
from app.models.centre_activity_model import CentreActivity
from app.models.centre_activity_preference_model import CentreActivityPreference
from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
from app.models.centre_activity_exclusion_model import CentreActivityExclusion

router = APIRouter()

@router.get("/activity")
async def get_activity_integrity(
    hours_back: int = Query(1, ge=1, le=168, description="Hours to look back (1-168)"),
    limit: int = Query(1000, ge=1, le=5000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Returns activity IDs and their last modified timestamps.
    Used by reconciliation service to detect data drift.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        activities = db.query(Activity).filter(
            Activity.modified_date >= cutoff_time
        ).order_by(Activity.id).limit(limit).offset(offset).all()
        
        records = []
        for activity in activities:
            records.append({
                "id": activity.id,
                "modified_date": activity.modified_date.isoformat(),
                "version_timestamp": int(activity.modified_date.timestamp() * 1000),
                "record_type": "activity"
            })
        
        # Get total count for pagination
        total_count = db.query(Activity).filter(
            Activity.modified_date >= cutoff_time
        ).count()
        
        return {
            "service": "activity",
            "endpoint": "/integrity/activity",
            "window_hours": hours_back,
            "cutoff_time": cutoff_time.isoformat(),
            "total_count": total_count,
            "returned_count": len(records),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(records)) < total_count,
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activity integrity check failed: {str(e)}")

@router.get("/centre-activity")
async def get_centre_activity_integrity(
    hours_back: int = Query(1, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns centre activity IDs and their last modified timestamps.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Query centre activities modified in the time window
        centre_activities = db.query(CentreActivity).filter(
            CentreActivity.modified_date >= cutoff_time
        ).order_by(CentreActivity.id).limit(limit).offset(offset).all()
        
        records = []
        for ca in centre_activities:
            # Use modified_date if available, otherwise created_date
            last_modified = ca.modified_date or ca.created_date
            
            records.append({
                "id": ca.id,
                "activity_id": ca.activity_id,
                "modified_date": last_modified.isoformat(),
                "version_timestamp": int(last_modified.timestamp() * 1000),
                "record_type": "centre_activity"
            })
        
        # Total count for pagination
        total_count = db.query(CentreActivity).filter(
            CentreActivity.modified_date >= cutoff_time
        ).count()
        
        return {
            "service": "activity",
            "endpoint": "/integrity/centre-activity",
            "window_hours": hours_back,
            "cutoff_time": cutoff_time.isoformat(),
            "total_count": total_count,
            "returned_count": len(records),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(records)) < total_count,
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centre activity integrity check failed: {str(e)}")

@router.get("/centre-activity-preference")
async def get_centre_activity_preference_integrity(
    hours_back: int = Query(1, ge=1, le=168),
    patient_id: Optional[int] = Query(None, description="Filter by specific patient"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns centre activity preference IDs and their last modified timestamps.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        query = db.query(CentreActivityPreference).filter(
            CentreActivityPreference.modified_date >= cutoff_time
        )
        
        if patient_id:
            query = query.filter(CentreActivityPreference.patient_id == patient_id)
            
        preferences = query.order_by(CentreActivityPreference.id).limit(limit).offset(offset).all()
        
        records = []
        for pref in preferences:
            # Use modified_date if available, otherwise created_date
            last_modified = pref.modified_date or pref.created_date
            
            records.append({
                "id": pref.id,
                "centre_activity_id": pref.centre_activity_id,
                "patient_id": pref.patient_id,
                "modified_date": last_modified.isoformat(),
                "version_timestamp": int(last_modified.timestamp() * 1000),
                "record_type": "centre_activity_preference"
            })
        
        return {
            "service": "activity",
            "endpoint": "/integrity/centre-activity-preference",
            "window_hours": hours_back,
            "patient_filter": patient_id,
            "total_count": len(records),
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centre activity preference integrity check failed: {str(e)}")

@router.get("/centre-activity-recommendation")
async def get_centre_activity_recommendation_integrity(
    hours_back: int = Query(1, ge=1, le=168),
    patient_id: Optional[int] = Query(None, description="Filter by specific patient"),
    doctor_id: Optional[str] = Query(None, description="Filter by specific doctor"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns centre activity recommendation IDs and their last modified timestamps.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        query = db.query(CentreActivityRecommendation).filter(
            CentreActivityRecommendation.modified_date >= cutoff_time
        )
        
        if patient_id:
            query = query.filter(CentreActivityRecommendation.patient_id == patient_id)
        if doctor_id:
            query = query.filter(CentreActivityRecommendation.doctor_id == doctor_id)
            
        recommendations = query.order_by(CentreActivityRecommendation.id).limit(limit).offset(offset).all()
        
        records = []
        for rec in recommendations:
            # Use modified_date if available, otherwise created_date
            last_modified = rec.modified_date or rec.created_date
            
            records.append({
                "id": rec.id,
                "centre_activity_id": rec.centre_activity_id,
                "patient_id": rec.patient_id,
                "doctor_id": rec.doctor_id,
                "modified_date": last_modified.isoformat(),
                "version_timestamp": int(last_modified.timestamp() * 1000),
                "record_type": "centre_activity_recommendation"
            })
        
        return {
            "service": "activity",
            "endpoint": "/integrity/centre-activity-recommendation",
            "window_hours": hours_back,
            "patient_filter": patient_id,
            "doctor_filter": doctor_id,
            "total_count": len(records),
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centre activity recommendation integrity check failed: {str(e)}")

@router.get("/centre-activity-exclusion")
async def get_centre_activity_exclusion_integrity(
    hours_back: int = Query(1, ge=1, le=168),
    patient_id: Optional[int] = Query(None, description="Filter by specific patient"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns centre activity exclusion IDs and their last modified timestamps.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        query = db.query(CentreActivityExclusion).filter(
            CentreActivityExclusion.modified_date >= cutoff_time
        )
        
        if patient_id:
            query = query.filter(CentreActivityExclusion.patient_id == patient_id)
            
        exclusions = query.order_by(CentreActivityExclusion.id).limit(limit).offset(offset).all()
        
        records = []
        for exclusion in exclusions:
            records.append({
                "id": exclusion.id,
                "centre_activity_id": exclusion.centre_activity_id,
                "patient_id": exclusion.patient_id,
                "modified_date": exclusion.modified_date.isoformat(),
                "version_timestamp": int(exclusion.modified_date.timestamp() * 1000),
                "record_type": "centre_activity_exclusion"
            })
        
        return {
            "service": "activity",
            "endpoint": "/integrity/centre-activity-exclusion",
            "window_hours": hours_back,
            "patient_filter": patient_id,
            "total_count": len(records),
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centre activity exclusion integrity check failed: {str(e)}")

@router.get("/summary")
async def get_integrity_summary(
    hours_back: int = Query(1, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Returns a summary of all activity-related record counts for the specified time window.
    Useful for high-level drift detection and monitoring.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Count records in each table
        activity_count = db.query(Activity).filter(
            Activity.modified_date >= cutoff_time
        ).count()
        
        centre_activity_count = db.query(CentreActivity).filter(
            CentreActivity.modified_date >= cutoff_time
        ).count()
        
        preference_count = db.query(CentreActivityPreference).filter(
            CentreActivityPreference.modified_date >= cutoff_time
        ).count()
        
        recommendation_count = db.query(CentreActivityRecommendation).filter(
            CentreActivityRecommendation.modified_date >= cutoff_time
        ).count()
        
        exclusion_count = db.query(CentreActivityExclusion).filter(
            CentreActivityExclusion.modified_date >= cutoff_time
        ).count()
        
        return {
            "service": "activity",
            "endpoint": "/integrity/summary",
            "window_hours": hours_back,
            "cutoff_time": cutoff_time.isoformat(),
            "record_counts": {
                "activity": activity_count,
                "centre_activity": centre_activity_count,
                "centre_activity_preference": preference_count,
                "centre_activity_recommendation": recommendation_count,
                "centre_activity_exclusion": exclusion_count,
                "total": (activity_count + centre_activity_count + preference_count + 
                         recommendation_count + exclusion_count)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integrity summary failed: {str(e)}")

# Health check endpoint for the integrity system
@router.get("/health")
async def integrity_health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify integrity system is working.
    """
    try:
        # Test database connectivity
        db.execute(text("SELECT 1"))
        
        # Get recent activity to verify data access
        recent_activity = db.query(Activity).filter(
            Activity.modified_date >= datetime.now() - timedelta(hours=24)
        ).first()
        
        return {
            "status": "healthy",
            "service": "activity",
            "database_connected": True,
            "recent_data_available": recent_activity is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Integrity health check failed: {str(e)}")
