# environment/tasks.py
# Task definitions for SQL Data Analyst environment
# 3 Tasks: Easy (single table COUNT), Medium (JOIN + aggregation), Hard (subquery/ordering)

from dataclasses import dataclass
from typing import List, Callable, Any
import random


@dataclass
class Task:
    """
    Represents a data analysis task for the agent.
    
    Attributes:
        task_id: Unique identifier for the task
        difficulty: easy, medium, or hard
        question: The business question to answer
        ground_truth: The expected correct answer
        ground_truth_sql: A SQL query that produces the correct answer
        description: Additional context about the task
    """
    task_id: str
    difficulty: str
    question: str
    ground_truth: Any
    ground_truth_sql: str
    description: str


# ============================================
# TASK DEFINITIONS
# ============================================

TASK_EASY = Task(
    task_id="easy_user_count",
    difficulty="easy",
    question=(
        "How many users are registered in the system? "
        "Provide the total count as a single number."
    ),
    ground_truth=15,
    ground_truth_sql="SELECT COUNT(*) FROM users",
    description="Single table COUNT query on users table"
)

TASK_MEDIUM = Task(
    task_id="medium_usa_revenue",
    difficulty="medium",
    question=(
        "What is the total revenue (sum of total_amount) from purchases made by users in the USA? "
        "Provide the total as a number (rounded to 2 decimal places if needed)."
    ),
    ground_truth=2423.87,  # Sum of purchases by USA users (user_ids: 1, 4, 7, 10, 14)
    ground_truth_sql="""
        SELECT ROUND(SUM(p.total_amount), 2) as total_revenue
        FROM purchases p
        JOIN users u ON p.user_id = u.user_id
        WHERE u.country = 'USA'
    """,
    description="Two-table JOIN with SUM aggregation filtered by country"
)

TASK_HARD = Task(
    task_id="hard_top_spender",
    difficulty="hard",
    question=(
        "Who is the top spender (user with highest total purchase amount)? "
        "Provide the username of the user who spent the most money in total."
    ),
    ground_truth="alice",  # alice has purchases totaling 1509.96 (1299.99 + 59.98 + 149.99)
    ground_truth_sql="""
        SELECT u.username
        FROM users u
        JOIN purchases p ON u.user_id = p.user_id
        GROUP BY u.user_id, u.username
        ORDER BY SUM(p.total_amount) DESC
        LIMIT 1
    """,
    description="Complex query with JOIN, GROUP BY, ORDER BY, and LIMIT"
)


# List of all tasks
TASKS: List[Task] = [TASK_EASY, TASK_MEDIUM, TASK_HARD]


def get_task_by_id(task_id: str) -> Task:
    """
    Get a task by its ID.
    
    Args:
        task_id: The unique task identifier
        
    Returns:
        Task: The matching task
        
    Raises:
        ValueError: If task_id not found
    """
    for task in TASKS:
        if task.task_id == task_id:
            return task
    raise ValueError(f"Task not found: {task_id}")


def get_task_by_difficulty(difficulty: str) -> Task:
    """
    Get a task by difficulty level.
    
    Args:
        difficulty: easy, medium, or hard
        
    Returns:
        Task: A task matching the difficulty
        
    Raises:
        ValueError: If difficulty not found
    """
    for task in TASKS:
        if task.difficulty == difficulty:
            return task
    raise ValueError(f"No task found for difficulty: {difficulty}")


def get_random_task() -> Task:
    """
    Get a random task from the available tasks.
    
    Returns:
        Task: A randomly selected task
    """
    return random.choice(TASKS)


def get_all_tasks() -> List[Task]:
    """
    Get all available tasks.
    
    Returns:
        List[Task]: All defined tasks
    """
    return TASKS.copy()
