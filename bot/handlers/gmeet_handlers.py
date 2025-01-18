from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from bot.states.gmeet_states import GoogleMeetStates
from bot.keyboards.gmeet_keyboard import delete_guest_keyboard, select_guests_keyboard
from bot.config.auth import authenticate
from bot.requests.gmeet_requests import add_guest, delete_guest, get_all_guests, schedule_google_meet, create_google_meet_link
import os

router = Router()
user_credentials = {}

@router.message(Command("gmeet_auth"))
async def generate_auth_link(message: Message):
    """Authenticate the user via local server."""
    chat_id = message.chat.id
    try:
        # Perform authentication
        credentials = authenticate()
        user_credentials[chat_id] = credentials.to_json()

        await message.reply("Authorization successful! Use /gmeet_link to create a Google Meet link.")
    except Exception as e:
        await message.reply(f"Error during authorization: {e}")


@router.message(Command("gmeet_link"))
async def create_meet(message: Message):
    """Create a Google Meet link and send it to the user."""
    chat_id = message.chat.id

    if chat_id not in user_credentials:
        await message.reply("You need to authorize first! Use /auth to begin.")
        return
    
    try:
        creds_json = user_credentials[chat_id]
        meet_link = create_google_meet_link(creds_json)

        await message.reply(f"Google Meet link created: {meet_link}\nShare it with your participants!")
    except Exception as e:
        await message.reply(f"Error creating Google Meet link: {e}")


@router.message(Command('group_id'))
async def get_group_id(message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    if chat_type in ["group", "supergroup"]:
        await message.reply(f"Group ID: {chat_id}")
    else:
        await message.reply(f"Personal Chat ID: {chat_id}")


#-___________-

@router.message(Command("gmeet_schedule_meeting"))
async def add_meeting_handler(message: Message, state: FSMContext):
    """Handler to start creating a new meeting."""
    chat_id = message.chat.id

    # Check if the user is authenticated
    if chat_id not in user_credentials:
        await message.reply("You need to authenticate first! Use /gmeet_auth to authorize.")
        return
    
    # Proceed to gather meeting details
    await state.set_state(GoogleMeetStates.name)
    await message.answer("Enter the meeting name:")

@router.message(GoogleMeetStates.name)
async def set_meeting_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(GoogleMeetStates.date)
    await message.answer("Enter the meeting date (YYYY-MM-DD):")

@router.message(GoogleMeetStates.date)
async def set_meeting_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(GoogleMeetStates.time)
    await message.answer("Enter the meeting time (HH:MM in 24-hour format):")

@router.message(GoogleMeetStates.time)
async def set_meeting_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    guests = await get_all_guests()
    selected_guests = []  # Initialize empty selection
    keyboard = await select_guests_keyboard(guests, selected_guests)
    await message.answer("Select guests for the meeting:", reply_markup=keyboard)
    await state.set_state(GoogleMeetStates.guests)

@router.callback_query(F.data.startswith("toggle_guest"))
async def toggle_guest_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle guest selection and update the inline keyboard."""
    guest_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected_guests = data.get("selected_guests", [])
    
    # Toggle the selection
    if guest_id in selected_guests:
        selected_guests.remove(guest_id)
    else:
        selected_guests.append(guest_id)
    
    await state.update_data(selected_guests=selected_guests)

    # Update the keyboard with the toggled state
    guests = await get_all_guests()
    keyboard = await select_guests_keyboard(guests, selected_guests)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Selection updated!")

@router.callback_query(F.data == "confirm_guests")
async def confirm_guests(callback: CallbackQuery, state: FSMContext):
    """Confirm the selected guests and create the meeting."""
    chat_id = callback.message.chat.id

    # Ensure the user is authenticated
    if chat_id not in user_credentials:
        await callback.message.answer("You need to authenticate first! Use /auth to authorize.")
        return

    data = await state.get_data()
    guests = await get_all_guests()

    # Filter selected guests
    selected_guest_ids = data.get("selected_guests", [])
    selected_guests = [guest for guest in guests if guest.id in selected_guest_ids]

    try:
        # Use stored credentials to create the meeting
        creds_json = user_credentials[chat_id]
        meeting_link = await schedule_google_meet(
            credentials_json=creds_json,
            name=data["name"],
            date=data["date"],
            time=data["time"],
            guests=selected_guests,
        )
        await callback.message.answer(f"Meeting created successfully! Link: {meeting_link}")
        await state.clear()
    except Exception as e:
        await callback.message.answer(f"Error creating meeting: {e}")
        
        
# Add a new guest
@router.message(Command("gmeet_add_guest"))
async def add_guest_name(message: Message, state: FSMContext):
    await state.set_state(GoogleMeetStates.add_guest_name)
    await message.answer("Enter guest's name:")

@router.message(GoogleMeetStates.add_guest_name)
async def add_guest_email(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(GoogleMeetStates.add_guest_email)
    await message.answer("Enter guest's email:")

@router.message(GoogleMeetStates.add_guest_email)
async def save_guest(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_guest(name=data["name"], email=message.text)
    await message.answer("Guest added successfully!")
    await state.clear()

# Delete a guest
@router.message(Command("gmeet_delete_guest"))
async def delete_guest_handler(message: Message):
    guests = await get_all_guests()
    keyboard = await delete_guest_keyboard(guests)
    await message.answer("Select a guest to delete:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("delete_guest"))
async def delete_guest_callback(callback: CallbackQuery):
    guest_id = int(callback.data.split(":")[1])
    await delete_guest(guest_id)
    await callback.message.answer("Guest deleted successfully!")