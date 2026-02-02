"""
FSM states for category management
"""
from aiogram.fsm.state import State, StatesGroup


class EditCategoryStates(StatesGroup):
    """FSM states for editing category"""
    waiting_category_selection = State()
    waiting_new_name = State()


class DeleteCategoryStates(StatesGroup):
    """FSM states for deleting category"""
    waiting_category_selection = State()
    waiting_confirmation = State()
