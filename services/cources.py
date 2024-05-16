import csv
from dataclasses import dataclass
from pathlib import Path

from db import fetch_all


@dataclass
class Lesson:
    title: str
    time_start: str
    lecturer: str

    def to_dict(self):
        result = {
            "title": self.title,
            "time_start": self.time_start,
            "lecturer": self.lecturer,
        }

        return result

    async def get_lessons_from_db(self) -> list[dict]:
        raw_select = """SELECT title, time_start, lecturer FROM course"""
        return await fetch_all(raw_select)


def get_lessons_from_file(file_name: Path) -> list[Lesson]:
    lessons: list[Lesson] = []
    with open(file_name, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            lessons.append(
                Lesson(
                    title=row["title"],
                    time_start=row["time_start"],
                    lecturer=row["lecturer"],
                )
            )

    return lessons


async def get_lessons_from_db():
    raw_select = """SELECT title, time_start, lecturer FROM course"""
    return await fetch_all(raw_select)
