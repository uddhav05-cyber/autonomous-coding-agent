"""
Duplicate Prevention for Autonomous Coding Agent.

This module provides duplicate detection and prevention mechanisms to ensure
that the LLM context does not contain redundant or duplicate information,
preserving precious token capacity for novel content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import hashlib
import time


@dataclass
class DuplicatePolicy:
    """Policy for handling duplicate context."""
    # Enable or disable duplicate prevention
    enabled: bool = True

    # Similarity threshold for detecting duplicates (0.0 to 1.0)
    similarity_threshold: float = 0.85

    # Whether to use exact hash matching or similarity-based detection
    use_exact_matching: bool = True

    # Whether to remove duplicates or just flag them
    removal_enabled: bool = True

    # Whether to preserve the first occurrence or the most relevant
    preserve_first: bool = True

    # Maximum number of duplicates to track in memory
    max_tracked_items: int = 10000

    # Time-to-live for tracked items in seconds
    item_ttl_seconds: int = 3600  # 1 hour

    # Whether to consider context-aware duplicates (same meaning, different form)
    enable_semantic_detection: bool = False

    def __hash__(self) -> int:
        """Generate a hash for caching purposes."""
        return hash((
            self.enabled,
            self.similarity_threshold,
            self.use_exact_matching,
            self.removal_enabled,
            self.preserve_first,
            self.max_tracked_items,
            self.item_ttl_seconds,
            self.enable_semantic_detection
        ))


class DuplicatePreventer:
    """
    Duplicate Preventer that detects and removes duplicate context to
    preserve token capacity for novel information.

    This class provides:
    - Exact duplicate detection using content hashing
    - Similarity-based duplicate detection (optional)
    - Seen-content tracking to prevent reprocessing
    - Duplicate removal and suppression
    - Metrics on duplicate prevention effectiveness
    """

    def __init__(self):
        """Initialize the Duplicate Preventer."""
        # Track seen content by hash to prevent reprocessing
        self._seen_content: Dict[str, float] = {}  # hash -> timestamp

        # Track content that has been provided in context to prevent duplicates
        self._provided_content: Dict[str, float] = {}  # hash -> timestamp

        # For similarity-based detection (more expensive)
        self._content_vectors: Dict[str, Any] = {}  # hash -> vector representation

        # Maximum number of items to track before cleaning up old entries
        self.max_tracked_items: int = 10000

        # Statistics
        self._stats = {
            "total_items_checked": 0,
            "duplicates_detected": 0,
            "duplicates_removed": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def remove_duplicates(
        self,
        context: Dict[str, Any],
        policy: Optional[DuplicatePolicy] = None
    ) -> Dict[str, Any]:
        """
        Remove duplicate content from the context.

        Args:
            context: Context dictionary potentially containing duplicates
            policy: Duplicate policy to use (uses default if None)

        Returns:
            Context with duplicates removed
        """
        if policy is None:
            policy = DuplicatePolicy()

        if not policy.enabled:
            return context

        start_time = time.time()

        # Make a copy to avoid modifying the original
        result = self._deep_copy_context(context)

        # Track duplicates found
        duplicates_found = []

        # Process different context types
        for context_type in ["repository_context", "working_context", "task_context", "history_context"]:
            if context_type in result:
                result[context_type], type_duplicates = self._remove_duplicates_from_type(
                    result[context_type], context_type, policy
                )
                duplicates_found.extend(type_duplicates)

        # Update statistics
        self._stats["total_items_checked"] += 1
        self._stats["duplicates_detected"] += len(duplicates_found)
        if policy.removal_enabled:
            self._stats["duplicates_removed"] += len(duplicates_found)

        # Clean up old entries to prevent memory growth
        self._cleanup_old_entries(policy)

        return result

    def _remove_duplicates_from_type(
        self,
        context_data: Any,
        context_type: str,
        policy: DuplicatePolicy
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Remove duplicates from a specific type of context data.

        Args:
            context_data: Context data of a specific type
            context_type: Type of context data (for tracking)
            policy: Duplicate policy to use

        Returns:
            Tuple of (cleaned_data, list_of_duplicates_found)
        """
        duplicates_found = []

        if isinstance(context_data, dict):
            cleaned_dict, dict_duplicates = self._remove_duplicates_from_dict(
                context_data, context_type, policy
            )
            duplicates_found.extend(dict_duplicates)
            return cleaned_dict, duplicates_found

        elif isinstance(context_data, list):
            cleaned_list, list_duplicates = self._remove_duplicates_from_list(
                context_data, context_type, policy
            )
            duplicates_found.extend(list_duplicates)
            return cleaned_list, duplicates_found

        else:
            # For primitive types, check if we've seen this exact value before
            cleaned_data, item_duplicate = self._remove_duplicates_from_item(
                context_data, f"{context_type}_value", policy
            )
            if item_duplicate:
                duplicates_found.append(item_duplicate)
            return cleaned_data, duplicates_found

    def _remove_duplicates_from_dict(
        self,
        data: Dict[str, Any],
        context_type: str,
        policy: DuplicatePolicy
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Remove duplicates from a dictionary.

        Args:
            data: Dictionary to process
            context_type: Type of context data
            policy: Duplicate policy to use

        Returns:
            Tuple of (cleaned_dict, list_of_duplicates_found)
        """
        duplicates_found = []
        cleaned_dict = {}

        for key, value in data.items():
            # Process the key (usually safe, but check anyway)
            clean_key, key_duplicate = self._remove_duplicates_from_item(
                key, f"{context_type}.key.{key}", policy
            )
            if key_duplicate:
                duplicates_found.append(key_duplicate)

            # Process the value recursively
            clean_value, value_duplicates = self._remove_duplicates_from_item(
                value, f"{context_type}.{key}", policy
            )
            duplicates_found.extend(value_duplicates)

            # Only add if not a duplicate (or if we're keeping duplicates)
            if not (policy.removal_enabled and key_duplicate) and not (policy.removal_enabled and value_duplicates):
                cleaned_dict[clean_key] = clean_value

        return cleaned_dict, duplicates_found

    def _remove_duplicates_from_list(
        self,
        data: List[Any],
        context_type: str,
        policy: DuplicatePolicy
    ) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """
        Remove duplicates from a list.

        Args:
            data: List to process
            context_type: Type of context data
            policy: Duplicate policy to use

        Returns:
            Tuple of (cleaned_list, list_of_duplicates_found)
        """
        duplicates_found = []
        cleaned_list = []

        for index, item in enumerate(data):
            # Process each item
            clean_item, item_duplicates = self._remove_duplicates_from_item(
                item, f"{context_type}[{index}]", policy
            )
            duplicates_found.extend(item_duplicates)

            # Only add if not a duplicate (or if we're keeping duplicates)
            if not (policy.removal_enabled and item_duplicates):
                cleaned_list.append(clean_item)

        return cleaned_list, duplicates_found

    def _remove_duplicates_from_item(
        self,
        item: Any,
        item_id: str,
        policy: DuplicatePolicy
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Remove duplicates from a single item.

        Args:
            item: Item to check for duplicates
            item_id: Identifier for the item (for tracking)
            policy: Duplicate policy to use

        Returns:
            Tuple of (cleaned_item, list_of_duplicates_found)
        """
        duplicates_found = []

        # Convert item to a string representation for hashing
        try:
            item_str = str(item)
            item_hash = hashlib.sha256(item_str.encode('utf-8')).hexdigest()
        except Exception:
            # If we can't hash the item, treat it as unique
            return item, []

        current_time = time.time()

        # Check if we've seen this exact content before in provided context
        if item_hash in self._provided_content:
            # This is a duplicate
            last_seen = self._provided_content[item_hash]
            age_seconds = current_time - last_seen

            # Check if the item has expired (optional TTL)
            if age_seconds < policy.item_ttl_seconds:
                duplicates_found.append({
                    "item_id": item_id,
                    "hash": item_hash,
                    "original_timestamp": last_seen,
                    "current_timestamp": current_time,
                    "age_seconds": age_seconds,
                    "duplicate_type": "exact_match",
                    "content_preview": str(item)[:100] + ("..." if len(str(item)) > 100 else "")
                })

                # Return a marker indicating this was a duplicate
                # In practice, we might return None or a special duplicate marker
                # For now, we'll return the item but the caller knows it's a duplicate
                # The actual removal happens at the list/dict level
                return item, duplicates_found

        # If we get here, it's not a duplicate (or expired)
        # Mark it as seen if duplicate prevention is enabled
        if policy.enabled:
            self._provided_content[item_hash] = current_time
            self._stats["cache_misses"] += 1
        else:
            self._stats["cache_hits"] += 1

        return item, duplicates_found

    def _deep_copy_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a deep copy of the context dictionary.

        Args:
            context: Context dictionary to copy

        Returns:
            Deep copy of the context dictionary
        """
        import copy
        return copy.deepcopy(context)

    def _cleanup_old_entries(self, policy: DuplicatePolicy) -> None:
        """
        Remove old entries from tracking dictionaries to prevent memory growth.
        """
        current_time = time.time()
        cutoff_time = current_time - policy.item_ttl_seconds

        # Clean up seen_content
        keys_to_delete = [
            key for key, timestamp in self._seen_content.items()
            if timestamp < cutoff_time
        ]
        for key in keys_to_delete:
            del self._seen_content[key]

        # Clean up provided_content
        keys_to_delete = [
            key for key, timestamp in self._provided_content.items()
            if timestamp < cutoff_time
        ]
        for key in keys_to_delete:
            del self._provided_content[key]

        # Enforce maximum tracked items
        if len(self._provided_content) > self.max_tracked_items:
            # Remove oldest entries
            sorted_items = sorted(
                self._provided_content.items(),
                key=lambda x: x[1]  # Sort by timestamp
            )
            # Keep only the most recent items
            items_to_keep = sorted_items[-self.max_tracked_items:]
            self._provided_content = dict(items_to_keep)

        if len(self._seen_content) > self.max_tracked_items:
            # Remove oldest entries
            sorted_items = sorted(
                self._seen_content.items(),
                key=lambda x: x[1]  # Sort by timestamp
            )
            # Keep only the most recent items
            items_to_keep = sorted_items[-self.max_tracked_items:]
            self._seen_content = dict(items_to_keep)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get duplicate prevention statistics.

        Returns:
            Dictionary containing duplicate prevention statistics
        """
        total_checked = self._stats["total_items_checked"]
        if total_checked > 0:
            duplicate_rate = self._stats["duplicates_detected"] / total_checked
        else:
            duplicate_rate = 0.0

        return {
            "total_items_checked": self._stats["total_items_checked"],
            "duplicates_detected": self._stats["duplicates_detected"],
            "duplicates_removed": self._stats["duplicates_removed"],
            "duplicate_rate": round(self._stats["duplicates_detected"] / max(total_checked, 1), 4),
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "currently_tracking": len(self._provided_content),
            "efficiency": "high" if duplicate_rate < 0.05 else "medium" if duplicate_rate < 0.2 else "low"
        }

    def reset(self) -> None:
        """Reset all statistics and tracking data."""
        self._seen_content.clear()
        self._provided_content.clear()
        self._content_vectors.clear()
        self._stats = {
            "total_items_checked": 0,
            "duplicates_detected": 0,
            "duplicates_removed": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def __repr__(self) -> str:
        return f"DuplicatePreventer(enabled={len(self._provided_content)} items tracked)"