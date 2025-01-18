from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from bot.database.models import JiraUser 
from sqlalchemy.ext.asyncio import AsyncSession
from bot.requests.jira_requests import get_assignees_list

async def assignee_keyboard():
    """
    Build inline keyboard for selecting assignees from the database.
    :return: Inline keyboard markup.
    """
    keyboard = InlineKeyboardBuilder()
    assignees = await get_assignees_list()
    for assignee in assignees:
        keyboard.add(
            InlineKeyboardButton(
                text=f'{assignee["name"]}',
                callback_data=f"assignee_{assignee['account_id']}"
            )
        )
    return keyboard.adjust(2).as_markup()

async def labels_keyboard(selected_labels=None):
    """
    Build inline keyboard for selecting labels.
    :param selected_labels: List of currently selected labels.
    :return: Inline keyboard markup.
    """
    selected_labels = selected_labels or []
    labels = ["backend", "frontend", "design"]
    keyboard = InlineKeyboardBuilder()
    for label in labels:
        is_selected = "✅" if label in selected_labels else "❌"
        keyboard.add(
            InlineKeyboardButton(
                text=f"{label} {is_selected}",
                callback_data=f"toggle_label:{label}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="Done", callback_data="confirm_labels"))
    return keyboard.adjust(4).as_markup()


async def priority_keyboard():
    """
    Build inline keyboard for selecting task priority.
    :return: Inline keyboard markup.
    """
    priorities = ["Highest", "High", "Medium", "Low", "Lowest"]
    keyboard = InlineKeyboardBuilder()
    for priority in priorities:
        keyboard.add(
            InlineKeyboardButton(
                text=priority,
                callback_data=f"set_priority:{priority}"
            )
        )
    return keyboard.adjust(5).as_markup()


async def parent_issues_keyboard(parent_issues):
    """
    Build inline keyboard for selecting parent issues.
    :param parent_issues: List of parent issue keys.
    :return: Inline keyboard markup.
    """
    keyboard = InlineKeyboardBuilder()
    for parent in parent_issues:
        keyboard.add(
            InlineKeyboardButton(
                text=parent,
                callback_data=f"set_parent:{parent}"
            )
        )
    return keyboard.adjust(2).as_markup()