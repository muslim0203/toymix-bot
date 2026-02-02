"""
FSM states for bestseller management
"""
from aiogram.fsm.state import State, StatesGroup


class AddBestsellerStates(StatesGroup):
    """FSM states for adding manual bestseller"""
    waiting_period = State()
    waiting_category = State()
    waiting_rank = State()


class DeleteBestsellerStates(StatesGroup):
    """FSM states for deleting bestseller"""
    waiting_period = State()
    waiting_bestseller = State()
