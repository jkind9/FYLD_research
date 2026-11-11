"""Compatibility imports for session readers and the capture receiver."""

from functools import partial
from importlib import import_module

from sitescan.session import read_wire_session as read_session
from sitescan.session.replay import replay as _replay

session_v1 = import_module("experiments.01_camera_capture_delivery.host.session_v1")
session_v2 = import_module("experiments.01_camera_capture_delivery.host.session_v2")
capture_receiver = import_module("experiments.01_camera_capture_delivery.host.capture_receiver")
replay = partial(_replay, reader=read_session)

__all__ = ["capture_receiver", "read_session", "replay", "session_v1", "session_v2"]
