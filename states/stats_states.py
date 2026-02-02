"""
FSM states for statistics selection
"""
from aiogram.fsm.state import State, StatesGroup


class StatsStates(StatesGroup):
    """FSM states for statistics"""
    select_stats_type = State()
    select_time_range = State()
