"""Compatibility imports for adopted mapping and experimental chunk readers."""

from sitescan.mapping.footprint import MAX_GRID_CELLS  # noqa: F401
from sitescan.mapping.footprint import onto_plane as _onto_plane  # noqa: F401
from sitescan.mapping.footprint import signed_axes as _signed  # noqa: F401
from sitescan.mapping.types import Footprint, Plane  # noqa: F401

from .chunks import PointChunks, _as_chunks, _checked_chunk, _Scatter  # noqa: F401
from .streaming import fit_dominant_plane, footprint  # noqa: F401
