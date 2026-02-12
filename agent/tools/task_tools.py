from typing import Optional
from google.adk.tools import ToolContext
from utils.task_service import TaskService
from utils.models import TaskStatus
from utils.logging_config import configure_logging

logger = configure_logging()

def add_task(
    tool_context: ToolContext, 
    description: Optional[str] = None,
    equipment_name: Optional[str] = None,
    equipment_type: Optional[str] = None,
    location_description: Optional[str] = None
) -> str:
    """
    Adds a new task to the shared session queue.
    
    Args:
        description: A clear description of the task to be performed.
        equipment_name: (Optional) The unique name of the equipment (e.g. SF-1).
        equipment_type: (Optional) The category of the equipment (e.g. fans).
        location_description: (Optional) Robust topological location info.
    """
    logger.info(f"Adding task via tool: {description} for {equipment_name}")
    task = TaskService.add_task(
        tool_context, 
        description, 
        equipment_name=equipment_name,
        equipment_type=equipment_type,
        location_description=location_description
    )
    return f":::thought\n[System] Task added with ID: {task.id}\n:::\n"

def enqueue_all_identified_components(tool_context: ToolContext) -> str:
    """
    Automatically creates tasks for all equipment identified by previous agents.
    This reads the 'detailed_equipment_dict' from the state and enqueues one task per item.
    """
    logger.info("Enqueuing all equipment tasks via batch tool.")
    detailed_dict = tool_context.state.get("detailed_equipment_dict", {})
    if not detailed_dict:
        return ":::thought\n[System] No equipment data found in 'detailed_equipment_dict'.\n:::\n"
        
    tasks = TaskService.add_equipment_tasks_batch(tool_context, detailed_dict)
    
    if not tasks:
        return ":::thought\n[System] No tasks were created (check dictionary format).\n:::\n"
        
    task_ids = [t.id for t in tasks]
    return f":::thought\n[System] Successfully enqueued {len(tasks)} tasks: {', '.join(task_ids)}\n:::\n"

def set_task_status(tool_context: ToolContext, task_id: str, status: TaskStatus) -> str:
    """
    Updates the status of an existing task.
    
    Args:
        task_id: The unique ID of the task.
        status: The new status (pending, working, verification_ready, verified, failed).
    """
    # Ensure we use the string value regardless of whether it was passed as enum or string
    status_val = status.value if hasattr(status, 'value') else status
    logger.info(f"Updating task {task_id} status via tool to: {status_val}")
    
    updated_task = TaskService.set_task_status(tool_context, task_id, status)
    if updated_task:
        return f":::thought\n[System] Task {task_id} updated to {status_val}\n:::\n"
    return f":::thought\n[System] Task {task_id} not found.\n:::\n"

def fetch_pending_task(tool_context: ToolContext) -> str:
    """
    Retrieves the next task with 'pending' status from the queue.
    """
    logger.info("Getting next pending task via tool...")
    task = TaskService.fetch_pending_task(tool_context)
    if task:
        return f":::thought\n[System] Next pending task: [{task.id}] {task.description}\n:::\n"
    return ":::thought\n[System] No pending tasks found.\n:::\n"

def fetch_verification_task(tool_context: ToolContext) -> str:
    """
    Retrieves the next task ready for verification.
    """
    logger.info("Getting next verification task via tool...")
    task = TaskService.fetch_verification_task(tool_context)
    if task:
        return f":::thought\n[System] Next verification task: [{task.id}] {task.description}\n:::\n"
    return ":::thought\n[System] No tasks ready for verification.\n:::\n"

def count_pending_tasks(tool_context: ToolContext) -> int:
    """
    Returns the total number of tasks with 'pending' status in the current session.
    
    This is used by the Plan Agent to verify if all components identified from the image 
    have been enqueued as tasks before finishing the planning phase.
    """
    logger.info("Counting pending tasks for current session.")
    tasks = TaskService.get_tasks(tool_context)
    pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
    count = len(pending_tasks)
    logger.info(f"Counted {count} pending tasks.")
    return count

def get_remaining_planning_tasks(tool_context: ToolContext) -> str:
    """
    Counts the total equipment identified by parallel agents versus the tasks already enqueued.
    Returns a status message indicating how many tasks are still missing.
    
    The Plan Agent should use this tool to determine when to finish the planning phase.
    """
    logger.info("Calculating remaining planning tasks.")
    
    # 1. Get total identified equipment from state
    detailed_dict = tool_context.state.get("detailed_equipment_dict", {})
    total_equipment = 0
    if isinstance(detailed_dict, dict):
        for category, items in detailed_dict.items():
            if isinstance(items, dict):
                total_equipment += len(items)
            elif isinstance(items, list):
                total_equipment += len(items)
                
    # 2. Get count of existing tasks
    tasks = TaskService.get_tasks(tool_context)
    # We count all tasks created so far, regardless of status (though usually they are 'pending' during planning)
    total_tasks_created = len(tasks)
    
    remaining = total_equipment - total_tasks_created
    
    if remaining > 0:
        return f":::thought\n[System] Verification result: {total_tasks_created}/{total_equipment} components planned. {remaining} tasks remaining. Please continue planning.\n:::\n"
    elif remaining == 0:
        return f":::thought\n[System] All {total_equipment} components have been successfully planned. You can now call exit_loop_level_4() to finish the planning phase.\n:::\n"
    else:
        return f":::thought\n[System] Error/Warning: More tasks ({total_tasks_created}) exist than components identified ({total_equipment}). Please verify duplicates.\n:::\n"

def get_remaining_acting_tasks(tool_context: ToolContext) -> str:
    """
    Counts the total tasks with 'pending' status in the current session.
    Returns a status message indicating how many tasks are still missing execution.
    
    The Act Agent should use this tool to determine when to finish the acting phase.
    """
    logger.info("Calculating remaining acting tasks.")
    
    tasks = TaskService.get_tasks(tool_context)
    pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
    remaining = len(pending_tasks)
    
    if remaining > 0:
        return f":::thought\n[System] Verification result: {remaining} tasks still pending. Please continue execution.\n:::\n"
    else:
        return f":::thought\n[System] All planned tasks have been processed. You can now call exit_loop_level_4() to finish the acting phase.\n:::\n"
