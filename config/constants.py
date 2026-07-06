"""Central constants for MediMind AI."""

API_PREFIX = "/api/v1"
APP_TITLE = "MediMind AI API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Enterprise healthcare intelligence platform foundation"

# ── Table names ────────────────────────────────────────────────
TABLE_USERS = "users"
TABLE_PATIENTS = "patients"
TABLE_DOCTORS = "doctors"
TABLE_PATIENT_ALLERGIES = "patient_allergies"
TABLE_PATIENT_CHRONIC_CONDITIONS = "patient_chronic_conditions"
TABLE_DOCUMENTS = "documents"
TABLE_PRESCRIPTIONS = "prescriptions"
TABLE_MEDICATIONS = "medications"
TABLE_LAB_RESULTS = "lab_results"
TABLE_MEDICAL_TIMELINE = "medical_timeline"
TABLE_CHAT_SESSIONS = "chat_sessions"
TABLE_CHAT_MESSAGES = "chat_messages"
TABLE_CHAT_RETRIEVALS = "chat_retrievals"
TABLE_DRUG_INTERACTIONS = "drug_interactions"

from enum import Enum


class MessageRole(str, Enum):
    """Supported roles for chat conversation messages."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── Status constants ───────────────────────────────────────────
DOCUMENT_STATUS_PROCESSING = "PROCESSING"
DOCUMENT_STATUS_READY = "READY"
DOCUMENT_STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
DOCUMENT_STATUS_FAILED = "FAILED"
DOCUMENT_STATUS_DELETED = "deleted"

# ── Document upload configuration ──────────────────────────────
ALLOWED_DOCUMENT_TYPES = (".jpg", ".jpeg", ".png", ".pdf")
MAX_DOCUMENT_SIZE_MB = 15
DOCUMENT_STORAGE_BASE_PATH = "storage/documents"

DOCUMENT_TYPE_PRESCRIPTION_PRINTED = "prescription_printed"
DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN = "prescription_handwritten"
DOCUMENT_TYPE_LAB_REPORT = "lab_report"
DOCUMENT_TYPE_DRUG_PACKAGE = "drug_package"
DOCUMENT_TYPE_MEDICAL_BILL = "medical_bill"
DOCUMENT_TYPE_DISCHARGE_SUMMARY = "discharge_summary"
DOCUMENT_TYPE_INSURANCE_DOCUMENT = "insurance_document"
DOCUMENT_TYPE_MEDICAL_RECORD = "medical_record"
DOCUMENT_TYPES = (
    DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
    DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN,
    DOCUMENT_TYPE_LAB_REPORT,
    DOCUMENT_TYPE_DRUG_PACKAGE,
    DOCUMENT_TYPE_MEDICAL_BILL,
    DOCUMENT_TYPE_DISCHARGE_SUMMARY,
    DOCUMENT_TYPE_INSURANCE_DOCUMENT,
    DOCUMENT_TYPE_MEDICAL_RECORD,
)

MEDICATION_STATUS_ACTIVE = "ACTIVE"
MEDICATION_STATUS_COMPLETED = "COMPLETED"
MEDICATION_STATUS_DISCONTINUED = "DISCONTINUED"

# ── AI extraction configuration ────────────────────────────────
GEMINI_VISION_MODEL = "gemini-2.5-flash"
EXTRACTION_CONFIDENCE_THRESHOLD = 0.75

# ── Chat configuration ─────────────────────────────────────────
CHAT_MODEL = "gemini-2.5-flash"
RELEVANT_SCORE_THRESHOLD = 0.5
MAX_CHAT_HISTORY_MESSAGES = 10
NO_INFO_FALLBACK_MESSAGE = (
    "I don't have enough information in your medical records to answer that confidently. Please consult your doctor."
)
LISTING_TRIGGER_WORDS = (
    "show",
    "list",
    "give me",
    "what are",
    "display",
    "history",
    "all my",
    "everything",
    "complete",
    "full",
)
EXPLANATION_OVERRIDE_KEYWORDS = (
    "why",
    "explain",
    "how",
    "what happens",
    "side effect",
    "is it safe",
    "should i",
    "interaction",
    "can i take",
)
LAB_HISTORY_KEYWORDS = (
    "lab",
    "lab report",
    "lab_report",
    "blood test",
    "test result",
    "test data",
)
PRESCRIPTION_HISTORY_KEYWORDS = (
    "prescription",
    "medicine",
    "medication",
    "drug",
)

ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_STAGING = "staging"
ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_TESTING = "testing"
ENVIRONMENT_NAMES = (
    ENVIRONMENT_DEVELOPMENT,
    ENVIRONMENT_STAGING,
    ENVIRONMENT_PRODUCTION,
    ENVIRONMENT_TESTING,
)

LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"
LOG_LEVELS = (
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_CRITICAL,
)

REQUEST_ID_HEADER = "X-Request-ID"
LOG_DIRECTORY = "logs"
LOG_FILE_NAME = "app.log"
DEFAULT_SUCCESS_MESSAGE = "Operation successful"
DEFAULT_ERROR_MESSAGE = "An unexpected error occurred"
DEFAULT_VALIDATION_ERROR_MESSAGE = "Validation failed"
DEFAULT_AUTHENTICATION_ERROR_MESSAGE = "Authentication failed"
DEFAULT_DATABASE_ERROR_MESSAGE = "Database operation failed"
HEALTH_ENDPOINT_MESSAGE = "MediMind API Healthy"
UTC_TIMEZONE_NAME = "UTC"
JSON_LOG_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_LOG_FIELDS = (
    "timestamp",
    "request_id",
    "module_name",
    "function_name",
    "message",
)
JWT_ALGORITHM_DEFAULT = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES_DEFAULT = 60 * 24
DATABASE_POOL_SIZE_DEFAULT = 5
DATABASE_MAX_OVERFLOW_DEFAULT = 10
DATABASE_POOL_RECYCLE_DEFAULT = 1800
DATABASE_POOL_TIMEOUT_DEFAULT = 30
DATABASE_DRIVER_DEFAULT = "postgresql+psycopg2"
DATABASE_HOST_DEFAULT = "localhost"
DATABASE_PORT_DEFAULT = 5432
AUTH_TOKEN_TYPE_BEARER = "bearer"

# ── Database connection retry & monitoring ─────────────────────
DB_RETRY_MAX_ATTEMPTS = 5
DB_RETRY_BASE_DELAY_SECONDS = 5
DB_MONITOR_PING_INTERVAL_SECONDS = 60

# ── RAG & Pinecone configuration ───────────────────────────────
PINECONE_INDEX_NAME = "medimind-medical-records"
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 50
PINECONE_UPSERT_BATCH_SIZE = 100
METADATA_SCHEMA_VERSION = 1
