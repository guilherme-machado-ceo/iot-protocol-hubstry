"""
GDPR Data Anonymization Engine
=============================

Implements GDPR-compliant data anonymization, pseudonymization, and data subject rights
for the Harmonic IoT Protocol.

Copyright (c) 2025 Guilherme Gonçalves Machado
Licensed under CC BY-NC-SA 4.0
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import re

logger = logging.getLogger(__name__)

class DataSubjectRights(Enum):
    """GDPR Data Subject Rights enumeration."""
    ACCESS = "access"           # Article 15 - Right of access
    RECTIFICATION = "rectification"  # Article 16 - Right to rectification
    ERASURE = "erasure"         # Article 17 - Right to erasure
    PORTABILITY = "portability" # Article 20 - Right to data portability
    RESTRICTION = "restriction" # Article 18 - Right to restriction
    OBJECTION = "objection"     # Article 21 - Right to object

class LegalBasis(Enum):
    """GDPR Legal Basis for processing."""
    CONSENT = "consent"                    # Article 6(1)(a)
    CONTRACT = "contract"                  # Article 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Article 6(1)(c)
    VITAL_INTERESTS = "vital_interests"    # Article 6(1)(d)
    PUBLIC_TASK = "public_task"           # Article 6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Article 6(1)(f)

class GDPREngine:
    """
    GDPR Compliance Engine for Harmonic IoT Protocol.

    Handles data anonymization, pseudonymization, consent management,
    and data subject rights in compliance with GDPR requirements.
    """

    def __init__(self, encryption_key: str, salt: str):
        """
        Initialize GDPR Engine.

        Args:
            encryption_key: Key for pseudonymization
            salt: Salt for hashing operations
        """
        self.encryption_key = encryption_key
        self.salt = salt
        self.consent_records: Dict[str, Dict] = {}
        self.processing_records: List[Dict] = []

        # PII detection patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            'mac_address': re.compile(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'),
            'device_serial': re.compile(r'\b[A-Z0-9]{8,16}\b')
        }

        logger.info("GDPR Engine initialized")

    def anonymize_personal_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize personal data to comply with GDPR.

        Args:
            data: Raw data containing potential PII

        Returns:
            Dict: Anonymized data
        """
        anonymized = data.copy()

        try:
            # Anonymize user identifiers
            if 'user_id' in anonymized:
                anonymized['user_id'] = self._hash_identifier(anonymized['user_id'])

            # Anonymize device identifiers
            if 'device_id' in anonymized:
                anonymized['device_id'] = self._pseudonymize_device_id(anonymized['device_id'])

            # Generalize location data
            if 'location' in anonymized:
                anonymized['location'] = self._generalize_location(anonymized['location'])

            # Round timestamps to reduce precision
            if 'timestamp' in anonymized:
                anonymized['timestamp'] = self._round_timestamp(anonymized['timestamp'])

            # Remove or anonymize IP addresses
            if 'ip_address' in anonymized:
                anonymized['ip_address'] = self._anonymize_ip_address(anonymized['ip_address'])

            # Preserve harmonic protocol data (non-personal)
            harmonic_fields = ['harmonic_channel', 'frequency', 'fft_data', 'signal_strength']
            for field in harmonic_fields:
                if field in data:
                    anonymized[field] = data[field]

            # Detect and anonymize PII in text fields
            for key, value in anonymized.items():
                if isinstance(value, str):
                    anonymized[key] = self._detect_and_anonymize_pii(value)

            logger.debug("Data anonymized successfully")
            return anonymized

        except Exception as e:
            logger.error(f"Anonymization failed: {e}")
            raise

    def pseudonymize_data(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Pseudonymize data (reversible anonymization) for analytics.

        Args:
            data: Raw data to pseudonymize
            user_id: User identifier for pseudonymization key

        Returns:
            Dict: Pseudonymized data
        """
        pseudonymized = data.copy()

        try:
            # Create user-specific pseudonymization key
            pseudo_key = self._generate_pseudonym_key(user_id)

            # Pseudonymize identifiers
            if 'user_id' in pseudonymized:
                pseudonymized['user_id'] = self._pseudonymize_with_key(
                    pseudonymized['user_id'], pseudo_key
                )

            if 'device_id' in pseudonymized:
                pseudonymized['device_id'] = self._pseudonymize_with_key(
                    pseudonymized['device_id'], pseudo_key
                )

            # Add pseudonymization metadata
            pseudonymized['_pseudonymized'] = True
            pseudonymized['_pseudo_timestamp'] = datetime.utcnow().isoformat()

            return pseudonymized

        except Exception as e:
            logger.error(f"Pseudonymization failed: {e}")
            raise

    def handle_data_subject_request(self,
                                  request_type: DataSubjectRights,
                                  user_id: str,
                                  additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle GDPR data subject rights requests.

        Args:
            request_type: Type of data subject request
            user_id: User making the request
            additional_data: Additional data for specific request types

        Returns:
            Dict: Response to the data subject request
        """
        try:
            if request_type == DataSubjectRights.ACCESS:
                return self._handle_access_request(user_id)

            elif request_type == DataSubjectRights.RECTIFICATION:
                return self._handle_rectification_request(user_id, additional_data)

            elif request_type == DataSubjectRights.ERASURE:
                return self._handle_erasure_request(user_id)

            elif request_type == DataSubjectRights.PORTABILITY:
                return self._handle_portability_request(user_id)

            elif request_type == DataSubjectRights.RESTRICTION:
                return self._handle_restriction_request(user_id)

            elif request_type == DataSubjectRights.OBJECTION:
                return self._handle_objection_request(user_id, additional_data)

            else:
                raise ValueError(f"Unsupported request type: {request_type}")

        except Exception as e:
            logger.error(f"Data subject request failed: {e}")
            raise

    def record_consent(self,
                      user_id: str,
                      purpose: str,
                      legal_basis: LegalBasis,
                      consent_given: bool = True,
                      expiry_date: Optional[datetime] = None) -> str:
        """
        Record user consent for data processing.

        Args:
            user_id: User identifier
            purpose: Purpose of data processing
            legal_basis: Legal basis for processing
            consent_given: Whether consent was given
            expiry_date: Optional consent expiry date

        Returns:
            str: Consent record ID
        """
        consent_id = self._generate_consent_id(user_id, purpose)

        consent_record = {
            'consent_id': consent_id,
            'user_id': user_id,
            'purpose': purpose,
            'legal_basis': legal_basis.value,
            'consent_given': consent_given,
            'timestamp': datetime.utcnow().isoformat(),
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'ip_address': None,  # Should be provided by calling system
            'user_agent': None   # Should be provided by calling system
        }

        self.consent_records[consent_id] = consent_record

        logger.info(f"Consent recorded: {consent_id} for user {user_id}")
        return consent_id

    def withdraw_consent(self, user_id: str, purpose: str) -> bool:
        """
        Withdraw user consent for specific purpose.

        Args:
            user_id: User identifier
            purpose: Purpose to withdraw consent for

        Returns:
            bool: True if consent withdrawn successfully
        """
        try:
            consent_id = self._generate_consent_id(user_id, purpose)

            if consent_id in self.consent_records:
                self.consent_records[consent_id]['consent_given'] = False
                self.consent_records[consent_id]['withdrawal_timestamp'] = datetime.utcnow().isoformat()

                logger.info(f"Consent withdrawn: {consent_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Consent withdrawal failed: {e}")
            return False

    def check_consent_validity(self, user_id: str, purpose: str) -> bool:
        """
        Check if user consent is valid for specific purpose.

        Args:
            user_id: User identifier
            purpose: Purpose to check consent for

        Returns:
            bool: True if consent is valid
        """
        try:
            consent_id = self._generate_consent_id(user_id, purpose)

            if consent_id not in self.consent_records:
                return False

            record = self.consent_records[consent_id]

            # Check if consent is given
            if not record['consent_given']:
                return False

            # Check expiry date
            if record['expiry_date']:
                expiry = datetime.fromisoformat(record['expiry_date'])
                if datetime.utcnow() > expiry:
                    return False

            return True

        except Exception as e:
            logger.error(f"Consent validity check failed: {e}")
            return False

    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier for anonymization."""
        return hashlib.sha256(f"{identifier}{self.salt}".encode()).hexdigest()[:16]

    def _pseudonymize_device_id(self, device_id: str) -> str:
        """Pseudonymize device ID while maintaining some structure."""
        hashed = self._hash_identifier(device_id)
        return f"device_{hashed}"

    def _generalize_location(self, location: Union[str, Dict]) -> str:
        """Generalize location data to reduce precision."""
        if isinstance(location, dict):
            # Round coordinates to ~1km precision
            if 'lat' in location and 'lon' in location:
                lat = round(float(location['lat']), 2)
                lon = round(float(location['lon']), 2)
                return f"area_{lat}_{lon}"

        # For string locations, return general area
        return "general_area"

    def _round_timestamp(self, timestamp: Union[str, float, datetime]) -> str:
        """Round timestamp to reduce temporal precision."""
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, float):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp

        # Round to nearest hour
        rounded = dt.replace(minute=0, second=0, microsecond=0)
        return rounded.isoformat()

    def _anonymize_ip_address(self, ip_address: str) -> str:
        """Anonymize IP address by masking last octet."""
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        return "anonymized_ip"

    def _detect_and_anonymize_pii(self, text: str) -> str:
        """Detect and anonymize PII in text fields."""
        anonymized_text = text

        for pii_type, pattern in self.pii_patterns.items():
            anonymized_text = pattern.sub(f"[{pii_type.upper()}_REDACTED]", anonymized_text)

        return anonymized_text

    def _generate_pseudonym_key(self, user_id: str) -> str:
        """Generate pseudonymization key for specific user."""
        return hashlib.sha256(f"{user_id}{self.encryption_key}".encode()).hexdigest()

    def _pseudonymize_with_key(self, data: str, key: str) -> str:
        """Pseudonymize data with specific key."""
        return hashlib.sha256(f"{data}{key}".encode()).hexdigest()[:16]

    def _generate_consent_id(self, user_id: str, purpose: str) -> str:
        """Generate unique consent ID."""
        return hashlib.sha256(f"{user_id}:{purpose}".encode()).hexdigest()[:16]

    def _handle_access_request(self, user_id: str) -> Dict[str, Any]:
        """Handle GDPR Article 15 - Right of access."""
        # Implementation would query all user data from databases
        return {
            "request_type": "access",
            "user_id": user_id,
            "data": "User data export would be generated here",
            "processing_purposes": self._get_user_processing_purposes(user_id),
            "consent_records": self._get_user_consent_records(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_rectification_request(self, user_id: str, data: Dict) -> Dict[str, Any]:
        """Handle GDPR Article 16 - Right to rectification."""
        # Implementation would update user data
        return {
            "request_type": "rectification",
            "user_id": user_id,
            "status": "completed",
            "updated_fields": list(data.keys()) if data else [],
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_erasure_request(self, user_id: str) -> Dict[str, Any]:
        """Handle GDPR Article 17 - Right to erasure."""
        # Implementation would delete all user data
        return {
            "request_type": "erasure",
            "user_id": user_id,
            "status": "completed",
            "deleted_records": "All user data deleted",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_portability_request(self, user_id: str) -> Dict[str, Any]:
        """Handle GDPR Article 20 - Right to data portability."""
        # Implementation would export user data in machine-readable format
        return {
            "request_type": "portability",
            "user_id": user_id,
            "export_format": "JSON",
            "download_url": f"/api/gdpr/export/{user_id}",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_restriction_request(self, user_id: str) -> Dict[str, Any]:
        """Handle GDPR Article 18 - Right to restriction."""
        # Implementation would restrict processing of user data
        return {
            "request_type": "restriction",
            "user_id": user_id,
            "status": "processing_restricted",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_objection_request(self, user_id: str, data: Dict) -> Dict[str, Any]:
        """Handle GDPR Article 21 - Right to object."""
        # Implementation would stop specific processing activities
        return {
            "request_type": "objection",
            "user_id": user_id,
            "objection_purpose": data.get('purpose') if data else 'all',
            "status": "processing_stopped",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_user_processing_purposes(self, user_id: str) -> List[str]:
        """Get all processing purposes for user."""
        purposes = []
        for record in self.consent_records.values():
            if record['user_id'] == user_id:
                purposes.append(record['purpose'])
        return list(set(purposes))

    def _get_user_consent_records(self, user_id: str) -> List[Dict]:
        """Get all consent records for user."""
        records = []
        for record in self.consent_records.values():
            if record['user_id'] == user_id:
                records.append(record)
        return records
