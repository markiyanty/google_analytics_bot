from aiogram.fsm.state import StatesGroup, State

class TaskCreationStates(StatesGroup):
    title = State()
    description = State()
    assignee = State()
    figma_link = State()
    confluence_link = State()
    labels = State()
    priority = State()
    parent = State()
    review = State()
    confirm = State()
    
class BugCreationStates(StatesGroup):
    issue_type = State()
    title = State()
    description = State()
    labels = State()
    assignee = State()
    priority = State()
    parent = State()
    review = State()
    
    
class IssuesStates(StatesGroup):
    issue_creation=State()