"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

Geely MADS模式实现 - 简化重构版
参考Honda、Hyundai等车型的实现

功能说明：
- MADS允许独立的横向控制激活/退出
- 支持基于ACC状态的自动激活
- 简洁的HUD反馈（白色/绿色/闪烁）
"""

from enum import StrEnum
from collections import namedtuple

from opendbc.car import DT_CTRL, structs
from opendbc.sunnypilot.mads_base import MadsCarStateBase
from opendbc.can.parser import CANParser


MadsDataSP = namedtuple("MadsDataSP", ["enable_mads", "lat_active", "disengaging", "paused"])


class MadsCarController:
  """Geely MADS控制器。"""

  def __init__(self):
    super().__init__()
    self.mads = MadsDataSP(False, False, False, False)
    self.lat_disengage_blink = 0
    self.lat_disengage_init = False
    self.prev_lat_active = False
    self.lkas_icon = 0

  def mads_status_update(self, CC: structs.CarControl, CC_SP: structs.CarControlSP, frame: int) -> MadsDataSP:
    enable_mads = CC_SP.mads.available
    if CC.latActive:
      self.lat_disengage_init = False
    elif self.prev_lat_active:
      self.lat_disengage_init = True

    if not self.lat_disengage_init:
      self.lat_disengage_blink = frame

    paused = CC_SP.mads.enabled and not CC.latActive
    disengaging = (frame - self.lat_disengage_blink) * DT_CTRL < 1.0 if self.lat_disengage_init else False
    self.prev_lat_active = CC.latActive
    return MadsDataSP(enable_mads, CC.latActive, disengaging, paused)

  def create_lkas_icon(self, enabled: bool) -> int:
    if self.mads.enable_mads:
      return 2 if self.mads.lat_active else 3 if self.mads.disengaging else 1
    return 2 if enabled else 1

  def update(self, CP: structs.CarParams, CC: structs.CarControl, CC_SP: structs.CarControlSP, frame: int) -> None:
    self.mads = self.mads_status_update(CC, CC_SP, frame)
    self.lkas_icon = self.create_lkas_icon(CC.enabled)


class MadsCarState(MadsCarStateBase):
  """Geely MADS状态扩展。"""

  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    super().__init__(CP, CP_SP)
    self.main_cruise_enabled: bool = False

  @staticmethod
  def get_parser(CP, CP_SP, pt_messages) -> None:
    # 吉利没有额外的 MADS CAN 信号。
    pass

  def get_main_cruise(self, ret: structs.CarState) -> bool:
    self.main_cruise_enabled = ret.cruiseState.available
    return self.main_cruise_enabled

  def update_mads(self, ret: structs.CarState, can_parsers: dict[StrEnum, CANParser]) -> None:
    # 吉利的 MADS 激活由 Safety 层处理。
    pass
