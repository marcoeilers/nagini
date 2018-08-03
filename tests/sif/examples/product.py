"""
Example from "Relational Verification using Product Programs"
G. Barthe, J. M. Crespo, and C. Kunz
FM 2011
Originally from "Privacy-Sensitive Information Flow with JML"
Dufay, G., Felty, A., & Matwin, S.
International Conference on Automated Deduction 2005
"""

from typing import List

from nagini_contracts.contracts import *

class Payroll:
    def __init__(self, PID: int, salary: int, joinInd: bool) -> None:
        self.PID = PID
        self.salary = salary
        self.joinInd = joinInd

class Employee:
    def __init__(self, EID: int) -> None:
        self.EID = EID

class Combined:
    def __init__(self, payroll: Payroll, employee: Employee) -> None:
        self.payroll = payroll
        self.employee = employee

def check_join_and_find_employee(psi: Payroll, es: List[Employee]) -> Combined:
    Requires(list_pred(es))
    Requires(Low(es))
    Requires(Acc(psi.joinInd, 1/4) and Low(psi.joinInd))
    Requires(Acc(psi.PID, 1/4) and Low(psi.PID))
    Requires(Forall(es, lambda e: Acc(e.EID, 1/4) and Low(e.EID)))
    Ensures(list_pred(es))
    Ensures(Acc(psi.PID, 1/4))
    Ensures(Acc(psi.joinInd, 1/4))
    Ensures(Forall(es, lambda e: Acc(e.EID, 1/4)))
    Ensures(Low(Result()))

    if psi.joinInd:
        j = 0
        while j < len(es):
            Invariant(list_pred(es))
            Invariant(Acc(psi.PID, 1/8) and Low(psi.PID))
            Invariant(j >= 0 and j <= len(es) and Low(j))
            Invariant(Forall(es, lambda e: Acc(e.EID, 1/4) and Low(e.EID)))
            if psi.PID == es[j].EID:
                return Combined(psi, es[j])
            j += 1
