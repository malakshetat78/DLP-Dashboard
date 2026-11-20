import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict
import re

class AttributeBasedAccessControl:
    """
    Attribute-Based Access Control (ABE) system
    Allows defining who can access data based on user attributes
    """
    
    def __init__(self):
        self.policies = {}
        self.user_attributes = {}
        self.access_logs = []
    
    # ==================== User Attributes Management ====================
    
    def add_user_attributes(self, user_id: str, attributes: Dict[str, any]):
        if user_id not in self.user_attributes:
            self.user_attributes[user_id] = {}
        self.user_attributes[user_id].update(attributes)
        self.user_attributes[user_id]['updated_at'] = datetime.now().isoformat()
    
    def get_user_attributes(self, user_id: str) -> Dict:
        return self.user_attributes.get(user_id, {})
    
    def remove_user_attribute(self, user_id: str, attribute: str):
        if user_id in self.user_attributes and attribute in self.user_attributes[user_id]:
            del self.user_attributes[user_id][attribute]
    
    # ==================== Access Policies Management ====================
    
    def create_access_policy(self, file_id: str, policy: Dict):
        self.policies[file_id] = {
            'policy': policy,
            'created_at': datetime.now().isoformat(),
            'version': 1
        }
    
    def update_policy(self, file_id: str, new_policy: Dict):
        if file_id in self.policies:
            current_version = self.policies[file_id].get('version', 1)
            self.policies[file_id] = {
                'policy': new_policy,
                'updated_at': datetime.now().isoformat(),
                'version': current_version + 1
            }
    
    def get_policy(self, file_id: str) -> Dict:
        return self.policies.get(file_id, {}).get('policy', {})
    
    # ==================== Access Checks ====================
    
    def check_attribute_match(self, user_attrs: Dict, required_attrs: Dict) -> bool:
        for attr_name, attr_requirements in required_attrs.items():
            if attr_name not in user_attrs:
                return False
            user_value = user_attrs[attr_name]
            if isinstance(attr_requirements, list):
                if user_value not in attr_requirements:
                    return False
            elif isinstance(attr_requirements, dict):
                if 'min' in attr_requirements and user_value < attr_requirements['min']:
                    return False
                if 'max' in attr_requirements and user_value > attr_requirements['max']:
                    return False
            else:
                if user_value != attr_requirements:
                    return False
        return True
    
    def check_time_restrictions(self, time_policy: Dict) -> bool:
        if not time_policy:
            return True
        now = datetime.now()
        if 'days' in time_policy:
            if now.strftime('%A') not in time_policy['days']:
                return False
        if 'start' in time_policy and 'end' in time_policy:
            current_time = now.strftime('%H:%M')
            if not (time_policy['start'] <= current_time <= time_policy['end']):
                return False
        return True
    
    def check_expiry(self, expiry_date: str) -> bool:
        if not expiry_date:
            return True
        expiry = datetime.fromisoformat(expiry_date)
        return datetime.now() <= expiry
    
    def check_access(self, user_id: str, file_id: str, action: str, context: Dict = None) -> Dict:
        context = context or {}
        user_attrs = self.get_user_attributes(user_id)
        policy = self.get_policy(file_id)
        
        if not policy:
            return {'allowed': False, 'reason': 'No access policy defined for this file', 'restrictions': {}}
        
        if 'required_attributes' in policy:
            if not self.check_attribute_match(user_attrs, policy['required_attributes']):
                return {'allowed': False, 'reason': 'User does not meet required attributes', 'restrictions': policy['required_attributes']}
        
        if 'time_restrictions' in policy:
            if not self.check_time_restrictions(policy['time_restrictions']):
                return {'allowed': False, 'reason': 'Access not allowed at this time', 'restrictions': policy['time_restrictions']}
        
        if 'expiry_date' in policy:
            if not self.check_expiry(policy['expiry_date']):
                return {'allowed': False, 'reason': 'Access has expired', 'restrictions': {'expiry_date': policy['expiry_date']}}
        
        if 'actions_allowed' in policy:
            if action not in policy['actions_allowed']:
                return {'allowed': False, 'reason': f'Action "{action}" not allowed', 'restrictions': {'allowed_actions': policy['actions_allowed']}}
        
        if 'location_restrictions' in policy and 'location' in context:
            if context['location'] not in policy['location_restrictions']:
                return {'allowed': False, 'reason': 'Access not allowed from this location', 'restrictions': {'allowed_locations': policy['location_restrictions']}}
        
        self.log_access(user_id, file_id, action, True, context)
        return {'allowed': True, 'reason': 'Access granted', 'restrictions': {}}
    
    # ==================== Logging ====================
    
    def log_access(self, user_id: str, file_id: str, action: str, allowed: bool, context: Dict = None):
        self.access_logs.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'file_id': file_id,
            'action': action,
            'allowed': allowed,
            'context': context or {}
        })
    
    def get_access_logs(self, file_id: str = None, user_id: str = None, limit: int = 100) -> List[Dict]:
        logs = self.access_logs
        if file_id:
            logs = [log for log in logs if log['file_id'] == file_id]
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        return logs[-limit:]
    
    def detect_suspicious_access(self, threshold: int = 10) -> List[Dict]:
        failed_attempts = {}
        for log in self.access_logs:
            if not log['allowed']:
                key = (log['user_id'], log['file_id'])
                failed_attempts[key] = failed_attempts.get(key, 0) + 1
        return [{'user_id': k[0], 'file_id': k[1], 'failed_attempts': v} for k, v in failed_attempts.items() if v >= threshold]


# ==================== Example Usage ====================

if __name__ == "__main__":
    abac = AttributeBasedAccessControl()
    
    abac.add_user_attributes('user001', {
        'department': 'IT',
        'role': 'admin',
        'clearance_level': 5,
        'location': 'Egypt'
    })
    
    abac.add_user_attributes('user002', {
        'department': 'HR',
        'role': 'employee',
        'clearance_level': 2,
        'location': 'Egypt'
    })
    
    abac.create_access_policy('confidential_file_001', {
        'required_attributes': {
            'department': ['IT', 'Security'],
            'clearance_level': {'min': 4}
        },
        'actions_allowed': ['read', 'download'],
        'expiry_date': '2025-12-31'
    })
    
    result1 = abac.check_access('user001', 'confidential_file_001', 'read')
    print(f"✅ User 1 - Access: {result1['allowed']}")
    print(f"   Reason: {result1['reason']}")
    
    result2 = abac.check_access('user002', 'confidential_file_001', 'read')
    print(f"\n❌ User 2 - Access: {result2['allowed']}")
    print(f"   Reason: {result2['reason']}")
    
    logs = abac.get_access_logs(file_id='confidential_file_001')
    print(f"\n📊 Total access attempts: {len(logs)}")