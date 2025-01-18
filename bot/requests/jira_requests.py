from jira import JIRA
from bot.config.settings import settings
import requests, asyncio, datetime
from bot.database.models import JiraUser, async_session
from bot.config.settings import settings
from sqlalchemy import select
from aiogram.types import Message
import asyncio
from concurrent.futures import ThreadPoolExecutor


jira = JIRA(
    server=settings.jira_base_url,
    basic_auth=(settings.jira_email, settings.jira_api_token)
    )


def sync_create_jira_task(issue_dict):
    return jira.create_issue(fields=issue_dict)


async def get_issues_by_account_id(account_id: str, statuses: list = None):
    statuses = statuses or ["TO DO", "IN PROGRESS", "IN REVIEW"]
    jql = f"""assignee = "{account_id}" AND status IN ({", ".join([f'"{status}"' for status in statuses])})"""
    try:
        result = jira.search_issues(jql, maxResults=100)  # Fetch up to 100 issues (adjust as needed)
        print(result)
        return list(result)  # Convert the ResultList to a standard list
    except Exception as e:
        raise Exception(f"Failed to fetch issues: {e}")


async def get_issues_by_status(account_id: str = None, status: str = None, project_key: str = None):
    jql_parts = []
    if account_id:
        jql_parts.append(f'assignee = "{account_id}"')
    if status:
        jql_parts.append(f'status = "{status}"')
    if project_key:
        jql_parts.append(f'project = "{project_key}"')

    jql = " AND ".join(jql_parts)

    try:
        result = jira.search_issues(jql, maxResults=100)  # Fetch up to 100 issues
        return list(result)
    except Exception as e:
        raise Exception(f"Failed to fetch issues: {e}")

async def get_all_bugs():

    statuses = ["TO DO", "IN PROGRESS", "IN REVIEW"]
    jql = f"""
        project = "FA" AND issuetype = "Bug" AND status IN ({", ".join(f'"{status}"' for status in statuses)})
    """
    try:
        issues = jira.search_issues(jql, maxResults=1000)  # Adjust maxResults as needed
        return sorted(
            issues,
            key=lambda issue: (
                issue.fields.parent.key if hasattr(issue.fields, "parent") else "No Parent",
                issue.fields.summary.lower(),
                issue.fields.status.name,
                issue.fields.assignee.displayName.lower() if issue.fields.assignee else "Unassigned",
            ),
        )
    except Exception as e:
        raise Exception(f"Failed to fetch bugs: {e}")


def format_bugs_list(issues):
    tasks_by_parent = {}
    for issue in issues:
        parent = issue.fields.parent.key if hasattr(issue.fields, "parent") else "No Parent"
        if parent not in tasks_by_parent:
            tasks_by_parent[parent] = []
        tasks_by_parent[parent].append(issue)

    response = "**All Bugs (TO DO, IN PROGRESS, IN REVIEW):**\n"
    for parent, tasks in tasks_by_parent.items():
        response += f"\n**Parent:** {parent}\n"
        for task in tasks:
            title = task.fields.summary
            status = task.fields.status.name
            assignee = task.fields.assignee.displayName if task.fields.assignee else "Unassigned"
            description = task.fields.description or "No description provided."
            jira_link = f"https://your-jira-instance.atlassian.net/browse/{task.key}"

            response += (
                f"- **{task.key}**: {title} (Status: {status}, Assignee: {assignee})\n"
                f"  Description: {description}\n"
                f"  [View on Jira]({jira_link})\n"
            )

    return response if response.strip() else "No bugs found."


async def get_in_progress_issues():
    jql = 'project = "FA" AND status = "IN PROGRESS" ORDER BY parent ASC'

    try:
        jira = JIRA(
            server=settings.jira_base_url,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
        return jira.search_issues(jql)
    except Exception as e:
        raise Exception(f"Failed to fetch IN PROGRESS issues for project FA: {e}")


def format_in_progress_issues(issues):
    tasks_by_parent = {}
    for issue in issues:
        parent = issue.fields.parent.key if hasattr(issue.fields, "parent") else "No Parent"
        if parent not in tasks_by_parent:
            tasks_by_parent[parent] = []
        tasks_by_parent[parent].append(issue)

    # Sort parents alphabetically
    sorted_parents = sorted(tasks_by_parent.keys())

    # Format the grouped tasks
    response = "Current IN PROGRESS tasks in project FA:\n"
    for parent in sorted_parents:
        response += f"\n**Parent:** {parent}\n"

        # Group tasks by assignee
        tasks_by_assignee = {}
        for task in tasks_by_parent[parent]:
            assignee = task.fields.assignee.displayName if task.fields.assignee else "Unassigned"
            if assignee not in tasks_by_assignee:
                tasks_by_assignee[assignee] = []
            tasks_by_assignee[assignee].append(task)

        # Sort assignees alphabetically
        sorted_assignees = sorted(tasks_by_assignee.keys())

        # Format tasks for each assignee
        for assignee in sorted_assignees:
            response += f"\n{assignee}:\n"
            for task in tasks_by_assignee[assignee]:
                key = task.key
                summary = task.fields.summary
                jira_link = f"https://your-jira-instance.atlassian.net/browse/{key}"

                # Add task details with links
                response += f"- **{key}**: {summary} (Assignee: {assignee})\n"
                response += f"  [Jira Link]({jira_link})\n"

    if not response.strip():
        return "No tasks found."

    return response


def format_on_dev_tasks(issues):
    tasks_by_parent = {}
    for issue in issues:
        parent = issue.fields.parent.key if hasattr(issue.fields, "parent") else "No Parent"
        if parent not in tasks_by_parent:
            tasks_by_parent[parent] = []
        tasks_by_parent[parent].append(issue)

    # Sort parents alphabetically
    sorted_parents = sorted(tasks_by_parent.keys())

    # Format the grouped tasks
    response = "ON DEV tasks in project FA:\n"
    for parent in sorted_parents:
        response += f"\n**Parent:** {parent}\n"
        for task in tasks_by_parent[parent]:
            # Task details
            key = task.key
            summary = task.fields.summary
            assignee = task.fields.assignee.displayName if task.fields.assignee else "Unassigned"
            jira_link = f"https://your-jira-instance.atlassian.net/browse/{key}"

            # Add task details with links
            response += f"- **{key}**: {summary} (Assignee: {assignee})\n"
            response += f"  [Jira Link]({jira_link})\n"

    if not response.strip():
        return "No tasks found."

    return response


def format_tasks_with_links(issues):
    """
    Format Jira tasks into a readable text with links and additional details.
    :param issues: List of Jira Issue objects.
    :param limit: Maximum number of tasks to include in the response.
    :return: Formatted string of tasks.
    """
    response = "Your tasks:\n"

    for issue in issues:
        # Extract task details
        key = issue.key
        summary = issue.fields.summary
        status = issue.fields.status.name
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        jira_link = f"https://your-jira-instance.atlassian.net/browse/{key}"  # Generate the Jira link

        # Format task details
        response += f"- **{key}**: {summary} (Status: {status}, Assignee: {assignee})\n"
        response += f"  [Jira Link]({jira_link})\n"

        # Add links for Figma and Confluence if available
        figma_link = getattr(issue.fields, "customfield_10104", None)
        confluence_link = getattr(issue.fields, "customfield_10105", None)
        if figma_link:
            response += f"  [Figma Design]({figma_link})\n"
        if confluence_link:
            response += f"  [Confluence Doc]({confluence_link})\n"

    return response

async def add_user(name: str = None, telegram_id: int = None, email: str = None, account_id: str = None):
    """Adds a new Jira user to the database."""
    async with async_session() as session:
        user = JiraUser(name=name, telegram_id=telegram_id, email=email, account_id=account_id)
        session.add(user)
        try:
            await session.commit()
            print(f"User {name or account_id} added successfully.")
        except Exception as e:
            await session.rollback()  # Rollback in case of error
            print(f"Error adding user: {e}")
            raise e


async def get_assignees_list():
    """
    Fetch a list of Jira assignees from the database.

    :return: List of dictionaries with 'name' and 'account_id'.
    """
    async with async_session() as session:
        result = await session.execute(select(JiraUser.name, JiraUser.account_id))
        assignees = result.all()  # Get all results
        return [{"name": name, "account_id": account_id} for name, account_id in assignees]


async def get_on_dev_issues():
    """
    Fetch all Jira issues with status `ON DEV`.
    :return: List of Jira issues.
    """
    jql = 'status = "ON DEV" ORDER BY parent ASC'

    try:
        jira = JIRA(
            server=settings.jira_base_url,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
        return jira.search_issues(jql)
    except Exception as e:
        raise Exception(f"Failed to fetch ON DEV issues: {e}")


async def add_attachment_async(issue_key, file_path):
    """
    Attach a file to a Jira issue asynchronously.
    :param issue_key: The key of the Jira issue (e.g., "FA-100").
    :param file_path: Path to the file to be uploaded.
    """
    def upload_attachment():
        jira = JIRA(
            server=settings.jira_base_url,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
        with open(file_path, "rb") as f:
            jira.add_attachment(issue=issue_key, attachment=f)

    with ThreadPoolExecutor() as executor:
        await asyncio.get_event_loop().run_in_executor(executor, upload_attachment)


async def get_user_by_tg_id(telegram_id: int):
    """
    Fetch the Jira user associated with a given Telegram ID.
    :param session: Async SQLAlchemy session.
    :param telegram_id: Telegram user ID.
    :return: JiraUser object or None if not found.
    """
    async with async_session() as session:
        user_query = await session.execute(select(JiraUser).where(JiraUser.telegram_id == telegram_id))
        return user_query.scalar_one_or_none()



def get_all_projects(jira_instance):
    projects = jira_instance.projects()
    project_list = [(project.name, project.key) for project in projects]
    return project_list


def get_tasks_in_project(jira_instance, project_key):
    jql_query = f'project="{project_key}" ORDER BY created DESC'
    issues = jira_instance.search_issues(jql_query, maxResults=50)  # Fetch up to 50 tasks (can be adjusted)
    task_list = [(issue.key, issue.fields.summary) for issue in issues]
    return task_list


def create_issue_dict(
    title: str,
    description: str,
    parent: str = None,
    labels: list = None,
    priority: str = "Medium",
    assignee_account_id: str = None, 
    figma_link: str = None,
    confluence_link: str = None,
    original_estimate: str = None
):
    priority_options = ["Highest", "High", "Medium", "Low", "Lowest"]
    if priority not in priority_options:
        raise ValueError(f"Invalid priority. Choose from {priority_options}.")

    # Validate labels
    valid_labels = ["backend", "design", "frontend"]
    if not all(label in valid_labels for label in labels):
        raise ValueError(f"Invalid labels. Choose from {valid_labels}.")

    # Build the issue dictionary
    issue_dict = {
        "project": {"key": 'FA'},  # Extract project key from parent (e.g., "FA" from "FA-100")
        "summary": title,
        "description": description,
        "issuetype": {"name": "Task"},
        "priority": {"name": priority},
        "parent": {"key": parent},
        "labels": labels,
    }

    # Add optional fields if provided
    if assignee_account_id:
        issue_dict["assignee"] = {"accountId": assignee_account_id}
    if figma_link:
        issue_dict["customfield_10104"] = figma_link  # Figma link
    if confluence_link:
        issue_dict["customfield_10105"] = confluence_link  # Confluence link
    if original_estimate:
        issue_dict["timetracking"] =  original_estimate
   

    return issue_dict

def create_bug_dict(
    title: str,
    description: str,
    parent: str = None,
    labels: list = None,
    priority: str = "Medium",
    assignee_account_id: str = None, 
):
    # Validate priority
    priority_options = ["Highest", "High", "Medium", "Low", "Lowest"]
    if priority not in priority_options:
        raise ValueError(f"Invalid priority. Choose from {priority_options}.")

    # Validate labels (only if provided)
    valid_labels = ["backend", "design", "frontend"]
    if labels and not all(label in valid_labels for label in labels):
        raise ValueError(f"Invalid labels. Choose from {valid_labels}.")

    # Build the issue dictionary
    issue_dict = {
        "project": {"key": "FA"},  # Hardcoded project key for simplicity
        "summary": title,
        "description": description,
        "issuetype": {"name": "Bug"},
        "priority": {"name": priority},
    }

    # Add parent if provided
    if parent:
        issue_dict["parent"] = {"key": parent}

    # Add labels if provided
    if labels:
        issue_dict["labels"] = labels

    # Add optional assignee
    if assignee_account_id:
        issue_dict["assignee"] = {"accountId": assignee_account_id}

    return issue_dict

#print(f"Task created successfully! Task Key: {issue.key}")
    
# jira = JIRA(
#     server=settings.jira_base_url,
#     basic_auth=(settings.jira_email, settings.jira_api_token)
#     )
# # Fetch issue details
# issue = jira.issue("FA-266")

# # # Display all field names and values
# print("Field Names and Values for Task:")
# for field_key, field_value in issue.raw["fields"].items():
#     print(f"{field_key}: {field_value}")



#     projects = {
#     "BizDev & Mrktng":" BM",
#     "Devops": "DEVOPS",
#     "FITTON": "FA",
#     "HAPI": "HAP",
#     'PitchTalk': 'PT'
# }



# issue_dict =[ {
#     "project": "FA",  # Replace with your project key
#     "summary": "Test Task",
#     "description": "This is a test task.",
#     "issuetype": {"name": "Task"}
# }]

# try:
#     issue = jira.create_issues(field_list=issue_dict)
#     print(f"Task created successfully: {issue}")
# except Exception as e:
#     print(f"Error: {e}")


# async def populate_users():
#     """Populates the Jira users table with predefined data."""
#     users = [
#         {"name": "Aleksander Shevchenko", "account_id": "61d713ac8534980073c88cef"},
#         {"name": "Anastasiia Vakarenko", "account_id": "712020:ea929854-d22b-4a81-ba03-6a73635fbf6f"},
#         {"name": "Savytskyi Andrii", "account_id": "712020:a430427c-351e-4cb0-b5e1-5936931c3539"},
#         {"name": "Maksym Boichuk", "account_id": "712020:966c18c0-3728-44a7-b819-b316ee3e4776"},
#         {"name": "Illia Dolbnia", "account_id": "712020:9e4b98fb-055f-4e8d-af74-68591e1fd1cf"},
#         {"name": "Dzenko", "account_id": "61dc1693e67ea2006b1b8de7"},
#         {"name": "Eugene Pshenychkin", "account_id": "61d59a2c7c6f9800705470a4"},
#         {"name": "eugene.koychev", "account_id": "61dc1693567cb70070226bf4"},
#         {"name": "Markiyan Tyndyk", "account_id": "712020:973e4723-973b-4e12-be25-616ae8808be5"},
#         {"name": "kampod", "account_id": "712020:8812745a-a39d-4c6e-8166-be3a2542d439"},
#         {"name": "Oleg Kislitsa", "account_id": "61dc17bd9ee70a0068b13b98"},
#         {"name": "mister", "account_id": "61dc1693326554006c4ba6c2"},
#         {"name": "Taras Oliynyk", "account_id": "61bb084e2f24e70068b76f12"},
#         {"name": "rkonoval", "account_id": "61dc1692ce3652006a0a5d9a"},
#         {"name": "Sergio Sklyar", "account_id": "61dc17bd49f1950069880043"},
#         {"name": "Илья", "account_id": "5fd76482d364960139e26a03"},
#     ]

#     for user in users:
#         await add_user(name=user["name"], account_id=user["account_id"])
