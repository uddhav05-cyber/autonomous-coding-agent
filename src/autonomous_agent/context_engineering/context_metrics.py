"""
Context Metrics for Autonomous Coding Agent.

This module provides context metrics collection and reporting to monitor
the effectiveness of context selection, budgeting, and assembly processes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import time
import threading
from collections import defaultdict, deque

from .context_assembler import AssemblyResult


@dataclass
class MetricsReport:
    """Report of context metrics."""
    # Timestamp of the report
    timestamp: float = field(default_factory=time.time)

    # Context creation metrics
    total_contexts_created: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0

    # Token usage metrics
    total_tokens_used: int = 0
    average_tokens_per_context: float = 0.0
    token_usage_by_type: Dict[str, int] = field(default_factory=dict)

    # Selection metrics
    contexts_selected: int = 0
    average_selection_time_ms: float = 0.0
    relevance_scores: List[float] = field(default_factory=list)
    average_relevance_score: float = 0.0

    # Assembly metrics
    contexts_assembled: int = 0
    average_assembly_time_ms: float = 0.0
    average_completeness_score: float = 0.0
    average_relevance_score_assembled: float = 0.0
    average_diversity_score: float = 0.0

    # Duplicate prevention metrics
    duplicates_detected: int = 0
    duplicates_removed: int = 0
    duplicate_rate: float = 0.0
    tokens_saved_by_deduplication: int = 0

    # Budget adherence metrics
    budget_exceeded_count: int = 0
    average_budget_utilization: float = 0.0
    budget_violation_severity: Dict[str, int] = field(default_factory=dict)

    # Performance metrics
    average_total_processing_time_ms: float = 0.0
    context_creation_rate_per_second: float = 0.0

    # Quality metrics
    context_quality_score: float = 0.0
    user_satisfaction_estimate: float = 0.0  # Would be inferred from usage patterns

    def is_healthy(self) -> bool:
        """Check if metrics indicate healthy context engineering performance."""
        # Healthy if:
        # - Cache hit rate is reasonable (>0.1 or we have enough data)
        # - Budget is not exceeded too often (<0.1 violation rate)
        # - Average relevance is decent (>0.3)
        # - Duplicate rate is not excessive (<0.5)

        cache_healthy = self.cache_hit_rate >= 0.1 or self.total_contexts_created < 10
        budget_healthy = (self.budget_exceeded_count / max(self.total_contexts_created, 1)) < 0.1
        relevance_healthy = self.average_relevance_score >= 0.3
        duplicate_healthy = self.duplicate_rate < 0.5

        return cache_healthy and budget_healthy and relevance_healthy and duplicate_healthy

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the metrics report."""
        return {
            "timestamp": self.timestamp,
            "total_contexts_created": self.total_contexts_created,
            "cache_hit_rate": round(self.cache_hit_rate, 3),
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_context": round(self.average_tokens_per_context, 1),
            "budget_exceeded_count": self.budget_exceeded_count,
            "average_relevance_score": round(self.average_relevance_score, 3),
            "duplicate_rate": round(self.duplicate_rate, 3),
            "is_healthy": self.is_healthy()
        }


class ContextMetrics:
    """
    Context Metrics collector that tracks and reports on the effectiveness
    of context selection, budgeting, assembly, and duplicate prevention.

    This class provides:
    - Token usage tracking and budget adherence monitoring
    - Context selection and assembly performance metrics
    - Duplicate prevention effectiveness tracking
    - Context quality and completeness scoring
    - Performance trend analysis
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize the Context Metrics collector.

        Args:
            max_history: Maximum number of historical records to keep
        """
        self.max_history = max_history
        self._lock = threading.Lock()  # Thread-safe operations

        # Initialize metrics counters
        self.reset()

        # For rate calculations
        self._start_time = time.time()
        self._last_report_time = time.time()

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self._metrics = {
                # Context creation metrics
                "total_contexts_created": 0,
                "cache_hits": 0,
                "cache_misses": 0,

                # Token usage metrics
                "total_tokens_used": 0,
                "token_type_usage": defaultdict(int),
                "context_token_usage": [],  # List of (timestamp, tokens) tuples

                # Selection metrics
                "contexts_selected": 0,
                "selection_times": [],  # List of (timestamp, time_ms) tuples
                "relevance_scores_collected": [],  # List of (timestamp, score) tuples

                # Assembly metrics
                "contexts_assembled": 0,
                "assembly_times": [],  # List of (timestamp, time_ms) tuples
                "completeness_scores": [],  # List of (timestamp, score) tuples
                "relevance_scores_assembled": [],  # List of (timestamp, score) tuples
                "diversity_scores": [],  # List of (timestamp, score) tuples

                # Duplicate prevention metrics
                "duplicates_detected": 0,
                "duplicates_removed": 0,
                "tokens_saved_by_deduplication": 0,

                # Budget adherence metrics
                "budget_exceeded_count": 0,
                "budget_utilization": [],  # List of (timestamp, utilization%) tuples
                "budget_violations": [],  # List of (timestamp, severity, details) tuples

                # Quality metrics
                "context_quality_scores": [],  # List of (timestamp, score) tuples
            }

    def record_context_creation(
        self,
        context_package: 'ContextPackage',
        processing_time_ms: float
    ) -> None:
        """
        Record metrics for context creation.

        Args:
            context_package: The context package that was created
            processing_time_ms: Time taken to create the context in milliseconds
        """
        with self._lock:
            # Increment context creation counter
            self._metrics["total_contexts_created"] += 1

            # Record token usage
            tokens_used = context_package.total_tokens
            self._metrics["total_tokens_used"] += tokens_used
            self._metrics["token_type_usage"]["total"] += tokens_used

            # Record by context type if available
            if hasattr(context_package, 'token_breakdown'):
                for context_type, tokens in context_package.token_breakdown.items():
                    self._metrics["token_type_usage"][context_type] += tokens

            # Record timing
            self._metrics["context_token_usage"].append((time.time(), tokens_used))

            # Update averages
            self._update_token_averages()

            # Record overall processing time (would be more detailed in practice)
            # For now, we'll just note that creation happened

            # Enforce history limits
            self._enforce_history_limits()

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._metrics["cache_hits"] += 1
            self._update_cache_rates()

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._metrics["cache_misses"] += 1
            self._update_cache_rates()

    def record_context_selection(
        self,
        selection_time_ms: float,
        relevance_score: Optional[float] = None
    ) -> None:
        """
        Record metrics for context selection.

        Args:
            selection_time_ms: Time taken for selection in milliseconds
            relevance_score: Average relevance score of selected items
        """
        with self._lock:
            self._metrics["contexts_selected"] += 1
            self._metrics["selection_times"].append((time.time(), selection_time_ms))

            if relevance_score is not None:
                self._metrics["relevance_scores_collected"].append((time.time(), relevance_score))

            self._update_selection_averages()
            self._enforce_history_limits()

    def record_context_assembly(
        self,
        assembly_result: AssemblyResult,
        assembly_time_ms: float
    ) -> None:
        """
        Record metrics for context assembly.

        Args:
            assembly_result: The assembly result
            assembly_time_ms: Time taken for assembly in milliseconds
        """
        with self._lock:
            self._metrics["contexts_assembled"] += 1
            self._metrics["assembly_times"].append((time.time(), assembly_time_ms))
            self._metrics["completeness_scores"].append((time.time(), assembly_result.completeness_score))
            self._metrics["relevance_scores_assembled"].append((time.time(), assembly_result.relevance_score))
            self._metrics["diversity_scores"].append((time.time(), assembly_result.diversity_score))

            self._update_assembly_averages()
            self._enforce_history_limits()

    def record_duplicate_detection(
        self,
        duplicates_detected: int,
        duplicates_removed: int,
        tokens_saved: int = 0
    ) -> None:
        """
        Record metrics for duplicate detection and removal.

        Args:
            duplicates_detected: Number of duplicates detected
            duplicates_removed: Number of duplicates actually removed
            tokens_saved: Estimated tokens saved by removing duplicates
        """
        with self._lock:
            self._metrics["duplicates_detected"] += duplicates_detected
            self._metrics["duplicates_removed"] += duplicates_removed
            self._metrics["tokens_saved_by_deduplication"] += tokens_saved

            self._update_duplicate_rates()

    def record_budget_violation(
        self,
        tokens_used: int,
        max_tokens: int,
        context_type: Optional[str] = None
    ) -> None:
        """
        Record a budget violation.

        Args:
            tokens_used: Number of tokens used
            max_tokens: Maximum allowed tokens
            context_type: Type of context that caused the violation (if known)
        """
        with self._lock:
            self._metrics["budget_exceeded_count"] += 1

            utilization = tokens_used / max_tokens if max_tokens > 0 else 0
            self._metrics["budget_utilization"].append((time.time(), utilization * 100))

            # Record violation details
            severity = "low" if utilization < 1.1 else "medium" if utilization < 1.5 else "high"
            self._metrics["budget_violations"].append({
                "timestamp": time.time(),
                "severity": severity,
                "tokens_used": tokens_used,
                "max_tokens": max_tokens,
                "excess_tokens": tokens_used - max_tokens,
                "context_type": context_type,
                "utilization_percent": utilization * 100
            })

            self._update_budget_averages()

    def record_context_quality(
        self,
        quality_score: float
    ) -> None:
        """
        Record a context quality score.

        Args:
            quality_score: Quality score between 0.0 and 1.0
        """
        with self._lock:
            self._metrics["context_quality_scores"].append((time.time(), quality_score))
            self._update_quality_averages()
            self._enforce_history_limits()

    def get_report(self) -> MetricsReport:
        """
        Get a comprehensive metrics report.

        Returns:
            MetricsReport containing all collected metrics
        """
        with self._lock:
            # Calculate derived metrics
            total_contexts = self._metrics["total_contexts_created"]

            # Cache hit rate
            total_cache_requests = self._metrics["cache_hits"] + self._metrics["cache_misses"]
            cache_hit_rate = (
                self._metrics["cache_hits"] / max(total_cache_requests, 1)
                if total_cache_requests > 0 else 0.0
            )

            # Average tokens per context
            avg_tokens_per_context = (
                self._metrics["total_tokens_used"] / max(total_contexts, 1)
                if total_contexts > 0 else 0.0
            )

            # Token usage by type
            token_usage_by_type = dict(self._metrics["token_type_usage"])

            # Selection metrics
            contexts_selected = self._metrics["contexts_selected"]
            avg_selection_time = 0.0
            if self._metrics["selection_times"]:
                avg_selection_time = sum(t for _, t in self._metrics["selection_times"]) / len(self._metrics["selection_times"])

            avg_relevance_score = 0.0
            if self._metrics["relevance_scores_collected"]:
                avg_relevance_score = sum(s for _, s in self._metrics["relevance_scores_collected"]) / len(self._metrics["relevance_scores_collected"])

            # Assembly metrics
            contexts_assembled = self._metrics["contexts_assembled"]
            avg_assembly_time = 0.0
            if self._metrics["assembly_times"]:
                avg_assembly_time = sum(t for _, t in self._metrics["assembly_times"]) / len(self._metrics["assembly_times"])

            avg_completeness = 0.0
            if self._metrics["completeness_scores"]:
                avg_completeness = sum(s for _, s in self._metrics["completeness_scores"]) / len(self._metrics["completeness_scores"])

            avg_relevance_assembled = 0.0
            if self._metrics["relevance_scores_assembled"]:
                avg_relevance_assembled = sum(s for _, s in self._metrics["relevance_scores_assembled"]) / len(self._metrics["relevance_scores_assembled"])

            avg_diversity = 0.0
            if self._metrics["diversity_scores"]:
                avg_diversity = sum(s for _, s in self._metrics["diversity_scores"]) / len(self._metrics["diversity_scores"])

            # Duplicate prevention metrics
            duplicates_detected = self._metrics["duplicates_detected"]
            duplicates_removed = self._metrics["duplicates_removed"]
            duplicate_rate = (
                self._metrics["duplicates_detected"] / max(self._metrics["total_items_checked"], 1)
                if hasattr(self, '_metrics') and 'total_items_checked' in self._metrics else 0.0
            )
            # Note: We don't have total_items_checked in this metrics system - would need to track it elsewhere

            # Budget adherence
            budget_exceeded_count = self._metrics["budget_exceeded_count"]
            avg_budget_utilization = 0.0
            if self._metrics["budget_utilization"]:
                avg_budget_utilization = sum(u for _, u in self._metrics["budget_utilization"]) / len(self._metrics["budget_utilization"])

            # Quality metrics
            avg_quality_score = 0.0
            if self._metrics["context_quality_scores"]:
                avg_quality_score = sum(s for _, s in self._metrics["context_quality_scores"]) / len(self._metrics["context_quality_scores"])

            # Processing rate
            elapsed_time = time.time() - self._start_time
            context_creation_rate = (
                total_contexts / elapsed_time
                if elapsed_time > 0 else 0.0
            )

            return MetricsReport(
                timestamp=time.time(),
                total_contexts_created=total_contexts,
                cache_hits=self._metrics["cache_hits"],
                cache_misses=self._metrics["cache_misses"],
                cache_hit_rate=cache_hit_rate,
                total_tokens_used=self._metrics["total_tokens_used"],
                average_tokens_per_context=avg_tokens_per_context,
                token_usage_by_type=token_usage_by_type,
                contexts_selected=contexts_selected,
                average_selection_time_ms=avg_selection_time,
                relevance_scores=[s for _, s in self._metrics["relevance_scores_collected"]],
                average_relevance_score=avg_relevance_score,
                contexts_assembled=contexts_assembled,
                average_assembly_time_ms=avg_assembly_time,
                average_completeness_score=avg_completeness,
                average_relevance_score_assembled=avg_relevance_assembled,
                average_diversity_score=avg_diversity,
                duplicates_detected=duplicates_detected,
                duplicates_removed=duplicates_removed,
                duplicate_rate=duplicate_rate,
                budget_exceeded_count=budget_exceeded_count,
                average_budget_utilization=avg_budget_utilization,
                budget_violation_severity={},  # Would populate from violation history
                average_total_processing_time_ms=0.0,  # Would need to track end-to-end time
                context_creation_rate_per_second=context_creation_rate,
                context_quality_score=avg_quality_score,
                user_satisfaction_estimate=0.0  # Would need feedback mechanism
            )

    def _update_cache_rates(self) -> None:
        """Update cache hit/miss rates."""
        # This is called whenever hits or misses are recorded
        # The actual calculation happens in get_report()
        pass

    def _update_token_averages(self) -> None:
        """Update token usage averages."""
        # This is called whenever token usage is recorded
        # The actual calculation happens in get_report()
        pass

    def _update_selection_averages(self) -> None:
        """Update selection time and relevance averages."""
        # This is called whenever selection metrics are recorded
        # The actual calculation happens in get_report()
        pass

    def _update_assembly_averages(self) -> None:
        """Update assembly metric averages."""
        # This is called whenever assembly metrics are recorded
        # The actual calculation happens in get_report()
        pass

    def _update_duplicate_rates(self) -> None:
        # This is called whenever duplicate metrics are recorded
        # The actual calculation happens in get_report()
        pass

    def _update_budget_averages(self) -> None:
        """Update budget utilization averages."""
        # This is called whenever budget metrics are recorded
        # The actual calculation happens in get_report()
        pass

    def _update_quality_averages(self) -> None:
        """Update quality score averages."""
        # This is called whenever quality metrics are recorded
        # The actual calculation happens in get_report()
        pass

    def _enforce_history_limits(self) -> None:
        """
        Enforce maximum history limits to prevent memory growth.

        This method ensures that we don't store unlimited historical data.
        """
        # For each metrics list, keep only the most recent entries
        history_lists = [
            "context_token_usage",
            "selection_times",
            "relevance_scores_collected",
            "assembly_times",
            "completeness_scores",
            "relevance_scores_assembled",
            "diversity_scores",
            "budget_utilization",
            "budget_violations",
            "context_quality_scores"
        ]

        for list_name in history_lists:
            if list_name in self._metrics and isinstance(self._metrics[list_name], list):
                if len(self._metrics[list_name]) > self.max_history:
                    # Keep only the most recent entries
                    self._metrics[list_name] = self._metrics[list_name][-self.max_history:]

    def __repr__(self) -> str:
        return f"ContextMetrics(contexts_created={self._metrics['total_contexts_created']})"