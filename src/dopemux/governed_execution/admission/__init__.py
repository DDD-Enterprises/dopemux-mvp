"""Owner-local first-wave admission ports; portable projections grant no authority."""

from .identity import AdmissionError, ExpectedScope
from .owner_admission import OwnerAdmitter

__all__ = ["AdmissionError", "ExpectedScope", "OwnerAdmitter"]
