from pathlib import Path
from typing import Any
import uuid

import faiss

from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.system.i_logging import ILogger


class FaissMemoryPool(IMemoryPool):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.pool = dict[Any, faiss.IndexFlatL2 | faiss.IndexIDMap]()

    def add_to_pool(
        self,
        key: Any,
        index: faiss.IndexFlatL2 | faiss.IndexIDMap,
        file_caller: str = "",
    ) -> dict[str, faiss.IndexFlatL2 | faiss.IndexIDMap | Any]:
        try:
            self.pool[key] = index
            self.logger.info(f"Added index to pool for conversation ID {key}",
                Path(__file__).name, call_by=file_caller, method_call=self.add_to_pool.__name__)
            return {"status": "success", "message": f"Index added to pool for conversation ID {key}"}
        except Exception as e:
            self.logger.error(f"Failed to add index to pool for conversation ID {key}: {str(e)}", Path(__file__).name, call_by=file_caller, method_call=self.add_to_pool.__name__)
            return {"status": "error", "message": f"Failed to add index to pool for conversation ID {key}"}

    def get_from_pool(self, key: Any, file_caller: str = "") -> faiss.IndexFlatL2 | faiss.IndexIDMap | None:
        try:
            value = self.pool.get(key)
            if value is None:
                self.logger.warning(f"No index found in pool for conversation ID {key}", Path(__file__).name, call_by=file_caller, method_call=self.get_from_pool.__name__)
            else:
                self.logger.info(f"Retrieved index from pool for conversation ID {key}", Path(__file__).name, call_by=file_caller, method_call=self.get_from_pool.__name__)
            return value
        except Exception as e:
            self.logger.error(f"Failed to retrieve index from pool for conversation ID {key}: {str(e)}", Path(__file__).name, call_by=file_caller, method_call=self.get_from_pool.__name__)
            return None

    def remove_from_pool(self, key: Any, file_caller: str = "") -> bool:
        try:
            result = self.pool.pop(key, None)
            if result is not None:
                return True
            else:
                self.logger.warning(f"No index found in pool to remove for conversation ID {key}", Path(__file__).name, call_by=file_caller, method_call=self.remove_from_pool.__name__)
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove index from pool for conversation ID {key}: {str(e)}", Path(__file__).name, call_by=file_caller, method_call=self.remove_from_pool.__name__)
            return False

    def clear_pool(self, file_caller: str = "") -> int:
        try:
            count = len(self.pool)
            self.pool.clear()
            self.logger.info(f"Cleared pool, removed {count} indices",
                Path(__file__).name, call_by=file_caller, method_call=self.clear_pool.__name__)
            return count
        except Exception as e:
            self.logger.error(f"Failed to clear pool: {str(e)}", Path(__file__).name, call_by=file_caller, method_call=self.clear_pool.__name__)
            return 0