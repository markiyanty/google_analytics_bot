import os
from tempfile import gettempdir
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from bot.states.jira_states import TaskCreationStates, BugCreationStates, IssuesStates
from bot.requests.jira_requests import (create_issue_dict, 
                                        sync_create_jira_task, 
                                        add_attachment_async,
                                        get_user_by_tg_id,
                                        get_issues_by_account_id,
                                        format_tasks_with_links,
                                        format_in_progress_issues,
                                        get_issues_by_status,
                                        format_on_dev_tasks,
                                        create_bug_dict,
                                        get_all_bugs,
                                        format_bugs_list)
from bot.keyboards.jira_keyboard import (assignee_keyboard, 
                                        labels_keyboard, 
                                        priority_keyboard,
                                        parent_issues_keyboard)


router = Router()


@router.message(Command("jira_create_issue"))
async def start_task_creation(message: Message, state: FSMContext):
    """Start task creation."""
    await state.set_state(TaskCreationStates.title)
    await message.answer("Enter the task title:")


@router.message(TaskCreationStates.title)
async def set_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskCreationStates.description)
    await message.answer("Enter the task description (you can also attach media like photos, code, or tables):")


import os

@router.message(TaskCreationStates.description)
async def set_task_description(message: Message, state: FSMContext):
    """
    Handle task description updates, including photos and files.
    """
    if message.text == "/done":
        # Proceed to the next state when `/done` is received
        await state.set_state(TaskCreationStates.assignee)
        await message.answer("Description finalized. Proceeding to assignee selection.")
        return

    data = await state.get_data()
    description = data.get("description", "")
    attachments = data.get("attachments", [])

    # Check for photo attachments
    if message.photo:
        user_id = message.from_user.id
        photo = message.photo[-1]  # Get the highest resolution photo
        file_path = f"temp_photos/photo_{user_id}_{photo.file_id}.jpg"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Download the photo
            file_info = await message.bot.get_file(photo.file_id)
            downloaded_file = await message.bot.download_file(file_info.file_path)
            with open(file_path, "wb") as photo_file:
                photo_file.write(downloaded_file.getvalue())

            # Append the photo to attachments
            attachments.append(file_path)
            description += f"\n![Photo: {os.path.basename(file_path)}](attached later)\n"
        except Exception as e:
            await message.reply(f"Error processing photo: {e}")

    # Check for document attachments
    elif message.document:
        document = message.document
        file_id = document.file_id
        file_path = os.path.join("temp_files", document.file_name)  # Temp file path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Download the document
            file_info = await message.bot.get_file(file_id)
            downloaded_file = await message.bot.download_file(file_info.file_path)
            with open(file_path, "wb") as document_file:
                document_file.write(downloaded_file.getvalue())

            # Append the document to attachments
            attachments.append(file_path)
            description += f"\n[Attachment: {document.file_name}](attached later)\n"
        except Exception as e:
            await message.reply(f"Error processing document: {e}")

    # Handle plain text
    elif message.text:
        description += message.text + "\n"

    # Update the state with the new description and attachments
    await state.update_data(description=description, attachments=attachments)
    await message.answer(
        "Description updated. Send more details (text, photos, or files) or type `/done` when finished."
    )

@router.message(Command("done"), TaskCreationStates.assignee)
async def finish_description(message: Message, state: FSMContext):
    """Move to assignee selection."""
    await state.set_state(TaskCreationStates.assignee)

    # Fetch assignees dynamically from the database
    keyboard = await assignee_keyboard()
    await message.answer("Select an assignee:", reply_markup=keyboard)


@router.callback_query(TaskCreationStates.assignee, F.data.startswith("assignee"))
async def set_assignee(callback: CallbackQuery, state: FSMContext):
    account_id = callback.data.split("_")[1]
    await state.update_data(assignee_account_id=account_id)
    await state.set_state(TaskCreationStates.figma_link)
    await callback.message.answer("Enter the Figma link (or type `skip` if not applicable):")


@router.message(TaskCreationStates.figma_link)
async def set_figma_link(message: Message, state: FSMContext):
    link = message.text if message.text.lower() != "skip" else None
    await state.update_data(figma_link=link)
    await state.set_state(TaskCreationStates.confluence_link)
    await message.answer("Enter the Confluence link (or type `skip` if not applicable):")


@router.message(TaskCreationStates.confluence_link)
async def set_confluence_link(message: Message, state: FSMContext):
    link = message.text if message.text.lower() != "skip" else None
    await state.update_data(confluence_link=link)

    # Provide options for labels
    keyboard = InlineKeyboardBuilder()
    for label in ["backend", "frontend", "design"]:
        keyboard.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"toggle_label:{label}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="Done", callback_data="confirm_labels"))
    await state.set_state(TaskCreationStates.labels)
    await message.answer("Select labels for the task:", reply_markup=keyboard.as_markup())


@router.callback_query(TaskCreationStates.labels, F.data.startswith("toggle_label"))
async def toggle_label(callback: CallbackQuery, state: FSMContext):
    label = callback.data.split(":")[1]
    data = await state.get_data()
    labels = data.get("labels", [])
    if label in labels:
        labels.remove(label)
    else:
        labels.append(label)
    await state.update_data(labels=labels)

    # Update the keyboard with the toggled state
    keyboard = await labels_keyboard(selected_labels=labels)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Label '{label}' {'added' if label in labels else 'removed'}.")




@router.callback_query(TaskCreationStates.labels, F.data == "confirm_labels")
async def confirm_labels(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreationStates.priority)

    # Provide options for priority
    keyboard = await priority_keyboard()
    await callback.message.answer("Select priority for the task:", reply_markup=keyboard)



@router.callback_query(TaskCreationStates.priority,  F.data.startswith("set_priority"))
async def set_priority(callback: CallbackQuery, state: FSMContext):
    priority = callback.data.split(":")[1]
    await state.update_data(priority=priority)
    await state.set_state(TaskCreationStates.parent)

    # Provide options for parent issues
    parent_issues = ["FA-100", "FA-99"] 
    keyboard = await parent_issues_keyboard(parent_issues)
    await callback.message.answer("Select a parent issue:", reply_markup=keyboard)


@router.callback_query(TaskCreationStates.parent, F.data.startswith("set_parent"))
async def set_parent(callback: CallbackQuery, state: FSMContext):
    parent = callback.data.split(":")[1]
    await state.update_data(parent=parent)
    await state.set_state(TaskCreationStates.review)

    data = await state.get_data()
    review_message = f"""
**Task Review:**
- Title: {data['title']}
- Description: {data['description']}
- Assignee: {data.get('assignee_account_id')}
- Figma Link: {data.get('figma_link')}
- Confluence Link: {data.get('confluence_link')}
- Labels: {', '.join(data.get('labels', []))}
- Priority: {data.get('priority')}
- Parent Issue: {data.get('parent')}
    """
    await callback.message.answer(review_message, parse_mode="Markdown")
    await callback.message.answer("Type `/confirm` to send the request or `/cancel` to discard.")

@router.message(Command("confirm"), TaskCreationStates.review)
async def confirm_task_creation(message: Message, state: FSMContext):
    """
    Finalize and create the Jira task with attachments.
    """
    data = await state.get_data()

    # Construct the issue dictionary
    issue_dict = create_issue_dict(title=data["title"],
                                    description=data["description"],
                                    priority=  data.get("priority", "Medium"),
                                    labels=data.get("labels", []),
                                    assignee_account_id=data.get("assignee_account_id"),
                                    figma_link=data.get("figma_link"),
                                    confluence_link=data.get("confluence_link"),
                                    parent=data['parent'])


    try:
        # Step 1: Create the task
        issue = sync_create_jira_task(issue_dict)

        # Step 2: Attach files
        attachments = data.get("attachments", [])
        for file_path in attachments:
            try:
                await add_attachment_async(issue.key, file_path)
                os.remove(file_path)  # Delete the file after successful upload
            except Exception as e:
                await message.reply(f"Failed to attach {file_path}: {e}")

        # Step 3: Respond to the user
        await message.answer(f"Task created successfully! Task key: {issue.key}")
        await state.clear()
    except Exception as e:
        await message.reply(f"Failed to create task: {e}")
        

@router.message(Command("cancel"), TaskCreationStates.review)
async def cancel_task_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Task creation cancelled.")
    
    

@router.message(Command("jira_my_issues"))
async def my_issues_handler(message: Message):
    """
    Handle the /my_issues command to fetch and display tasks assigned to the user.
    """
    telegram_id = message.from_user.id
    user = await get_user_by_tg_id(telegram_id)

    if not user:
        await message.answer("Your Jira account is not linked to this Telegram ID.")
        return

    try:
        # Fetch issues assigned to the user
        issues = await get_issues_by_account_id(user.account_id)

        if not issues:
            await message.answer("You currently have no tasks with the specified statuses.")
            return

        # Format and send the list of tasks
        response = format_tasks_with_links(issues, limit=10)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Failed to fetch your tasks: {e}")


@router.message(Command("jira_user_issues"))
async def user_issues_handler(message: Message, state: FSMContext):
    """
    Display a keyboard with all Jira assignees for selecting to view their tasks.
    """
    await state.set_state(IssuesStates.issue_creation)
    try:
        # Generate the keyboard with all assignees
        keyboard = await assignee_keyboard()

        if not keyboard.inline_keyboard:
            await message.answer("No assignees found.")
            return

        await message.answer("Select an assignee to view their tasks:", reply_markup=keyboard)
    except Exception as e:
        await message.answer(f"Failed to fetch assignees: {e}")


@router.callback_query(F.data.startswith("assignee_"), IssuesStates.issue_creation)
async def user_issues_callback(callback: CallbackQuery, state: FSMContext):
    """
    Fetch and display tasks for the selected assignee with links.
    """
    account_id = callback.data.split("_")[1]  # Extract the account ID from the callback data

    try:
        # Fetch issues for the selected assignee
        issues = await get_issues_by_account_id(account_id)

        if not issues:
            await callback.message.edit_text("No tasks found for this user.")
            return

        # Format the tasks into a readable response
        response = format_tasks_with_links(issues)  # Limit to the first 10 tasks
        await callback.message.edit_text(response, parse_mode="Markdown")
    except Exception as e:
        await callback.message.edit_text(f"Failed to fetch tasks: {e}")
    await state.clear()


@router.message(Command("jira_ready_for_test"))
async def ready_for_test_handler(message: Message):
    """
    Fetch and display all `READY FOR TEST` tasks from project `FA`, grouped and sorted by parent issue.
    """
    try:
        # Fetch READY FOR TEST issues
        issues = await get_issues_by_status(status="ON DEV", project_key="FA")

        if not issues:
            await message.answer("No tasks with status `ON DEV` found in project FA.")
            return

        # Format tasks grouped by parent issue
        response = format_on_dev_tasks(issues)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Failed to fetch tasks: {e}")
        
        
@router.message(Command("jira_current_issues"))
async def current_issues_handler(message: Message):
    """
    Fetch and display all `IN PROGRESS` tasks for project `FA`, grouped and sorted by parent issue.
    """
    try:
        # Fetch IN PROGRESS issues for project FA
        issues = await get_issues_by_status(status="IN PROGRESS", project_key="FA")

        if not issues:
            await message.answer("No tasks with status `IN PROGRESS` found in project FA.")
            return

        # Format and display the grouped tasks
        response = format_in_progress_issues(issues)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Failed to fetch tasks: {e}")


@router.message(Command("jira_report_bug"))
async def start_bug_report(message: Message, state: FSMContext):
    """
    Start bug report creation using a replied-to message.
    Automatically extracts the description and attachments from the reply.
    """
    if not message.reply_to_message:
        await message.answer("Please reply to a message to use as the bug description.")
        return

    # Extract description and attachments from the replied-to message
    reply_message = message.reply_to_message
    description = reply_message.text or reply_message.caption or "No description provided."
    print(f"Extracted description: {description}")  # Debugging
    attachments = []

    if reply_message.photo:
        # Save photo locally
        photo = reply_message.photo[-1]
        file_path = f"temp_photos/photo_{photo.file_id}.jpg"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_info = await message.bot.get_file(photo.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        with open(file_path, "wb") as photo_file:
            photo_file.write(downloaded_file.getvalue())
        attachments.append(file_path)

    # Initialize bug-specific state data
    await state.set_state(BugCreationStates.title)
    await state.update_data(
        description=description,
        attachments=attachments
    )
    await message.answer("Enter the title for bug report")

@router.message(BugCreationStates.title)
async def set_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(BugCreationStates.assignee)
    keyboard = await assignee_keyboard()
    await message.answer("Description prepared. Now, select an assignee for the bug report.", reply_markup=keyboard)


@router.message(BugCreationStates.assignee)
async def finish_description(message: Message, state: FSMContext):
    """Move to assignee selection."""
    await state.set_state(BugCreationStates.assignee)

    # Fetch assignees dynamically from the database
    keyboard = await assignee_keyboard()
    await message.answer("Select an assignee:", reply_markup=keyboard)


@router.callback_query(BugCreationStates.assignee, F.data.startswith("assignee"))
async def set_assignee(callback: CallbackQuery, state: FSMContext):
    account_id = callback.data.split("_")[1]
    await state.update_data(assignee_account_id=account_id)
    keyboard = InlineKeyboardBuilder()
    for label in ["backend", "frontend", "design"]:
        keyboard.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"toggle_label:{label}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="Done", callback_data="confirm_labels"))
    await state.set_state(BugCreationStates.labels)
    await callback.message.answer("Select labels for the task:", reply_markup=keyboard.as_markup())
    


@router.callback_query(BugCreationStates.labels, F.data.startswith("toggle_label"))
async def toggle_label(callback: CallbackQuery, state: FSMContext):
    label = callback.data.split(":")[1]
    data = await state.get_data()
    labels = data.get("labels", [])
    if label in labels:
        labels.remove(label)
    else:
        labels.append(label)
    await state.update_data(labels=labels)

    # Update the keyboard with the toggled state
    keyboard = await labels_keyboard(selected_labels=labels)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Label '{label}' {'added' if label in labels else 'removed'}.")




@router.callback_query(BugCreationStates.labels, F.data == "confirm_labels")
async def confirm_labels(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BugCreationStates.priority)

    # Provide options for priority
    keyboard = await priority_keyboard()
    await callback.message.answer("Select priority for the task:", reply_markup=keyboard)



@router.callback_query(BugCreationStates.priority,  F.data.startswith("set_priority"))
async def set_priority(callback: CallbackQuery, state: FSMContext):
    priority = callback.data.split(":")[1]
    await state.update_data(priority=priority)
    await state.set_state(BugCreationStates.parent)

    # Provide options for parent issues
    parent_issues = ["FA-100", "FA-99"] 
    keyboard = await parent_issues_keyboard(parent_issues)
    await callback.message.answer("Select a parent issue:", reply_markup=keyboard)


@router.callback_query(BugCreationStates.parent, F.data.startswith("set_parent"))
async def set_parent(callback: CallbackQuery, state: FSMContext):
    parent = callback.data.split(":")[1]
    await state.update_data(parent=parent)
    await state.set_state(BugCreationStates.review)

    data = await state.get_data()
    review_message = f"""
**Task Review:**
- Title: {data['title']}
- Description: {data['description']}
- Assignee: {data.get('assignee_account_id')}
- Labels: {', '.join(data.get('labels', []))}
- Priority: {data.get('priority')}
- Parent Issue: {data.get('parent')}
    """
    await callback.message.answer(review_message, parse_mode="Markdown")
    await callback.message.answer("Type `/confirm` to send the request or `/cancel` to discard.")

@router.message(Command("confirm"), BugCreationStates.review)
async def confirm_bug_report(message: Message, state: FSMContext):
    """
    Finalize and create the Jira bug report with attachments.
    """
    data = await state.get_data()

    # Construct the bug dictionary
    issue_dict = create_bug_dict(
        title=data["title"],
        description=data["description"],
        priority=data.get("priority", "Medium"),
        labels=data.get("labels"),
        parent=data.get("parent"),
        assignee_account_id=data.get("assignee_account_id")
    )

    try:
        # Step 1: Create the bug report
        issue = sync_create_jira_task(issue_dict)

        # Step 2: Attach files
        attachments = data.get("attachments", [])
        for file_path in attachments:
            try:
                await add_attachment_async(issue.key, file_path)
                os.remove(file_path)  # Delete the file after successful upload
            except Exception as e:
                await message.reply(f"Failed to attach {file_path}: {e}")

        # Step 3: Respond to the user
        await message.answer(f"Bug report created successfully! Task key: {issue.key}")
        await state.clear()
    except Exception as e:
        await message.reply(f"Failed to create bug report: {e}")
        
        

@router.message(Command("cancel"), BugCreationStates.review)
async def cancel_task_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Task creation cancelled.")
    

@router.message(Command("jira_all_bugs"))
async def jira_all_bugs_handler(message: Message):
    """
    Fetch and display all bugs with specific statuses, sorted and formatted.
    """
    try:
        # Fetch bugs
        bugs = await get_all_bugs()

        if not bugs:
            await message.answer("No bugs found with statuses TO DO, IN PROGRESS, or IN REVIEW.")
            return

        # Format the response
        response = format_bugs_list(bugs)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Failed to fetch bugs: {e}")