"""
Offline Cache System for Dragofactu.

Provides:
- LocalCache: Caches API responses as JSON files in ~/.dragofactu/cache/
- OperationQueue: Queues write operations (create/update/delete) for later sync
- ConnectivityMonitor: Detects online/offline state
"""
import json
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger('dragofactu.offline')

# Entity types that can be cached
CACHEABLE_ENTITIES = ['clients', 'products', 'documents', 'workers', 'diary', 'suppliers', 'reminders', 'dashboard_stats']

# Max age for cache data (seconds) before considered stale
CACHE_MAX_AGE = 3600  # 1 hour


class LocalCache:
    """
    File-based JSON cache for API data.

    Stores responses in ~/.dragofactu/cache/<entity>.json with metadata.
    Each cache file contains:
    {
        "timestamp": "2026-02-07T12:00:00",
        "entity": "clients",
        "data": { ... API response ... }
    }
    """

    def __init__(self):
        self.cache_dir = Path.home() / ".dragofactu" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, entity: str) -> Path:
        return self.cache_dir / f"{entity}.json"

    def save(self, entity: str, data: Any) -> bool:
        """Save API response data to cache."""
        if entity not in CACHEABLE_ENTITIES:
            return False
        try:
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "entity": entity,
                "data": data
            }
            self._cache_path(entity).write_text(
                json.dumps(cache_entry, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
            logger.debug(f"Cached {entity} data")
            return True
        except Exception as e:
            logger.error(f"Error caching {entity}: {e}")
            return False

    def load(self, entity: str, max_age: int = CACHE_MAX_AGE) -> Optional[Any]:
        """
        Load cached data for entity.

        Args:
            entity: Entity type name
            max_age: Maximum cache age in seconds. 0 = no age check.

        Returns:
            Cached data dict or None if not found/expired.
        """
        path = self._cache_path(entity)
        if not path.exists():
            return None
        try:
            cache_entry = json.loads(path.read_text(encoding='utf-8'))
            if max_age > 0:
                cached_time = datetime.fromisoformat(cache_entry["timestamp"])
                age = (datetime.now() - cached_time).total_seconds()
                if age > max_age:
                    logger.debug(f"Cache for {entity} expired (age: {age:.0f}s)")
                    return None
            return cache_entry.get("data")
        except Exception as e:
            logger.error(f"Error loading cache for {entity}: {e}")
            return None

    def get_cache_age(self, entity: str) -> Optional[float]:
        """Get cache age in seconds, or None if no cache."""
        path = self._cache_path(entity)
        if not path.exists():
            return None
        try:
            cache_entry = json.loads(path.read_text(encoding='utf-8'))
            cached_time = datetime.fromisoformat(cache_entry["timestamp"])
            return (datetime.now() - cached_time).total_seconds()
        except Exception:
            return None

    def clear(self, entity: str = None):
        """Clear cache for entity, or all caches if entity is None."""
        if entity:
            path = self._cache_path(entity)
            if path.exists():
                path.unlink()
                logger.info(f"Cleared cache for {entity}")
        else:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()
            logger.info("Cleared all cache")

    def has_cache(self, entity: str) -> bool:
        """Check if entity has any cached data (even expired)."""
        return self._cache_path(entity).exists()


class OperationQueue:
    """
    Queue for pending write operations when offline.

    Operations are stored in ~/.dragofactu/pending_operations.json.
    Each operation:
    {
        "id": "unique-id",
        "type": "create" | "update" | "delete",
        "entity": "clients" | "products" | ...,
        "entity_id": "uuid-if-applicable",
        "data": { ... payload ... },
        "timestamp": "2026-02-07T12:00:00",
        "retries": 0
    }
    """
    MAX_RETRIES = 3

    def __init__(self):
        self._queue_file = Path.home() / ".dragofactu" / "pending_operations.json"
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._operations: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self._queue_file.exists():
            try:
                return json.loads(self._queue_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.error(f"Error loading operation queue: {e}")
        return []

    def _save(self):
        try:
            self._queue_file.write_text(
                json.dumps(self._operations, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Error saving operation queue: {e}")

    @property
    def pending_count(self) -> int:
        return len(self._operations)

    @property
    def operations(self) -> List[Dict]:
        return list(self._operations)

    def add(self, op_type: str, entity: str, data: dict, entity_id: str = None):
        """
        Add operation to queue.

        Args:
            op_type: "create", "update", or "delete"
            entity: Entity type (e.g. "clients", "products")
            data: Payload dict
            entity_id: Entity UUID (for update/delete)
        """
        import uuid as _uuid
        op = {
            "id": str(_uuid.uuid4()),
            "type": op_type,
            "entity": entity,
            "entity_id": entity_id,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "retries": 0
        }
        self._operations.append(op)
        self._save()
        logger.info(f"Queued {op_type} {entity} operation (total pending: {len(self._operations)})")

    def sync(self, api_client) -> Dict[str, int]:
        """
        Sync all pending operations with the API.

        Returns dict with counts: {"synced": N, "failed": N, "remaining": N}
        """
        if not self._operations:
            return {"synced": 0, "failed": 0, "remaining": 0}

        synced = []
        failed = []

        for op in list(self._operations):
            try:
                self._execute_operation(api_client, op)
                synced.append(op)
            except Exception as e:
                op["retries"] = op.get("retries", 0) + 1
                op["last_error"] = str(e)
                if op["retries"] >= self.MAX_RETRIES:
                    failed.append(op)
                    logger.error(f"Operation {op['id']} failed permanently after {self.MAX_RETRIES} retries: {e}")
                else:
                    logger.warning(f"Operation {op['id']} retry {op['retries']}: {e}")

        # Remove synced and permanently failed operations
        remove_ids = {op["id"] for op in synced + failed}
        self._operations = [op for op in self._operations if op["id"] not in remove_ids]
        self._save()

        result = {
            "synced": len(synced),
            "failed": len(failed),
            "remaining": len(self._operations)
        }
        logger.info(f"Sync result: {result}")
        return result

    def _execute_operation(self, api, op: Dict):
        """Execute a single queued operation via API."""
        entity = op["entity"]
        op_type = op["type"]
        data = op.get("data", {})
        entity_id = op.get("entity_id")

        if op_type == "create":
            if entity == "clients":
                api.create_client(**data)
            elif entity == "products":
                api.create_product(**data)
            elif entity == "documents":
                api.create_document(**data)
            elif entity == "workers":
                api.create_worker(**data)
            elif entity == "diary":
                api.create_diary_entry(**data)
            elif entity == "suppliers":
                api.create_supplier(**data)
            elif entity == "reminders":
                api.create_reminder(**data)
            else:
                raise ValueError(f"Unknown entity for create: {entity}")

        elif op_type == "update":
            if not entity_id:
                raise ValueError("entity_id required for update")
            if entity == "clients":
                api.update_client(entity_id, **data)
            elif entity == "products":
                api.update_product(entity_id, **data)
            elif entity == "documents":
                api.update_document(entity_id, **data)
            elif entity == "workers":
                api.update_worker(entity_id, **data)
            elif entity == "diary":
                api.update_diary_entry(entity_id, **data)
            elif entity == "suppliers":
                api.update_supplier(entity_id, **data)
            elif entity == "reminders":
                api.update_reminder(entity_id, **data)
            else:
                raise ValueError(f"Unknown entity for update: {entity}")

        elif op_type == "delete":
            if not entity_id:
                raise ValueError("entity_id required for delete")
            if entity == "clients":
                api.delete_client(entity_id)
            elif entity == "products":
                api.delete_product(entity_id)
            elif entity == "documents":
                api.delete_document(entity_id)
            elif entity == "workers":
                api.delete_worker(entity_id)
            elif entity == "diary":
                api.delete_diary_entry(entity_id)
            elif entity == "suppliers":
                api.delete_supplier(entity_id)
            elif entity == "reminders":
                api.delete_reminder(entity_id)
            else:
                raise ValueError(f"Unknown entity for delete: {entity}")
        else:
            raise ValueError(f"Unknown operation type: {op_type}")

    def clear(self):
        """Clear all pending operations."""
        self._operations = []
        self._save()
        logger.info("Cleared operation queue")


class ConnectivityMonitor:
    """
    Monitors connectivity to the API server.

    Uses a lightweight health check to detect online/offline transitions.
    """

    def __init__(self):
        self._is_online = True
        self._last_check: float = 0
        self._check_interval = 30  # seconds between checks
        self._lock = threading.Lock()
        self._listeners = []

    @property
    def is_online(self) -> bool:
        return self._is_online

    def add_listener(self, callback):
        """Add callback for connectivity changes. Called with (is_online: bool)."""
        self._listeners.append(callback)

    def check_now(self, api_client) -> bool:
        """
        Force connectivity check.

        Returns True if online.
        """
        with self._lock:
            try:
                health = api_client.health_check()
                new_status = health.get("status") == "healthy"
            except Exception:
                new_status = False

            old_status = self._is_online
            self._is_online = new_status
            self._last_check = time.time()

            if old_status != new_status:
                logger.info(f"Connectivity changed: {'online' if new_status else 'offline'}")
                for listener in self._listeners:
                    try:
                        listener(new_status)
                    except Exception as e:
                        logger.error(f"Error in connectivity listener: {e}")

            return new_status

    def should_check(self) -> bool:
        """Whether enough time has passed for a new check."""
        return (time.time() - self._last_check) >= self._check_interval

    def set_offline(self):
        """Manually mark as offline (e.g. after a ConnectionError)."""
        with self._lock:
            if self._is_online:
                self._is_online = False
                logger.info("Marked as offline (connection error)")
                for listener in self._listeners:
                    try:
                        listener(False)
                    except Exception as e:
                        logger.error(f"Error in connectivity listener: {e}")

    def set_online(self):
        """Manually mark as online (e.g. after successful request)."""
        with self._lock:
            if not self._is_online:
                self._is_online = True
                self._last_check = time.time()
                logger.info("Back online")
                for listener in self._listeners:
                    try:
                        listener(True)
                    except Exception as e:
                        logger.error(f"Error in connectivity listener: {e}")


# ============================================================================
# Singleton instances
# ============================================================================

_cache: Optional[LocalCache] = None
_queue: Optional[OperationQueue] = None
_monitor: Optional[ConnectivityMonitor] = None


def get_cache() -> LocalCache:
    global _cache
    if _cache is None:
        _cache = LocalCache()
    return _cache


def get_operation_queue() -> OperationQueue:
    global _queue
    if _queue is None:
        _queue = OperationQueue()
    return _queue


def get_connectivity_monitor() -> ConnectivityMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ConnectivityMonitor()
    return _monitor
