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
        """Gets the next pending task (FIFO) and marks it as working."""
        tasks = TaskService.get_tasks(context)
        current_agent = context.state.get("active_agent", "System")
        formatted_agent = format_agent_name(current_agent).upper()
        
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                logger.info(f"Next pending task found: {task.id}. Marking as WORKING by {formatted_agent}.")
                task.status = TaskStatus.WORKING
                task.agent_name = formatted_agent
                TaskService.save_tasks(context, tasks)
                return task
        logger.info("No pending tasks found.")
        return None
    
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
        """Updates the treatment flag for a specific agent type (bacnet, control, electricity)."""
        tasks = TaskService.get_tasks(context)
        updated_task = None
        
        agent_type = agent_type.lower()
        
        for task in tasks:
            if task.equipment_name == equipment_name:
                if agent_type == "bacnet":
                    task.bacnet_treated = is_treated
                    if is_treated and "treated-by-bacnet" not in task.tags:
                        task.tags.append("treated-by-bacnet")
                elif agent_type == "control":
                    task.control_treated = is_treated
                    if is_treated and "treated-by-control" not in task.tags:
                        task.tags.append("treated-by-control")
                elif agent_type == "electricity":
                    task.electricity_treated = is_treated
                    if is_treated and "treated-by-electricity" not in task.tags:
                        task.tags.append("treated-by-electricity")
                
                # Auto-complete if all three are treated
                if task.bacnet_treated and task.control_treated and task.electricity_treated:
                    task.status = TaskStatus.VERIFICATION_READY
                
                updated_task = task
                break
        
        if updated_task:
            TaskService.save_tasks(context, tasks)
        return updated_task
