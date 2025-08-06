# Security Architecture

Comprehensive security framework and implementation patterns for pysystemtrade's production trading environment.

## Executive Summary

The security architecture for pysystemtrade implements **defense-in-depth** principles with multi-layered security controls designed to protect financial data, trading operations, and system integrity. The framework addresses regulatory compliance requirements while maintaining operational efficiency in automated trading environments.

### **Security Architecture Vision**
*"A comprehensive security posture that protects financial assets, ensures regulatory compliance, and maintains system availability while enabling efficient automated trading operations through layered security controls and continuous monitoring."*

## Security Framework Overview

### **Security Domains**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Perimeter Security          Application Security               │
│  ┌─────────────┐             ┌─────────────┐                    │
│  │ Firewalls   │─────────────│ Authentication│                  │
│  │ WAF         │             │ Authorization │                  │
│  │ DDoS Prot   │             │ Input Valid   │                  │
│  └─────────────┘             └─────────────┘                    │
│                                      │                          │
│  Data Security               Infrastructure Security            │
│  ┌─────────────┐             ┌─────────────┐                    │
│  │ Encryption  │─────────────│ OS Hardening│                    │
│  │ Key Mgmt    │             │ Network Seg │                    │
│  │ Data Class  │             │ Monitoring  │                    │
│  └─────────────┘             └─────────────┘                    │
│                                      │                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Compliance & Governance                    │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │ Audit Trail │ │ Risk Mgmt   │ │ Regulatory  │       │    │
│  │  │ & Logging   │ │ Framework   │ │ Reporting   │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication & Authorization

### **Multi-Factor Authentication Framework**

#### **Authentication Architecture**
```python
class SecurityManager:
    """
    Centralized security management for all system components
    """
    def __init__(self):
        self.auth_providers = {
            'interactive_sessions': MultiFactorAuthProvider(),
            'api_access': TokenBasedAuthProvider(),
            'service_accounts': CertificateAuthProvider(),
            'broker_connections': CredentialVaultProvider()
        }
        
    def authenticate_user(self, context: AuthenticationContext):
        """
        Multi-factor authentication workflow
        """
        # Primary authentication (username/password)
        primary_auth = self._validate_primary_credentials(context)
        if not primary_auth.success:
            self._log_authentication_failure(context)
            raise AuthenticationError("Primary authentication failed")
            
        # Secondary authentication (MFA)
        mfa_auth = self._validate_mfa_token(context)
        if not mfa_auth.success:
            self._log_mfa_failure(context)
            raise AuthenticationError("MFA authentication failed")
            
        # Generate secure session token
        session_token = self._generate_session_token(context)
        
        self._log_successful_authentication(context)
        return AuthenticationResult(session_token, primary_auth, mfa_auth)
```

#### **Role-Based Access Control (RBAC)**
```python
class RoleBasedAccessControl:
    """
    Granular permission management for trading operations
    """
    ROLE_DEFINITIONS = {
        'system_administrator': {
            'permissions': ['system:*', 'data:*', 'config:*'],
            'restrictions': [],
            'session_timeout': 3600  # 1 hour
        },
        'trader': {
            'permissions': [
                'trading:place_orders', 'trading:cancel_orders',
                'data:read_prices', 'data:read_positions',
                'reports:view_pnl'
            ],
            'restrictions': ['config:modify', 'system:restart'],
            'session_timeout': 28800  # 8 hours
        },
        'risk_manager': {
            'permissions': [
                'trading:override_limits', 'trading:emergency_stop',
                'data:read_all', 'reports:generate_all'
            ],
            'restrictions': ['trading:place_orders'],
            'session_timeout': 7200  # 2 hours
        },
        'read_only_analyst': {
            'permissions': ['data:read_prices', 'reports:view_standard'],
            'restrictions': ['trading:*', 'config:*'],
            'session_timeout': 14400  # 4 hours
        }
    }
    
    def check_permission(self, user_role: str, requested_action: str) -> bool:
        """
        Validate user permissions for requested action
        """
        role_config = self.ROLE_DEFINITIONS.get(user_role)
        if not role_config:
            return False
            
        # Check explicit restrictions first
        for restriction in role_config['restrictions']:
            if self._matches_pattern(requested_action, restriction):
                return False
                
        # Check permissions
        for permission in role_config['permissions']:
            if self._matches_pattern(requested_action, permission):
                return True
                
        return False
```

### **API Security Framework**

#### **Token-Based Authentication**
```python
class APISecurityManager:
    """
    Secure API access management with JWT tokens
    """
    def __init__(self):
        self.token_signing_key = self._load_signing_key()
        self.token_encryption_key = self._load_encryption_key()
        
    def generate_api_token(self, user_context: UserContext) -> str:
        """
        Generate secure JWT token with embedded permissions
        """
        payload = {
            'user_id': user_context.user_id,
            'role': user_context.role,
            'permissions': user_context.permissions,
            'issued_at': datetime.utcnow().timestamp(),
            'expires_at': (datetime.utcnow() + timedelta(hours=8)).timestamp(),
            'session_id': str(uuid.uuid4()),
            'ip_address': user_context.ip_address
        }
        
        # Sign and encrypt token
        signed_token = jwt.encode(payload, self.token_signing_key, algorithm='RS256')
        encrypted_token = self._encrypt_token(signed_token)
        
        return encrypted_token
        
    def validate_api_token(self, encrypted_token: str) -> TokenValidationResult:
        """
        Validate and decode API token
        """
        try:
            # Decrypt token
            signed_token = self._decrypt_token(encrypted_token)
            
            # Verify signature and decode
            payload = jwt.decode(signed_token, self.token_signing_key, 
                               algorithms=['RS256'])
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload['expires_at']:
                return TokenValidationResult(False, "Token expired")
                
            # Validate session
            if not self._is_session_active(payload['session_id']):
                return TokenValidationResult(False, "Session inactive")
                
            return TokenValidationResult(True, payload)
            
        except Exception as e:
            return TokenValidationResult(False, f"Token validation failed: {e}")
```

## Data Encryption & Protection

### **Data Classification Framework**

#### **Data Sensitivity Levels**
```python
class DataClassificationFramework:
    """
    Data protection based on sensitivity classification
    """
    CLASSIFICATION_LEVELS = {
        'public': {
            'encryption': None,
            'access_control': 'none',
            'retention': 'indefinite',
            'examples': ['market_holidays', 'exchange_specs']
        },
        'internal': {
            'encryption': 'aes_256_transit',
            'access_control': 'authenticated_users',
            'retention': '7_years',
            'examples': ['historical_prices', 'analytics_results']
        },
        'confidential': {
            'encryption': 'aes_256_rest_transit',
            'access_control': 'role_based',
            'retention': '10_years',
            'examples': ['trading_positions', 'pnl_data', 'order_history']
        },
        'restricted': {
            'encryption': 'aes_256_rest_transit_key_rotation',
            'access_control': 'need_to_know',
            'retention': '10_years_secure_deletion',
            'examples': ['api_keys', 'broker_credentials', 'encryption_keys']
        }
    }
    
    def classify_data(self, data_type: str, content: Any) -> str:
        """
        Automatically classify data based on type and content analysis
        """
        classification_rules = [
            # Restricted data patterns
            (r'.*(?:password|key|secret|token).*', 'restricted'),
            (r'.*(?:credential|auth|api_key).*', 'restricted'),
            
            # Confidential data patterns  
            (r'.*(?:position|order|trade|pnl).*', 'confidential'),
            (r'.*(?:account|balance|exposure).*', 'confidential'),
            
            # Internal data patterns
            (r'.*(?:price|analytics|forecast).*', 'internal'),
            
            # Default to internal for unknown patterns
            (r'.*', 'internal')
        ]
        
        for pattern, classification in classification_rules:
            if re.match(pattern, data_type.lower()):
                return classification
                
        return 'internal'  # Safe default
```

#### **Encryption Implementation**
```python
class EncryptionManager:
    """
    Comprehensive encryption management for all data types
    """
    def __init__(self):
        self.key_manager = KeyManager()
        self.encryption_algorithms = {
            'aes_256': AES256Encryption(),
            'rsa_2048': RSA2048Encryption(),
            'chacha20': ChaCha20Encryption()
        }
        
    def encrypt_at_rest(self, data: bytes, classification: str) -> EncryptedData:
        """
        Encrypt data for storage with appropriate algorithm
        """
        if classification in ['confidential', 'restricted']:
            # Use AES-256-GCM for authenticated encryption
            key = self.key_manager.get_data_encryption_key()
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            ciphertext, auth_tag = cipher.encrypt_and_digest(data)
            
            return EncryptedData(
                algorithm='aes_256_gcm',
                ciphertext=ciphertext,
                nonce=nonce,
                auth_tag=auth_tag,
                key_id=self.key_manager.current_key_id
            )
        else:
            # Basic encryption for internal data
            return self._encrypt_basic(data)
            
    def encrypt_in_transit(self, data: bytes) -> bytes:
        """
        Encrypt data for network transmission
        """
        # Use TLS 1.3 with perfect forward secrecy
        # Implementation handled by transport layer
        return data  # TLS handles encryption transparently
```

### **Key Management System**

#### **Hierarchical Key Architecture**
```python
class KeyManager:
    """
    Enterprise-grade key management with rotation and escrow
    """
    def __init__(self):
        self.key_hierarchy = {
            'master_key': self._load_master_key(),
            'data_encryption_keys': {},
            'api_signing_keys': {},
            'session_keys': {}
        }
        self.key_rotation_schedule = KeyRotationScheduler()
        
    def get_data_encryption_key(self, purpose: str = 'general') -> bytes:
        """
        Retrieve or generate data encryption key
        """
        if purpose not in self.key_hierarchy['data_encryption_keys']:
            # Generate new DEK using master key
            new_dek = self._derive_key_from_master(purpose)
            self.key_hierarchy['data_encryption_keys'][purpose] = {
                'key': new_dek,
                'created_at': datetime.utcnow(),
                'rotation_due': datetime.utcnow() + timedelta(days=90),
                'version': 1
            }
            
        return self.key_hierarchy['data_encryption_keys'][purpose]['key']
        
    def rotate_keys(self):
        """
        Automatic key rotation based on schedule and events
        """
        rotation_results = []
        
        for key_type, keys in self.key_hierarchy.items():
            if key_type == 'master_key':
                continue  # Master key rotation is manual process
                
            for purpose, key_info in keys.items():
                if datetime.utcnow() >= key_info['rotation_due']:
                    result = self._rotate_key(key_type, purpose, key_info)
                    rotation_results.append(result)
                    
        return KeyRotationResult(rotation_results)
```

## Network Security

### **Network Segmentation Strategy**

#### **Multi-Tier Network Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                      Network Security Zones                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DMZ Zone (Public Access)                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Load Balancer │ WAF │ API Gateway                       │    │
│  │ Port: 443 (HTTPS only)                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                        ┌─────────────┐                          │
│                        │   Firewall  │                          │
│                        │   Rules     │                          │
│                        └─────────────┘                          │
│                              │                                  │
│  Application Zone (Restricted Access)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Trading Engine │ Portfolio Manager │ Analytics Engine │    │
│  │ Internal Communication: TLS 1.3                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                        ┌─────────────┐                          │
│                        │   Firewall  │                          │
│                        │   Rules     │                          │
│                        └─────────────┘                          │
│                              │                                  │
│  Data Zone (Highly Restricted)                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ MongoDB │ Redis │ Backup Systems │ Logging              │    │
│  │ No Direct External Access                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### **Firewall Configuration**
```python
class NetworkSecurityManager:
    """
    Automated firewall and network security management
    """
    FIREWALL_RULES = {
        'dmz_to_app': {
            'source': 'dmz_zone',
            'destination': 'app_zone',
            'allowed_ports': [8443],  # HTTPS API only
            'protocol': 'tcp',
            'rate_limit': '1000_requests_per_minute'
        },
        'app_to_data': {
            'source': 'app_zone', 
            'destination': 'data_zone',
            'allowed_ports': [27017, 6379],  # MongoDB, Redis
            'protocol': 'tcp',
            'authentication': 'required'
        },
        'broker_connections': {
            'source': 'app_zone',
            'destination': 'external',
            'allowed_hosts': [
                'gw-api.interactivebrokers.com',
                'api.ibkr.com'
            ],
            'ports': [7496, 7497, 4001, 4002],
            'protocol': 'tcp',
            'monitoring': 'high_priority'
        }
    }
    
    def configure_network_security(self):
        """
        Apply comprehensive network security configuration
        """
        security_config = NetworkSecurityConfig()
        
        # Configure firewall rules
        for rule_name, rule_config in self.FIREWALL_RULES.items():
            security_config.add_firewall_rule(rule_name, rule_config)
            
        # Enable intrusion detection
        security_config.enable_ids({
            'sensitivity': 'high',
            'alert_threshold': 'medium',
            'auto_block': True,
            'whitelist': self._get_trusted_ips()
        })
        
        # Configure DDoS protection
        security_config.enable_ddos_protection({
            'rate_limiting': True,
            'connection_limiting': True,
            'traffic_analysis': True
        })
        
        return security_config
```

### **TLS/SSL Implementation**

#### **Transport Security Configuration**
```python
class TLSManager:
    """
    Comprehensive TLS configuration for all communications
    """
    TLS_CONFIGURATION = {
        'min_version': 'TLSv1.3',
        'cipher_suites': [
            'TLS_AES_256_GCM_SHA384',
            'TLS_CHACHA20_POLY1305_SHA256',
            'TLS_AES_128_GCM_SHA256'
        ],
        'certificate_management': {
            'auto_renewal': True,
            'renewal_threshold': 30,  # days before expiry
            'validation_method': 'dns_challenge'
        },
        'hsts_policy': {
            'max_age': 31536000,  # 1 year
            'include_subdomains': True,
            'preload': True
        }
    }
    
    def configure_tls_context(self, service_type: str) -> ssl.SSLContext:
        """
        Create secure TLS context for specific service type
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Set minimum TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        
        # Configure cipher suites
        context.set_ciphers(':'.join(self.TLS_CONFIGURATION['cipher_suites']))
        
        # Enable certificate verification
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Load service-specific certificates
        cert_path, key_path = self._get_service_certificates(service_type)
        context.load_cert_chain(cert_path, key_path)
        
        return context
```

## Compliance & Audit Framework

### **Regulatory Compliance Management**

#### **Compliance Framework**
```python
class ComplianceManager:
    """
    Comprehensive regulatory compliance management
    """
    REGULATORY_REQUIREMENTS = {
        'sox_compliance': {
            'description': 'Sarbanes-Oxley compliance for financial reporting',
            'requirements': [
                'segregation_of_duties',
                'audit_trail_integrity',
                'access_control_reviews',
                'change_management_approval'
            ],
            'audit_frequency': 'quarterly',
            'retention_period': '7_years'
        },
        'gdpr_compliance': {
            'description': 'General Data Protection Regulation compliance',
            'requirements': [
                'data_subject_rights',
                'consent_management',
                'data_breach_notification',
                'privacy_by_design'
            ],
            'audit_frequency': 'annually',
            'retention_period': 'data_subject_lifetime'
        },
        'pci_dss': {
            'description': 'Payment Card Industry Data Security Standard',
            'requirements': [
                'secure_network_architecture',
                'data_encryption',
                'access_control',
                'regular_security_testing'
            ],
            'audit_frequency': 'annually',
            'retention_period': '3_years'
        }
    }
    
    def generate_compliance_report(self, regulation: str) -> ComplianceReport:
        """
        Generate comprehensive compliance assessment report
        """
        requirements = self.REGULATORY_REQUIREMENTS[regulation]
        
        report = ComplianceReport(regulation)
        
        for requirement in requirements['requirements']:
            assessment = self._assess_requirement_compliance(requirement)
            report.add_assessment(requirement, assessment)
            
        return report
```

#### **Audit Trail Implementation**
```python
class AuditTrailManager:
    """
    Comprehensive audit logging and trail management
    """
    def __init__(self):
        self.audit_logger = self._initialize_audit_logger()
        self.event_processors = {
            'authentication': AuthenticationEventProcessor(),
            'trading': TradingEventProcessor(),
            'data_access': DataAccessEventProcessor(),
            'system': SystemEventProcessor()
        }
        
    def log_audit_event(self, event_type: str, event_data: dict):
        """
        Log security and compliance events with full context
        """
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=event_data.get('user_id'),
            ip_address=event_data.get('ip_address'),
            session_id=event_data.get('session_id'),
            action=event_data.get('action'),
            resource=event_data.get('resource'),
            outcome=event_data.get('outcome'),
            details=event_data.get('details'),
            risk_score=self._calculate_risk_score(event_data)
        )
        
        # Process event through specialized processor
        processor = self.event_processors.get(event_type)
        if processor:
            enriched_event = processor.process(audit_event)
        else:
            enriched_event = audit_event
            
        # Write to multiple audit targets
        self._write_audit_event(enriched_event)
        
        # Check for suspicious patterns
        self._analyze_for_anomalies(enriched_event)
        
    def _write_audit_event(self, event: AuditEvent):
        """
        Write audit event to multiple secure destinations
        """
        # Primary audit log (tamper-evident)
        self.audit_logger.info(event.to_json())
        
        # Security information and event management (SIEM)
        self._send_to_siem(event)
        
        # Compliance database (long-term retention)
        self._store_in_compliance_db(event)
```

## Incident Response & Security Monitoring

### **Security Incident Response**

#### **Incident Response Framework**
```python
class SecurityIncidentResponse:
    """
    Automated security incident detection and response
    """
    INCIDENT_TYPES = {
        'authentication_attack': {
            'severity': 'high',
            'auto_response': ['block_ip', 'alert_security_team'],
            'escalation_threshold': 5,  # failed attempts
            'containment_actions': ['isolate_user_session']
        },
        'data_breach': {
            'severity': 'critical',
            'auto_response': ['immediate_isolation', 'notify_management'],
            'escalation_threshold': 1,  # immediate
            'containment_actions': ['stop_all_processes', 'preserve_evidence']
        },
        'suspicious_trading': {
            'severity': 'high',
            'auto_response': ['freeze_positions', 'alert_risk_manager'],
            'escalation_threshold': 3,  # unusual patterns
            'containment_actions': ['halt_strategy', 'manual_review']
        }
    }
    
    def handle_security_incident(self, incident_type: str, 
                                incident_data: dict) -> IncidentResponse:
        """
        Comprehensive incident handling with automated response
        """
        incident_config = self.INCIDENT_TYPES[incident_type]
        
        # Create incident record
        incident = SecurityIncident(
            incident_id=str(uuid.uuid4()),
            incident_type=incident_type,
            severity=incident_config['severity'],
            detected_at=datetime.utcnow(),
            data=incident_data,
            status='detected'
        )
        
        # Execute automated response actions
        response_actions = []
        for action in incident_config['auto_response']:
            result = self._execute_response_action(action, incident)
            response_actions.append(result)
            
        # Update incident status
        incident.status = 'responding'
        incident.response_actions = response_actions
        
        # Check for escalation
        if self._should_escalate(incident, incident_config):
            escalation_result = self._escalate_incident(incident)
            incident.escalation_result = escalation_result
            
        return IncidentResponse(incident, response_actions)
```

#### **Threat Detection Engine**
```python
class ThreatDetectionEngine:
    """
    Real-time threat detection using machine learning and rules
    """
    def __init__(self):
        self.ml_models = {
            'anomaly_detection': AnomalyDetectionModel(),
            'behavioral_analysis': BehavioralAnalysisModel(),
            'threat_classification': ThreatClassificationModel()
        }
        self.rule_engine = SecurityRuleEngine()
        
    def analyze_security_event(self, event: SecurityEvent) -> ThreatAssessment:
        """
        Multi-dimensional threat analysis
        """
        # Rule-based detection
        rule_results = self.rule_engine.evaluate(event)
        
        # ML-based anomaly detection
        anomaly_score = self.ml_models['anomaly_detection'].predict(event)
        
        # Behavioral analysis
        behavioral_score = self.ml_models['behavioral_analysis'].analyze(
            event, self._get_user_baseline(event.user_id)
        )
        
        # Threat classification
        threat_classification = self.ml_models['threat_classification'].classify(
            event, rule_results, anomaly_score, behavioral_score
        )
        
        # Calculate composite risk score
        risk_score = self._calculate_composite_risk_score(
            rule_results, anomaly_score, behavioral_score, threat_classification
        )
        
        return ThreatAssessment(
            event_id=event.event_id,
            risk_score=risk_score,
            threat_level=self._categorize_threat_level(risk_score),
            rule_matches=rule_results,
            anomaly_indicators=anomaly_score,
            behavioral_indicators=behavioral_score,
            threat_type=threat_classification,
            recommended_actions=self._get_recommended_actions(risk_score)
        )
```

## Security Testing & Validation

### **Security Testing Framework**

#### **Automated Security Testing**
```python
class SecurityTestingSuite:
    """
    Comprehensive automated security testing
    """
    def __init__(self):
        self.test_categories = {
            'authentication': AuthenticationSecurityTests(),
            'authorization': AuthorizationSecurityTests(),
            'encryption': EncryptionSecurityTests(),
            'network': NetworkSecurityTests(),
            'data_protection': DataProtectionSecurityTests()
        }
        
    def run_security_test_suite(self) -> SecurityTestResults:
        """
        Execute comprehensive security test suite
        """
        results = SecurityTestResults()
        
        for category, test_suite in self.test_categories.items():
            category_results = test_suite.run_all_tests()
            results.add_category_results(category, category_results)
            
            # Immediate alerting for critical failures
            critical_failures = category_results.get_critical_failures()
            if critical_failures:
                self._alert_security_team(category, critical_failures)
                
        return results
        
    def run_penetration_testing(self) -> PenetrationTestResults:
        """
        Automated penetration testing simulation
        """
        pen_test_scenarios = [
            SQLInjectionTest(),
            XSSTest(),
            AuthenticationBypassTest(),
            PrivilegeEscalationTest(),
            DataExfiltrationTest(),
            DenialOfServiceTest()
        ]
        
        results = PenetrationTestResults()
        
        for test_scenario in pen_test_scenarios:
            test_result = test_scenario.execute()
            results.add_test_result(test_result)
            
            if test_result.vulnerability_found:
                self._create_security_finding(test_result)
                
        return results
```

#### **Vulnerability Management**
```python
class VulnerabilityManager:
    """
    Comprehensive vulnerability assessment and management
    """
    def __init__(self):
        self.vulnerability_scanners = {
            'code_analysis': StaticCodeAnalysisScanner(),
            'dependency_check': DependencyVulnerabilityScanner(),
            'infrastructure': InfrastructureScanner(),
            'web_application': WebApplicationScanner()
        }
        
    def run_vulnerability_assessment(self) -> VulnerabilityAssessment:
        """
        Comprehensive vulnerability assessment across all components
        """
        assessment = VulnerabilityAssessment()
        
        for scanner_type, scanner in self.vulnerability_scanners.items():
            scan_results = scanner.scan()
            
            for vulnerability in scan_results.vulnerabilities:
                # Risk scoring based on CVSS
                risk_score = self._calculate_cvss_score(vulnerability)
                
                # Business impact assessment
                business_impact = self._assess_business_impact(vulnerability)
                
                # Remediation recommendation
                remediation = self._get_remediation_guidance(vulnerability)
                
                assessment.add_vulnerability(VulnerabilityFinding(
                    vulnerability_id=vulnerability.id,
                    scanner_type=scanner_type,
                    severity=vulnerability.severity,
                    cvss_score=risk_score,
                    business_impact=business_impact,
                    remediation_guidance=remediation,
                    discovered_date=datetime.utcnow()
                ))
                
        return assessment
```

---

**Next:** [Monitoring & Observability Architecture](07-monitoring-observability.md) - Comprehensive system monitoring and observability patterns