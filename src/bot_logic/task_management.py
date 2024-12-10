from datetime import datetime

import dateparser
import google.generativeai as genai
from google.cloud.firestore_v1.base_query import FieldFilter

from .config import GEMINI_API_KEY
from .firebase_initializer import db

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# Function to infer priority and category using Gemini
def infer_task_details(task_description):
    response = model.generate_content(
        f"What is the priority and category of this task? "
        f"Only provide the priority (high,medium,low) as priority : and category (work, personal) as category : , "
        f"nothing else, no description, no extra information. : {task_description}"
    )
    return response.text.lower()


def add_task_from_input(task_description, deadline):
    inferred_details = infer_task_details(task_description)
    priority = "medium"
    category = "personal"

    if "priority" in inferred_details and "category" in inferred_details:
        priority = "high" if "high" in inferred_details else "low" if "low" in inferred_details else "medium"
        category = "work" if "work" in inferred_details else "personal"

    task_data = {
        "title": task_description,
        "category": category,
        "deadline": deadline,
        "priority": priority,
        "created_at": datetime.now(),
    }

    doc_ref = db.collection("tasks").document(task_description)
    doc_ref.set(task_data)
    return f"Task '{task_description}' added with priority: {priority} and category: {category}"


def get_tasks_by_priority(priority):
    tasks = db.collection("tasks").where(filter=FieldFilter("priority", "==", priority)).stream()
    task_list = [task.to_dict() for task in tasks]
    return task_list


def get_tasks_by_category(category):
    tasks = db.collection("tasks").where(filter=FieldFilter("category", "==", category)).stream()
    task_list = [task.to_dict() for task in tasks]
    return task_list


def get_upcoming_tasks(deadline_date):
    tasks = db.collection("tasks").where(filter=FieldFilter("deadline", "<=", deadline_date)).order_by(
        "deadline").stream()
    return [task.to_dict() for task in tasks]


def delete_task(task_title):
    db.collection("tasks").document(task_title).delete()
    return f"Task '{task_title}' deleted successfully!"


def task_voice_interaction(data):
    """
    Handle task-related commands. Payload should include additional data like task description or deadlines.
    """

    command = data.get("command", "")
    payload = data.get("payload", {})

    if "add" in command:
        task_description = payload.get("description")
        deadline_input = payload.get("deadline")
        deadline = dateparser.parse(deadline_input) if deadline_input else None
        return add_task_from_input(task_description, deadline)

    elif "priority" in command:
        priority = payload.get("priority", "medium").lower()
        return get_tasks_by_priority(priority)

    elif "category" in command:
        category = payload.get("category", "personal").lower()
        return get_tasks_by_category(category)

    elif "upcoming" in command:
        deadline_input = payload.get("deadline")
        if deadline_input == None:
            deadline_input = "tomorrow"
        deadline_date = dateparser.parse(deadline_input) if deadline_input else None
        return get_upcoming_tasks(deadline_date)

    elif "delete" in command:
        task_title = payload.get("title")
        return delete_task(task_title)

    else:
        return "Sorry, I didn't understand that command."
