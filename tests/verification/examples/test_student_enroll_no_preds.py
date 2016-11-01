from py2viper_contracts.contracts import *
from py2viper_contracts.io import *
from typing import *


class Student:
    def __init__(self, name: str) -> None:
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        Ensures(Acc(self.courses) and Acc(list_pred(self.courses)))  # type: ignore
        self.name = name
        self.courses = []  # type: List[str]

    #:: Label(L1)
    def enroll(self, course_name: str) -> None:
        Requires(Acc(self.courses, 1/2) and Acc(list_pred(self.courses)))
        Ensures(Acc(self.courses, 1/2) and Acc(list_pred(self.courses)) and course_name in self.courses)

        self.courses.append(course_name)


class GradStudent(Student):
    def __init__(self, name: str, advisor_name: str) -> None:
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        Ensures(Acc(self.courses) and Acc(list_pred(self.courses)))  # type: ignore
        Ensures(Acc(self.advisor_name) and self.advisor_name == advisor_name)  # type: ignore
        Ensures(Acc(self.research_only) and self.research_only)  # type: ignore
        super().__init__(name)
        self.advisor_name = advisor_name
        self.research_only = True

    #:: ExpectedOutput(call.precondition:insufficient.permission,L1)
    def enroll(self, course_name: str) -> None:
        Requires(Acc(self.courses, 1/2) and Acc(list_pred(self.courses)))
        Requires(Acc(self.research_only))
        Ensures(Acc(self.courses, 1/2) and Acc(list_pred(self.courses)) and course_name in self.courses)
        Ensures(Acc(self.research_only) and not self.research_only)

        self.courses.append(course_name)
        self.research_only = False


def enroll_all(students: Set[Student], course_name: str) -> None:
    Requires(Acc(set_pred(students), 2/3) and
             Forall(students, lambda s: (Acc(s.courses) and Acc(list_pred(s.courses)), [])))
    Ensures(Acc(set_pred(students), 2/3) and
            Forall(students, lambda s: (Acc(s.courses) and Acc(list_pred(s.courses)) and course_name in s.courses, [])))
    for student in students:
        Invariant(Forall(students, lambda s: (Acc(s.courses) and Acc(list_pred(s.courses)), [])))
        Invariant(Forall(Previous(student), lambda s: (course_name in s.courses, [])))
        student.enroll(course_name)


def client() -> None:
    s1 = Student('Marc')
    enroll_all({s1}, 'COOP')
    assert 'COOP' in s1.courses
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 'SAE' in s1.courses
