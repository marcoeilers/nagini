"""
Example from "Relational Verification using Product Programs"
G. Barthe, J. M. Crespo, and C. Kunz
FM 2011
Originally from "Privacy-Sensitive Information Flow with JML"
Dufay, G., Felty, A., & Matwin, S.
International Conference on Automated Deduction 2005
"""

from typing import List, Optional

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

def check_join_and_find_employee(psi: Payroll, es: List[Employee]) -> Optional[Combined]:
    Requires(list_pred(es))
    Requires(Low(es) and Low(len(es)))
    Requires(Acc(psi.joinInd, 1/4) and Low(psi.joinInd))
    Requires(Acc(psi.PID, 1/4) and Low(psi.PID))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(es), Acc(es[i].EID, 1/4) and Low(es[i].EID)), [[es[i]]])))
    Ensures(list_pred(es))
    Ensures(Acc(psi.PID, 1/4))
    Ensures(Acc(psi.joinInd, 1/4))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(es), Acc(es[i].EID, 1/4)), [[es[i]]])))
    Ensures(Low(Result()))

    if psi.joinInd:
        j = 0
        while j < len(es):
            Invariant(list_pred(es))
            Invariant(Low(es) and Low(len(es)))
            Invariant(Acc(psi.PID, 1/8) and Low(psi.PID))
            Invariant(j >= 0 and j <= len(es) and Low(j))
            Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(es), Acc(es[i].EID, 1/4) and Low(es[i].EID)), [[es[i]]])))
            Assert(Low(es[j].EID))
            Assert(Low(psi.PID == es[j].EID))
            if psi.PID == es[j].EID:
                return Combined(psi, es[j])
            j += 1
    return None
