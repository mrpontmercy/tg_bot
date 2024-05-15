from dataclasses import dataclass
from datetime import datetime


@dataclass
class Lesson:
    title: str
    start_datetime: str
    teacher_name: str


# def get_all_lessons():
