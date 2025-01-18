from aiogram.fsm.state import StatesGroup, State

class GoogleMeetStates(StatesGroup):
    name = State()
    date = State()
    time = State()
    guests = State()
    confirm = State()
    add_guest_name = State()
    add_guest_email = State()