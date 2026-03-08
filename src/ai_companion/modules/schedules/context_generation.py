from datetime import datetime
from typing import Dict, Optional
from ai_companion.core.schedules import (
    FRIDAY_SCHEDULE,
    MONDAY_SCHEDULE,
    SATURDAY_SCHEDULE,
    SUNDAY_SCHEDULE,
    THURSDAY_SCHEDULE,
    TUESDAY_SCHEDULE,
    WEDNESDAY_SCHEDULE,
)
from zoneinfo import ZoneInfo

class ScheduleContextGenerator:
    """Class to generate context about Ava's current activity based on schedules"""

    SCHEDULES = {
            0: MONDAY_SCHEDULE,  # Monday
            1: TUESDAY_SCHEDULE,  # Tuesday
            2: WEDNESDAY_SCHEDULE,  # Wednesday
            3: THURSDAY_SCHEDULE,  # Thursday
            4: FRIDAY_SCHEDULE,  # Friday
            5: SATURDAY_SCHEDULE,  # Saturday
            6: SUNDAY_SCHEDULE,  # Sunday
        }

    @staticmethod
    def _parse_time_range(time_range: str) -> tuple[datetime.time, datetime.time]:
        """parse a time range string into start time and end time"""
        start_str, end_str = time_range.split('-')
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        return start_time, end_time
    
    @classmethod
    def get_currect_activity(cls) -> Optional[str]:
        """Get ava's current activity based on current time and day of week.
        
        Returns:
            str: Description of current activity, or None if no matching time slot is found
        """

        current_datetime = datetime.now(ZoneInfo("Asia/Kolkata")) # to avoid docker using UTC time.
        print(current_datetime)
        current_time = current_datetime.time()
        current_day = current_datetime.weekday()

        schedule = cls.SCHEDULES.get(current_day, {})
        print(schedule)
        for time_range, activity in schedule.items():
            start_time, end_time = cls._parse_time_range(time_range)

            if start_time > end_time:
                if current_time >= start_time or current_time <= end_time:
                    return activity
            
            else:
                if start_time <= current_time <= end_time:
                    return activity
        
        return None
    
    # currently not used, but you can comabine it as tool, so that ava can answer if user ask for her schedule on certain day
    @classmethod
    def get_schedule_for_day(cls, day: int) -> Dict[str, str]:
        """
        Get complete schedule for specific day.

        Args:
            day: Day of week as integer (0 = Monday, 6 = Sunday)
        
        Returns:
            Dict[str, str]: schedule for specified day
        """
        return cls.SCHEDULES.get(day, {})