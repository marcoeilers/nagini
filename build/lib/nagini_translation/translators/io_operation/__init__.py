"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""
This module contains code responsible for translating IO operations.

Translation of IO Existential Variables
=======================================

VeriFast has ``?a`` syntax which is essentially an assignment expression
that allows to link IO operations in contracts. However, neither Python,
nor Silver has assignment expressions.

``IOExists`` is a special construct that allows to define IO existential
variables (class ``PythonIOExistentialVar``) that can be used for
linking IO operations in contracts. For example::

    def read_int(t1: Place) -> Tuple[Place, int]:
        IOExists = lambda t2, value: (
            Requires(
                token(t1) and
                read_int_io(t1, value, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()[0] and
                value == Result()[1]
            )
        )   # type: Callable[[Place, int], Tuple[bool, bool]]

Here ``t2`` and ``value`` are IO existential variables. Unlike normal
variables, existential variables are not created as variables on the
Silver level, but instead they are replaced with their definitions. A
definition of the existential variable is its first mention in a
contract, which must be one of:

1.  **IO operation's result.** In this case the definition of the
    existential variable is IO operation's getter. For example,
    ``read_int_io(t1, value, t2)`` in the example above defines
    ``value`` and ``t2``. As a result, in all subsequent uses
    ``value`` is translated to ``get__read_int_io__value(t1)`` and
    ``t2`` to ``get__read_int_io__t_post(t1)``.
2.  **Equality with already defined value.** The only accepted syntax in
    this case is ``existential_variable == something``. For example,
    ``2 == value`` would give an error because existential variable is
    on the right hand side. In this case, the definition of the
    existential variable is the right hand side of the equality.

    .. note::

        The defining equality must be a top level assertion because the
        following contract::

            (
                value == x.f
                if b
                else value == x.g
            ) and
            value == 2

        would be translated to:

        .. code-block:: silver

            (b ? True : x.f == x.g) && x.f == 2

        which is probably not what a programmer intended.

------------
Known Issues
------------

Heap Dependent Getters
----------------------

If one of the IO operation arguments is a field, then the emitted
getters are heap dependent. For example, the value of place ``t2``
depends on field ``self.int_field``::

    write_int_io(t1, self.int_field, t2)

This has interesting consequences such as:

1.  Postcondition must have access to ``self.int_field``, otherwise
    ``t2`` getter is not framed::

        IOExists1(Place)(
            lambda t2: (
            Requires(
                Acc(self.int_field) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                t2 == Result() # ERROR: not.wellformed:insufficient.permission
            ),
            )
        )

2.  Similarly, if defining getter is heap dependent and guarded by
    conditional, other branch fails well-formedness check::

        Requires(
            token(t1) and
            (
                Acc(self.int_field1, 1/2) and
                write_int_io(t1, self.int_field1, t2)
            ) if b else (
                Acc(self.int_field2, 1/2) and
                write_int_io(t1, self.int_field2, t2)
                               # ERROR: not.wellformed:insufficient.permission
            )
        ),

3.  If defining getter is changed from heap independent in overridden
    method to heap dependent in a overriding method and overriding
    method takes all permission to the heap location, the behavioural
    subtyping check fails because information about getter equality is
    havocked.

Currently, the plan is to ignore the problem because storing arguments
in fields should not be too common in practise:

1.  The Petri Net provided at the entry point cannot depend on the heap
    – otherwise also permissions has to be provided at the entry
    point, which does not make much sense.
2.  It is not allowed to have permissions in non-basic IO operation
    definitions.

.. todo:: Vytautas

    Things to investigate:

    1.  Does wrapping getters in ``old`` in postcondition solve the
        issue of having to provide permissions to fields in
        postcondition?
"""


from nagini_translation.translators.io_operation.interface import (
    IOOperationTranslator,
)
