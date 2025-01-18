from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Build guest selection keyboard
async def select_guests_keyboard(guests, selected_guests):
    """Build inline keyboard for selecting guests."""
    keyboard = InlineKeyboardBuilder()
    for guest in guests:
        is_selected = guest.id in selected_guests
        status = "✅" if is_selected else "❌"
        keyboard.add(
            InlineKeyboardButton(
                text=f"{guest.name} ({guest.email}) {status}",
                callback_data=f"toggle_guest:{guest.id}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="Confirm", callback_data="confirm_guests"))
    return keyboard.adjust(2).as_markup()  # Adjust to 2 columns

# Build guest deletion keyboard
async def delete_guest_keyboard(guests):
    keyboard = InlineKeyboardBuilder()
    for guest in guests:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{guest.name} ({guest.email})",
                callback_data=f"delete_guest:{guest.id}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    return keyboard.adjust(2).as_markup()