from enum import Enum

class TripIntent(str, Enum):
    CREATE_DAY_PLAN = "create_day_plan"
    REPLAN_DAY = "replan_day"
    MOVE_ACTIVITY = "move_activity"
    UPDATE_PREFERENCE = "update_preference"
    EXPLAIN_CHANGE = "explain_change"