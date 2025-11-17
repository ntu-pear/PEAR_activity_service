from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class MapperUtil:
    """
    Universal mapper that handles all source-to-target transformations
    Configured for Patient Service → Activity Service mappings
    """
    
    def __init__(self):
        # Mapping configurations
        self.mapping_configs = {
            # Patient Service → Activity Service
            'patient_service_to_activity': {
                'source_service': 'patient-service',
                'target_service': 'activity-service', 
                'entity_type': 'patient',
                'required_fields': ['id', 'name'],
                'field_mappings': {
                    # Direct mappings (source_field: target_field) - using snake_case
                    'id': 'id',
                    'name': 'name',
                    'preferredName': 'preferred_name',
                    'isActive': 'is_active',
                    'isDeleted': 'is_deleted',
                    'updateBit': 'update_bit',
                    'startDate': 'start_date',
                    'endDate': 'end_date',
                    'createdDate': 'created_date',
                    'modifiedDate': 'modified_date',
                    'createdById': 'created_by_id',
                    'modifiedById': 'modified_by_id',
                },
                'field_transforms': {
                    # Special transformations (target_field: transform_function)
                    'is_active': lambda x: self._convert_boolean(x, "1"),
                    'is_deleted': lambda x: self._convert_boolean(x, "0"), 
                    'update_bit': lambda x: self._convert_boolean(x, "1"),
                    'start_date': lambda x: self._parse_datetime(x) or datetime.now(),
                    'end_date': lambda x: self._parse_datetime(x),
                    'created_date': lambda x: self._parse_datetime(x) or datetime.now(),
                    'modified_date': lambda x: self._parse_datetime(x) or datetime.now(),
                },
                'defaults': {
                    'is_active': '1',
                    'is_deleted': '0',
                    'update_bit': '1',
                    'created_by_id': 'patient_service',
                    'modified_by_id': 'patient_service'
                },
                'ignored_fields': [
                    # Source fields to ignore
                    'nric', 'address', 'tempAddress', 'homeNo', 'handphoneNo',
                    'profilePicture', 'privacyLevel', 'preferredLanguageId',
                    'isApproved', 'isRespiteCare', 'autoGame', 'inActiveReason',
                    'terminationReason', 'inActiveDate', 'dateOfBirth', 'gender'
                ]
            },
            
            # Patient Allocation mapping - fields have same names, just need case conversion
            'patient_allocation_service_to_activity': {
                'source_service': 'patient-service',
                'target_service': 'activity-service',
                'entity_type': 'patient_allocation',
                'required_fields': ['id', 'patientId', 'doctorId', 'gameTherapistId', 'supervisorId', 'caregiverId'],
                'field_mappings': {
                    # Direct mappings - convert camelCase to snake_case
                    'id': 'id',
                    'active': 'active',
                    'isDeleted': 'is_deleted',
                    'patientId': 'patient_id',
                    'doctorId': 'doctor_id',
                    'gameTherapistId': 'game_therapist_id',
                    'supervisorId': 'supervisor_id',
                    'caregiverId': 'caregiver_id',
                    'tempDoctorId': 'temp_doctor_id',
                    'tempCaregiverId': 'temp_caregiver_id',
                    'createdDate': 'created_date',
                    'modifiedDate': 'modified_date',
                    'CreatedById': 'created_by_id',
                    'ModifiedById': 'modified_by_id',
                },
                'field_transforms': {
                    'is_deleted': lambda x: self._convert_boolean(x, "0"),
                    'created_date': lambda x: self._parse_datetime(x) or datetime.now(),
                    'modified_date': lambda x: self._parse_datetime(x) or datetime.now(),
                    'temp_doctor_id': lambda x: str(x) if x is not None else None,
                    'temp_caregiver_id': lambda x: str(x) if x is not None else None,
                },
                'defaults': {
                    'active': 'Y',
                    'is_deleted': '0',
                    'created_by_id': 'patient_service',
                    'modified_by_id': 'patient_service'
                },
                'ignored_fields': [
                    # Ignore guardian relationships for now since activity service does not use them
                    'guardianId', 'guardian2Id'
                ]
            },
        }
    
    def map_data(self, source_data: Dict[str, Any], mapping_key: str, 
                 operation: str = 'create') -> Optional[Dict[str, Any]]:
        """
        Universal mapping function
        
        Args:
            source_data: Source data dictionary
            mapping_key: Key for mapping config (e.g., 'patient_service_to_activity')
            operation: 'create' or 'update'
            
        Returns:
            Mapped data dictionary or None if mapping fails
        """
        try:
            config = self.mapping_configs.get(mapping_key)
            if not config:
                logger.error(f"Mapping configuration not found: {mapping_key}")
                return None
            
            # Validate required fields for create operations
            if operation == 'create':
                if not self._validate_required_fields(source_data, config['required_fields']):
                    return None
            
            mapped_data = {}
            
            # Apply field mappings
            for source_field, target_field in config['field_mappings'].items():
                if source_field in source_data:
                    value = source_data[source_field]
                    
                    # Debug logging for timestamp fields
                    if 'date' in target_field.lower():
                        logger.debug(f"Processing timestamp: {source_field}={value} (type: {type(value)})")
                    
                    # Apply transformation if defined
                    if target_field in config.get('field_transforms', {}):
                        transform_func = config['field_transforms'][target_field]
                        try:
                            transformed_value = transform_func(value)
                            if 'date' in target_field.lower():
                                logger.debug(f"Transformed to: {transformed_value} (type: {type(transformed_value)})")
                            value = transformed_value
                        except Exception as e:
                            logger.warning(f"Transform failed for {target_field}: {e}")
                            continue
                    
                    # Only add non-None values for updates
                    if operation == 'update' and value is None:
                        if target_field == 'modified_date':
                            logger.error(f"modified_date is None after transform! Source: {source_field}={source_data.get(source_field)}")
                        continue
                        
                    mapped_data[target_field] = value
            
            # Apply defaults for create operations or when required fields are missing
            if operation == 'create':
                for target_field, default_value in config.get('defaults', {}).items():
                    if target_field not in mapped_data:
                        mapped_data[target_field] = default_value
            elif operation == 'update':
                # For updates, ONLY default modified_by_id if missing
                # modified_date should ALWAYS come from source data
                critical_defaults = {'modified_by_id'}
                for target_field, default_value in config.get('defaults', {}).items():
                    if target_field in critical_defaults and target_field not in mapped_data:
                        mapped_data[target_field] = default_value
            
            if not mapped_data:
                logger.warning(f"No mappable fields found for {mapping_key}")
                return None
            
            self._log_mapping_success(config, source_data.get('id'), operation)
            return mapped_data
            
        except Exception as e:
            logger.error(f"Mapping failed for {mapping_key}: {str(e)}")
            logger.error(f"Source data: {source_data}")
            return None
    
    def get_mapping_info(self, mapping_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific mapping configuration"""
        config = self.mapping_configs.get(mapping_key)
        if not config:
            return None
            
        return {
            'source_service': config['source_service'],
            'target_service': config['target_service'],
            'entity_type': config['entity_type'],
            'mapped_fields': len(config['field_mappings']),
            'ignored_fields': len(config['ignored_fields']),
            'field_mappings': config['field_mappings'],
            'has_transforms': len(config.get('field_transforms', {})) > 0,
            'defaults': config.get('defaults', {})
        }
    
    def list_all_mappings(self) -> List[str]:
        """List all available mapping keys"""
        return list(self.mapping_configs.keys())
    
    # Helper methods
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate required fields are present"""
        missing = [field for field in required_fields if field not in data or data[field] is None]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return False
        return True
    
    def _parse_datetime(self, datetime_str: Any) -> Optional[datetime]:
        """Parse datetime string consistently WITHOUT timezone conversion"""
        if not datetime_str:
            return None
        
        try:
            if isinstance(datetime_str, str):
                if 'T' in datetime_str:
                    # Remove any existing timezone markers to keep as naive datetime
                    clean_str = datetime_str.replace('Z', '').replace('+00:00', '')
                    return datetime.fromisoformat(clean_str)
                else:
                    # Try datetime format first
                    try:
                        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # If that fails, try date-only format and add default time
                        try:
                            date_part = datetime.strptime(datetime_str, '%Y-%m-%d')
                            return date_part.replace(hour=0, minute=0, second=0)
                        except ValueError:
                            # Try ISO date format
                            clean_str = datetime_str.replace('Z', '').replace('+00:00', '')
                            return datetime.fromisoformat(clean_str)
            elif isinstance(datetime_str, datetime):
                return datetime_str
            return None
        except Exception as e:
            logger.warning(f"Failed to parse datetime: {datetime_str}, error: {str(e)}")
            return None
    
    def _convert_boolean(self, value: Any, default: str = "0") -> str:
        """Convert boolean values to string representation for database"""
        if value is None:
            return default
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, str):
            # Handle string boolean representations
            if value.lower() in ('true', '1', 'yes'):
                return "1"
            elif value.lower() in ('false', '0', 'no'):
                return "0"
        # For numeric values
        try:
            return "1" if int(value) else "0"
        except (ValueError, TypeError):
            return default
    
    def _log_mapping_success(self, config: Dict[str, Any], source_id: Any, operation: str):
        """Log successful mapping"""
        logger.info(f"✅ {operation.upper()} mapping: {config['source_service']} → "
                   f"{config['target_service']} ({config['entity_type']} ID: {source_id})")


# Global instance for easy import
mapper = MapperUtil()


# Convenience functions for the patient mapper
def map_patient_create(source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map patient data for create operation"""
    return mapper.map_data(source_data, 'patient_service_to_activity', 'create')


def map_patient_update(source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map patient data for update operation"""
    return mapper.map_data(source_data, 'patient_service_to_activity', 'update')


def get_patient_mapping_info() -> Optional[Dict[str, Any]]:
    """Get patient mapping information"""
    return mapper.get_mapping_info('patient_service_to_activity')


# Convenience functions for patient allocation mapper
def map_patient_allocation_create(source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map patient allocation data for create operation"""
    return mapper.map_data(source_data, 'patient_allocation_service_to_activity', 'create')


def map_patient_allocation_update(source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map patient allocation data for update operation"""
    return mapper.map_data(source_data, 'patient_allocation_service_to_activity', 'update')


def get_patient_allocation_mapping_info() -> Optional[Dict[str, Any]]:
    """Get patient allocation mapping information"""
    return mapper.get_mapping_info('patient_allocation_service_to_activity')
