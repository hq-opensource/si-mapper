from typing import Any, List, Optional
from google.adk.tools import ToolContext
from utils.models import Task, TaskStatus
from utils.logging_config import configure_logging
from utils.string_utils import format_agent_name

logger = configure_logging()

class TaskService:
    @staticmethod
    def get_tasks(context: ToolContext) -> List[Task]:
        """Retrieves and deserializes tasks from the session state."""
        tasks_data = context.state.get("tasks", [])
        valid_tasks = []
        for t in tasks_data:
            try:
                # Handle potential list conversion for tags if needed by Pydantic
                valid_tasks.append(Task(**t))
            except Exception as e:
                logger.error(f"Error deserializing task: {e}. Data: {t}")
                continue
        return valid_tasks

    @staticmethod
    def find_task_by_equipment(context: ToolContext, equipment_name: str) -> Optional[Task]:
        """Finds an existing task by equipment name."""
        tasks = TaskService.get_tasks(context)
        for task in tasks:
            if task.equipment_name == equipment_name:
                return task
        return None

    @staticmethod
    def save_tasks(context: ToolContext, tasks: List[Task]):
        """Serializes and saves tasks to the session state."""
        tasks_data = [t.model_dump() for t in tasks]
        context.state["tasks"] = tasks_data
        logger.info(f"Saved {len(tasks_data)} tasks to session state.")

    @staticmethod
    def add_task(
        context: ToolContext, 
        description: Optional[str] = None, 
        agent_name: Optional[str] = None,
        equipment_name: Optional[str] = None,
        equipment_type: Optional[str] = None,
        location_description: Optional[str] = None
    ) -> Task:
        """Adds a new task to the state."""
        if not agent_name:
            agent_name = context.state.get("active_agent", "System")
        
        agent_name = format_agent_name(agent_name).upper()
            
        if not description:
            description = f"Create {equipment_type or 'component'} with name '{equipment_name or 'unknown'}'. {location_description or ''}"

        new_task = Task(
            description=description, 
            agent_name=agent_name,
            equipment_name=equipment_name,
            equipment_type=equipment_type,
            location_description=location_description
        )
        logger.info(f"Adding new task: {new_task.description} (Agent: {agent_name})")
        
        tasks = TaskService.get_tasks(context)
        tasks.append(new_task)
        TaskService.save_tasks(context, tasks)
        
        return new_task

    @staticmethod
    def add_equipment_tasks_batch(
        context: ToolContext,
        equipment_dict: dict[str, Any]
    ) -> list[Task]:
        """Creates multiple tasks from a detailed equipment dictionary."""
        tasks_created = []
        for equipment_type, items in equipment_dict.items():
            if not isinstance(items, dict):
                continue
            for equipment_name, location_description in items.items():
                task = TaskService.add_task(
                    context,
                    equipment_name=equipment_name,
                    equipment_type=equipment_type,
                    location_description=location_description
                )
                tasks_created.append(task)
        return tasks_created

    @staticmethod
    def set_task_status(context: ToolContext, task_id: str, status: TaskStatus) -> Optional[Task]:
        """Updates the status of a specific task."""
        # Force cast to Enum member to avoid Pydantic V2 serialization warnings
        if isinstance(status, str):
            try:
                status = TaskStatus(status)
            except ValueError:
                logger.error(f"Invalid status string provided: {status}")
                return None

        logger.info(f"Updating task {task_id} to status: {status}")
        tasks = TaskService.get_tasks(context)
        updated_task = None
        
        current_agent = context.state.get("active_agent", "System")
        formatted_agent = format_agent_name(current_agent).upper()

        for task in tasks:
            if task.id == task_id:
                task.status = status
                task.agent_name = formatted_agent
                if status == TaskStatus.FAILED:
                    task.retry_count += 1
                updated_task = task
                break
        
        if updated_task:
            TaskService.save_tasks(context, tasks)
            logger.info(f"Successfully updated task {task_id}")
        else:
            logger.warning(f"Task {task_id} not found for status update.")
            
        return updated_task

    @staticmethod
    def fetch_pending_task(context: ToolContext) -> Optional[Task]:
        """
        Gets the next pending task (FIFO) and marks it as working.
        Checks for agent-specific pending states if a specialist is active.
        """
        tasks = TaskService.get_tasks(context)
        current_agent = context.state.get("active_agent", "System")
        formatted_agent = format_agent_name(current_agent).upper()
        
        logger.info(f"TaskService: fetch_pending_task called by {current_agent} (formatted: {formatted_agent}). Total tasks: {len(tasks)}")
        
        # Specialist detection
        agent_type = None
        if "BACNET" in formatted_agent:
            agent_type = "bacnet"
        elif "CONTROL" in formatted_agent:
            agent_type = "control"
        elif "ELECTRIC" in formatted_agent:
            agent_type = "electricity"

        logger.info(f"TaskService: Agent type identified as: {agent_type}")

        for task in tasks:
            # 1. Specialist Logic
            if agent_type == "bacnet" and task.bacnet_status == TaskStatus.PENDING:
                task.bacnet_status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
            elif agent_type == "control" and task.control_status == TaskStatus.PENDING:
                task.control_status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
            elif agent_type == "electricity" and task.electricity_status == TaskStatus.PENDING:
                task.electricity_status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
            
            # 2. Global Logic (Fallback for non-specialists)
            elif not agent_type and task.status == TaskStatus.PENDING:
                logger.info(f"Next pending global task found: {task.id}. Marking as WORKING by {formatted_agent}.")
                task.status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
                
        logger.info(f"No pending tasks found for agent {formatted_agent}.")
        return None
    
    @staticmethod
    def fetch_batch_pending_tasks(context: ToolContext, limit: int = 20) -> List[Task]:
        """
        Retrieves a batch of pending tasks (up to the limit).
        Marks them as WORKING immediately.
        Each specialist checks its own 'pending' state.
        """
        tasks = TaskService.get_tasks(context)
        current_agent = context.state.get("active_agent", "System").upper()
        formatted_agent = format_agent_name(current_agent).upper()
        
        # Determine agent type from name to skip already treated tasks
        agent_type = None
        if "BACNET" in formatted_agent:
            agent_type = "bacnet"
        elif "CONTROL" in formatted_agent:
            agent_type = "control"
        elif "ELECTRIC" in formatted_agent:
            agent_type = "electricity"
        
        batch = []
        count = 0
        
        for task in tasks:
            if count >= limit:
                break
            
            # Independent Status Logic
            is_pending = False
            if agent_type == "bacnet" and task.bacnet_status == TaskStatus.PENDING:
                is_pending = True
            elif agent_type == "control" and task.control_status == TaskStatus.PENDING:
                is_pending = True
            elif agent_type == "electricity" and task.electricity_status == TaskStatus.PENDING:
                is_pending = True
            elif not agent_type and task.status == TaskStatus.PENDING:
                is_pending = True

            if is_pending:
                if agent_type == "bacnet": task.bacnet_status = TaskStatus.WORKING
                elif agent_type == "control": task.control_status = TaskStatus.WORKING
                elif agent_type == "electricity": task.electricity_status = TaskStatus.WORKING
                else: task.status = TaskStatus.WORKING
                
                task.agent_name = formatted_agent
                batch.append(task)
                count += 1
                
        if batch:
            logger.info(f"Batch fetch: Retrieved {len(batch)} tasks for {formatted_agent}. Marked as WORKING.")
            TaskService.save_tasks(context, tasks)
            
        return batch
    
    @staticmethod
    def fetch_verification_task(context: ToolContext) -> Optional[Task]:
        """Gets the next task ready for verification and marks it as working."""
        tasks = TaskService.get_tasks(context)
        current_agent = context.state.get("active_agent", "System")
        formatted_agent = format_agent_name(current_agent).upper()
        
        for task in tasks:
            if task.status == TaskStatus.VERIFICATION_READY:
                logger.info(f"Next verification task found: {task.id}. Marking as WORKING by {formatted_agent}.")
                task.status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
        logger.info("No tasks ready for verification.")
        return None

    @staticmethod
    def add_grid_tasks_batch(
        context: ToolContext,
        grid_items: list[dict[str, Any]]
    ) -> list[Task]:
        """Creates tasks for each equipment found on the grid if they don't exist."""
        tasks_created = []
        for item in grid_items:
            equipment_type = item.get("type")
            
            # Skip "pure" ducts as they are conduits, not technical equipment
            if equipment_type == "duct":
                continue
                
            equipment_name = item.get("name")
            position = item.get("position") or item.get("start")
            
            existing = TaskService.find_task_by_equipment(context, equipment_name)
            if not existing:
                task = TaskService.add_task(
                    context,
                    description=f"Extract raw technical information for {equipment_name} ({equipment_type})",
                    equipment_name=equipment_name,
                    equipment_type=equipment_type,
                    location_description=f"Grid Position: {position}"
                )
                tasks_created.append(task)
        return tasks_created

    @staticmethod
    def update_technical_status(
        context: ToolContext, 
        equipment_name: str, 
        agent_type: str, 
        is_treated: bool = True
    ) -> Optional[Task]:
        """Updates the status for a specific specialist (bacnet, control, electricity)."""
        tasks = TaskService.get_tasks(context)
        updated_task = None
        
        agent_type = agent_type.lower()
        new_status = TaskStatus.VERIFIED if is_treated else TaskStatus.PENDING
        
        for task in tasks:
            if task.equipment_name == equipment_name:
                if agent_type == "bacnet":
                    task.bacnet_status = new_status
                    if is_treated and "treated-by-bacnet" not in task.tags:
                        task.tags.append("treated-by-bacnet")
                elif agent_type == "control":
                    task.control_status = new_status
                    if is_treated and "treated-by-control" not in task.tags:
                        task.tags.append("treated-by-control")
                elif agent_type == "electricity":
                    task.electricity_status = new_status
                    if is_treated and "treated-by-electricity" not in task.tags:
                        task.tags.append("treated-by-electricity")
                
                # Overall status management
                # The task stays in its current global status (PENDING or WORKING) 
                # until ALL specialist phases are VERIFIED.
                if task.bacnet_status == TaskStatus.VERIFIED and \
                   task.control_status == TaskStatus.VERIFIED and \
                   task.electricity_status == TaskStatus.VERIFIED:
                    task.status = TaskStatus.VERIFICATION_READY
                    task.agent_name = "SYSTEM (PHASE 2 COMPLETE)"
                else:
                    # Keep it as PENDING so other specialists can pick it up
                    if task.status not in [TaskStatus.VERIFIED, TaskStatus.FAILED]:
                        task.status = TaskStatus.PENDING
                
                updated_task = task
                break
        
        if updated_task:
            TaskService.save_tasks(context, tasks)
        return updated_task
