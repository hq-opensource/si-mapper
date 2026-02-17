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

def enqueue_grid_tasks(tool_context: ToolContext, grid_data: list[dict]) -> str:
    """
    Creates tasks for each piece of equipment found on the grid.
    
    Args:
        grid_data: List of equipment dictionaries (from read_grid).
    """
    logger.info("Enqueuing grid tasks.")
    tasks = TaskService.add_grid_tasks_batch(tool_context, grid_data)
    return f":::thought\n[System] Successfully enqueued {len(tasks)} tasks from grid.\n:::\n"

def mark_technical_progress(
    tool_context: ToolContext, 
    equipment_name: str, 
    agent_type: str
) -> str:
    """
    Marks a piece of equipment as treated by a specific agent (bacnet, control, electricity).
    
    Args:
        equipment_name: Name of the equipment.
        agent_type: Type of agent ('bacnet', 'control', or 'electricity').
    """
    logger.info(f"Marking {agent_type} progress for {equipment_name}")
    task = TaskService.update_technical_status(tool_context, equipment_name, agent_type)
    if task:
        # Check if it was the last one
        if task.status == TaskStatus.VERIFICATION_READY:
            return f":::thought\n[System] {agent_type} treatment complete for {equipment_name}. ALL AGENTS DONE. Task ready for verification.\n:::\n"
        return f":::thought\n[System] {agent_type} treatment complete for {equipment_name}. Remaining agents still needed.\n:::\n"
    return f":::thought\n[System] Task for {equipment_name} not found.\n:::\n"

def fetch_batch_tasks(tool_context: ToolContext, limit: int = 20) -> str:
    """
    Retrieves up to 'limit' pending tasks at once.
    Use this to process multiple items in a single iteration.
    
    Returns:
        A JSON string representation of the list of tasks.
    """
    import json
    logger.info(f"Fetching batch of tasks (limit={limit})...")
    tasks = TaskService.fetch_batch_pending_tasks(tool_context, limit)
    
    if not tasks:
        return ":::thought\n[System] No pending tasks found.\n:::\n []"
    
    # helper to make task serializable
    serializable_tasks = [t.model_dump() for t in tasks]
    
    # We return raw JSON so the LLM can parse it easily
    # We also add a thought block for the log
    return f":::thought\n[System] Retrieved {len(tasks)} tasks.\n:::\n{json.dumps(serializable_tasks, indent=2)}"

def mark_technical_progress_batch(
    tool_context: ToolContext, 
    updates: list[dict[str, str]]
) -> str:
    """
    Marks multiple equipment items as treated by a specific agent type in a single call.
    
    Args:
        updates: A list of dicts, where each dict has "equipment_name" and "agent_type".
                 Example: [{"equipment_name": "AHU-1", "agent_type": "bacnet"}, ...]
    """
    logger.info(f"Marking batch technical progress for {len(updates)} items.")
    
    success_count = 0
    for update in updates:
        equipment_name = update.get("equipment_name")
        agent_type = update.get("agent_type")
        
        if equipment_name and agent_type:
            res = TaskService.update_technical_status(tool_context, equipment_name, agent_type)
            if res:
                success_count += 1
                
    return f":::thought\n[System] Successfully marked {success_count}/{len(updates)} tasks as treated.\n:::\n"

def create_batch_tasks(tool_context: ToolContext) -> str:
    """
    Synchronizes the task queue with the current state of the grid.
    Reads all components from the grid and creates a task for each one.
    This is an internal batch tool that encapsulates reading and enqueuing.
    """
    logger.info("Executing create_batch_tasks tool.")
    
    import os
    import sys
    from dotenv import load_dotenv
    
    # 1. Setup Logic similar to tests/test_read_grid.py to ensure imports work
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # agent/tools/ -> agent/ -> si-mapper/
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        
        logger.info(f"debug: Project Root identified as: {project_root}")
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.info("debug: Added project root to sys.path")
            
        # Try importing now that path is set
        try:
            from mcp_server.graphivac.grid_manager import GridManager
            logger.info("debug: Successfully imported GridManager")
        except ImportError as ie:
            logger.error(f"debug: Failed to import GridManager: {ie}")
            logger.error(f"debug: Current sys.path: {sys.path}")
            return f":::thought\n[System] Critical Error: Could not import GridManager. Path issue. Debug info logged.\n:::\n"

        # 2. Load Environment Variables
        # Try to find the mcp.env relative to project root
        env_path = os.path.join(project_root, 'mcp_server', 'server', 'mcp.env')
        logger.info(f"debug: Checking env path: {env_path}")
        
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info("debug: Loaded mcp.env")
        else:
            load_dotenv()
            logger.info("debug: Warning - mcp.env not found, using default env")
        
        ORG_ID = os.getenv("GRAPHIVAC_ORG_ID")
        PROJECT_ID = os.getenv("GRAPHIVAC_PROJECT_ID")
        GRID_ID = os.getenv("GRAPHIVAC_GRID_ID")
        GRID_TITLE = os.getenv("GRAPHIVAC_GRID_TITLE")
        BASE_URL = os.getenv("GRAPHIVAC_BASE_URL")
        # Default font config is needed by the API init
        FONT_CONFIGS = {"family": "Serif", "style": "Oblique", "size": 20, "weight": "Lighter", "color": "string"}
        
        logger.info(f"debug: Config - Org: {ORG_ID}, Project: {PROJECT_ID}, Grid: {GRID_ID}, URL: {BASE_URL}")
        
        if not all([ORG_ID, PROJECT_ID, GRID_ID]):
            return f":::thought\n[System] Error: Missing required environment variables (Org/Project/Grid ID).\n:::\n"
            
        # 3. Fetch grid data
        logger.info("debug: Initializing GridManager...")
        manager = GridManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
        
        logger.info("debug: Calling read_grid()...")
        grid_data = manager.read_grid()
        logger.info(f"debug: read_grid returned {len(grid_data)} items")
        
        # 4. Enqueue tasks
        logger.info("debug: Creating tasks via TaskService...")
        tasks = TaskService.add_grid_tasks_batch(tool_context, grid_data)
        logger.info(f"debug: Tasks created count: {len(tasks)}")
        
        return f":::thought\n[System] Successfully synced with grid. Created {len(tasks)} new tasks. Total grid components processed: {len(grid_data)}.\n:::\n"
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"debug: Exception in create_batch_tasks: {tb}")
        return f":::thought\n[System] Unhandled exception in create_batch_tasks: {str(e)}\n:::\n"
