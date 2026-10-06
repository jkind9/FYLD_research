"""Public camera-tracking validation; predictions and references stay separate."""

from ..evaluation import evaluate, read_references

__all__ = ["evaluate", "read_references"]
