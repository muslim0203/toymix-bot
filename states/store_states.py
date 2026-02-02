"""
FSM states for store location management
"""
from aiogram.fsm.state import State, StatesGroup


class AddStoreLocationStates(StatesGroup):
    """FSM states for adding a store location"""
    waiting_name = State()
    waiting_address = State()
    waiting_location = State()  # Changed: single state for location instead of separate latitude/longitude


class DeleteStoreLocationStates(StatesGroup):
    """FSM states for deleting a store location"""
    waiting_location_selection = State()
