"""
Context Budgeting for Autonomous Coding Agent.

This module provides token budgeting and allocation mechanisms to ensure
that the LLM context stays within specified token limits while maximizing
relevance and utility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import heapq
import math


@dataclass
class BudgetAllocation:
    """Token budget allocation across different context types."""
    # Fixed token allocations for specific context types
    fixed_allocations: Dict[str, Any] = field(default_factory=dict)

    # Proportional allocations based on weights
    proportional_allocations: Dict[str, Any] = field(default_factory=dict)

    # Minimum and maximum token limits for each type
    min_allocations: Dict[str, int] = field(default_factory=dict)
    max_allocations: Dict[str, int] = field(default_factory=dict)

    # Whether to enable dynamic reallocation based on usage
    enable_dynamic_reallocation: bool = True

    # Phase-aware budgeting adjustments
    planning_budget_multiplier: float = 1.0
    execution_budget_multiplier: float = 1.0
    verification_budget_multiplier: float = 1.0

    # Reserve tokens for unexpected needs
    reserve_percentage: float = 0.1  # 10% reserve by default

    def __hash__(self) -> int:
        """Generate a hash for caching purposes."""
        return hash((
            tuple(sorted(self.fixed_allocations.items())),
            tuple(sorted(self.proportional_allocations.items())),
            tuple(sorted(self.min_allocations.items())),
            tuple(sorted(self.max_allocations.items())),
            self.enable_dynamic_reallocation,
            self.planning_budget_multiplier,
            self.execution_budget_multiplier,
            self.verification_budget_multiplier,
            self.reserve_percentage
        ))


class ContextBudgeter:
    """
    Context Budgeter that manages token allocation across different
    context types to ensure the LLM context stays within specified limits.

    This class provides:
    - Token-based budgeting with fixed and proportional allocations
    - Dynamic budget reallocation based on context usefulness
    - Phase-aware budgeting (different allocations for planning/execution/verification)
    - Graceful degradation when budget is exceeded
    - Reserve tokens for unexpected needs
    """

    def __init__(self):
        """Initialize the Context Budgeter."""
        # Default budget allocation if none provided
        self.default_allocation = BudgetAllocation(
            fixed_allocations={
                "repository_context": 800,   # ~20% for basic repo info
                "task_context": 200,         # ~5% for task description
                "history_context": 300       # ~7.5% for recent history
            },
            proportional_allocations={
                "working_context": 1.0       # Remaining 57.5% for working files/snippets
            },
            min_allocations={
                "repository_context": 200,
                "task_context": 50,
                "history_context": 100,
                "working_context": 100
            },
            max_allocations={
                "working_context": 2000      # Cap working context at 2000 tokens
            },
            reserve_percentage=0.1
        )

    def apply_budget(
        self,
        assembled_context: Dict[str, Any],
        budget_allocation: Optional[BudgetAllocation] = None,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Apply token budgeting to assembled context.

        Args:
            assembled_context: Context assembled from various sources
            budget_allocation: Specific budget allocation to use (uses default if None)
            max_tokens: Maximum total tokens allowed

        Returns:
            Budgeted context that fits within token limits
        """
        if budget_allocation is None:
            budget_allocation = self.default_allocation

        # Apply phase-aware adjustments if we know the current phase
        # For now, we'll use the allocation as-is - in practice, this would
        # be adjusted based on the agent's current task phase

        # Calculate token reserves
        reserve_tokens = int(max_tokens * budget_allocation.reserve_percentage)
        available_tokens = max_tokens - reserve_tokens

        # Apply allocations to determine token limits for each context type
        token_limits = self._calculate_token_limits(
            assembled_context, budget_allocation, available_tokens
        )

        # Apply the token limits to truncate or summarize content
        budgeted_context = self._apply_token_limits(
            assembled_context, token_limits
        )

        # Add budget metadata
        budgeted_context["_budget_info"] = {
            "max_tokens": max_tokens,
            "reserve_tokens": reserve_tokens,
            "available_tokens": available_tokens,
            "allocated_tokens": sum(token_limits.values()),
            "used_tokens": self._estimate_token_count(budgeted_context),
            "reserve_percentage": budget_allocation.reserve_percentage,
            "allocation_used": budget_allocation.__dict__
        }

        return budgeted_context

    def _calculate_token_limits(
        self,
        assembled_context: Dict[str, Any],
        budget_allocation: BudgetAllocation,
        available_tokens: int
    ) -> Dict[str, int]:
        """
        Calculate token limits for each context type based on allocation.

        Args:
            assembled_context: Context assembled from various sources
            budget_allocation: Budget allocation to apply
            available_tokens: Tokens available after reserve

        Returns:
            Dictionary mapping context types to their token limits
        """
        limits = {}

        # Start with minimum allocations
        for context_type, min_tokens in budget_allocation.min_allocations.items():
            limits[context_type] = min_tokens

        # Apply fixed allocations
        for context_type, allocation in budget_allocation.fixed_allocations.items():
            if hasattr(allocation, 'tokens'):
                fixed_tokens = allocation.tokens
            else:
                fixed_tokens = allocation  # Assume it's already a token value

            # Ensure we don't go below minimum
            limits[context_type] = max(
                limits.get(context_type, 0),
                fixed_tokens
            )

        # Calculate remaining tokens after fixed and minimum allocations
        allocated_so_far = sum(limits.values())
        remaining_tokens = max(0, available_tokens - allocated_so_far)

        # Apply proportional allocations
        total_weight = 0.0
        weighted_types = []

        for context_type, allocation in budget_allocation.proportional_allocations.items():
            if hasattr(allocation, 'weight'):
                weight = allocation.weight
            else:
                weight = float(allocation)  # Assume it's a numeric weight

            if weight > 0:
                total_weight += weight
                weighted_types.append(context_type)

        if total_weight > 0 and remaining_tokens > 0:
            # Distribute remaining tokens proportionally
            for context_type in weighted_types:
                if hasattr(budget_allocation.proportional_allocations[context_type], 'weight'):
                    weight = budget_allocation.proportional_allocations[context_type].weight
                else:
                    weight = float(budget_allocation.proportional_allocations[context_type])

                proportional_share = weight / total_weight
                proportional_tokens = int(remaining_tokens * proportional_share)

                # Add to existing limit (which includes minimum)
                limits[context_type] = limits.get(context_type, 0) + proportional_tokens

        # Apply maximum allocations
        for context_type, max_tokens in budget_allocation.max_allocations.items():
            if context_type in limits:
                limits[context_type] = min(limits[context_type], max_tokens)

        # Ensure we don't exceed available tokens
        total_allocated = sum(limits.values())
        if total_allocated > available_tokens:
            # Scale down proportionally if we're over budget
            scale_factor = available_tokens / total_allocated
            for context_type in limits:
                limits[context_type] = int(limits[context_type] * scale_factor)
                # But don't go below minimum
                min_tokens = budget_allocation.min_allocations.get(context_type, 0)
                limits[context_type] = max(limits[context_type], min_tokens)

        return limits

    def _apply_token_limits(
        self,
        assembled_context: Dict[str, Any],
        token_limits: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Apply token limits to assembled context by truncating or summarizing.

        Args:
            assembled_context: Context assembled from various sources
            token_limits: Token limits for each context type

        Returns:
            Context with content truncated to fit within token limits
        """
        budgeted_context = {}

        for context_type, context_content in assembled_context.items():
            if context_type in token_limits:
                max_tokens = token_limits[context_type]
                budgeted_context[context_type] = self._truncate_content_to_tokens(
                    context_content, max_tokens
                )
            else:
                # No specific allocation - apply a small default limit
                budgeted_context[context_type] = self._truncate_content_to_tokens(
                    context_content, 100  # Default small limit for unspecified types
                )

        return budgeted_context

    def _truncate_content_to_tokens(
        self,
        content: Any,
        max_tokens: int
    ) -> Any:
        """
        Truncate content to fit within the specified token limit.

        Args:
            content: Content to truncate (can be various types)
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated content that fits within token limit
        """
        # Simple token estimation: ~4 characters per token for English text
        # This is a rough approximation - in practice, we'd use a proper tokenizer
        chars_per_token = 4
        max_chars = max_tokens * chars_per_token

        if isinstance(content, str):
            if len(content) <= max_chars:
                return content
            else:
                # Truncate and add indicator
                truncated = content[:max_chars]
                # Try to break at a word boundary or line boundary
                last_newline = truncated.rfind('\n')
                last_space = truncated.rfind(' ')
                break_point = max(last_newline, last_space)

                if break_point > max_chars * 0.8:  # Only if we don't lose too much
                    truncated = truncated[:break_point]

                return truncated + "\n\n[...content truncated due to token limits...]"

        elif isinstance(content, list):
            if not content:
                return content

            # Estimate tokens per item (simplified)
            if len(content) <= 10:  # Small list
                # Estimate total tokens
                estimated_tokens = len(str(content)) // chars_per_token
                if estimated_tokens <= max_tokens:
                    return content
                else:
                    # Show fewer items
                    if len(content) > 0:
                        # Estimate based on average item size
                        avg_item_size = len(str(content[0])) if content else 100
                        avg_item_tokens = avg_item_size // chars_per_token
                        if avg_item_tokens > 0:
                            max_items = max(1, max_tokens // avg_item_tokens)
                            return content[:max_items]
                    return content[:max(1, max_tokens // 10)]  # Fallback
            else:
                # For larger lists, show first N items
                if len(content) > 0:
                    # Estimate based on first item
                    first_item_size = len(str(content[0]))
                    first_item_tokens = first_item_size // chars_per_token
                    if first_item_tokens > 0:
                        max_items = max(1, max_tokens // first_item_tokens)
                        return content[:max_items]
                return content[:max(1, max_tokens // 10)]  # Fallback

        elif isinstance(content, dict):
            if not content:
                return content

            # Estimate tokens per key-value pair
            if len(content) <= 10:  # Small dictionary
                estimated_tokens = len(str(content)) // chars_per_token
                if estimated_tokens <= max_tokens:
                    return content
                else:
                    # Show fewer items
                    if len(content) > 0:
                        # Estimate based on first item
                        first_item = list(content.items())[0]
                        first_item_size = len(str(first_item))
                        first_item_tokens = first_item_size // chars_per_token
                        if first_item_tokens > 0:
                            max_items = max(1, max_tokens // first_item_tokens)
                            items = list(content.items())[:max_items]
                            return dict(items)
                    return dict(list(content.items())[:max(1, max_tokens // 10)])
            else:
                # For larger dictionaries, show first N items
                if len(content) > 0:
                    # Estimate based on first item
                    first_item = list(content.items())[0]
                    first_item_size = len(str(first_item))
                    first_item_tokens = first_item_size // chars_per_token
                    if first_item_tokens > 0:
                        max_items = max(1, max_tokens // first_item_tokens)
                        items = list(content.items())[:max_items]
                        return dict(items)
                return dict(list(content.items())[:max(1, max_tokens // 10)])

        # For other types (int, float, bool, None), return as-is (assuming they're small)
        return content

    def _estimate_token_count(self, content: Any) -> int:
        """
        Estimate the token count of content.

        Args:
            content: Content to estimate token count for

        Returns:
            Estimated token count
        """
        # Simple token estimation: ~4 characters per token for English text
        chars_per_token = 4

        if isinstance(content, str):
            return len(content) // chars_per_token

        elif isinstance(content, list):
            if not content:
                return 0
            # Estimate based on string representation
            return len(str(content)) // chars_per_token

        elif isinstance(content, dict):
            if not content:
                return 0
            # Estimate based on string representation
            return len(str(content)) // chars_per_token

        else:
            # For other types, estimate based on string representation
            return len(str(content)) // chars_per_token

    def get_budget_recommendations(
        self,
        context_usage: Dict[str, int],
        total_tokens_used: int,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Get budget allocation recommendations based on actual usage.

        Args:
            context_usage: Token usage by context type
            total_tokens_used: Total tokens used
            max_tokens: Maximum allowed tokens

        Returns:
            Dictionary with budget recommendations
        """
        recommendations = {
            "current_utilization": total_tokens_used / max_tokens if max_tokens > 0 else 0,
            "is_over_budget": total_tokens_used > max_tokens,
            "suggested_adjustments": {},
            "warnings": []
        }

        if total_tokens_used > max_tokens:
            recommendations["warnings"].append(
                f"Context exceeded budget by {total_tokens_used - max_tokens} tokens"
            )

        # Suggest adjustments based on usage patterns
        for context_type, tokens_used in context_usage.items():
            if tokens_used == 0 and total_tokens_used > 0:
                # Type received no tokens but we used budget elsewhere
                recommendations["suggested_adjustments"][context_type] = {
                    "action": "consider_reducing_allocation",
                    "reason": "Received zero tokens despite budget being used"
                }
            elif context_usage:
                usage_percentage = tokens_used / sum(context_usage.values()) if sum(context_usage.values()) > 0 else 0
                if usage_percentage < 0.1 and total_tokens_used > max_tokens * 0.8:
                    # Low usage but we're over budget - could reduce allocation
                    recommendations["suggested_adjustments"][context_type] = {
                        "action": "consider_reducing_allocation",
                        "reason": f"Low usage ({usage_percentage:.1%}) while over budget"
                    }

        return recommendations

    def __repr__(self) -> str:
        return f"ContextBudgeter(default_allocation={self.default_allocation})"