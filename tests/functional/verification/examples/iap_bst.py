# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from typing import Optional
from nagini_contracts.contracts import *


class TreeNode:
    def __init__(self, key: int, val: str, left:'TreeNode'=None,
                 right:'TreeNode'=None, parent:'TreeNode'=None) -> None:
        self.key = key
        self.payload = val
        self.leftChild = left
        self.rightChild = right
        self.parent = parent
        Ensures(Acc(self.key) and self.key is key and
                Acc(self.payload) and self.payload is val and
                Acc(self.leftChild) and self.leftChild is left and
                Acc(self.rightChild) and self.rightChild is right and
                Acc(self.parent) and self.parent is parent)

    @Pure
    def hasLeftChild(self) -> Optional['TreeNode']:
        Requires(Acc(self.leftChild))
        return self.leftChild

    @Pure
    def hasRightChild(self) -> Optional['TreeNode']:
        Requires(Acc(self.rightChild))
        return self.rightChild

    @Pure
    def isRoot(self) -> bool:
        Requires(tree(self))
        return Unfolding(tree(self), not self.parent)

    @Pure
    def isLeaf(self) -> bool:
        Requires(tree(self))
        return Unfolding(tree(self), not (self.rightChild or self.leftChild))

    @Pure
    def hasAnyChildren(self) -> Optional['TreeNode']:
        Requires(tree(self))
        return Unfolding(tree(self), self.rightChild or self.leftChild)

    @Pure
    def hasBothChildren(self) -> Optional['TreeNode']:
        Requires(tree(self))
        return Unfolding(tree(self), self.rightChild and self.leftChild)


@Predicate
def tree(n : TreeNode) -> bool:
    return (Acc(n.key) and Acc(n.payload) and Acc(n.leftChild) and Acc(n.rightChild) and
            Acc(n.parent) and
            Implies(n.leftChild is not None, tree(n.leftChild) and
                    getParent(n.leftChild) is n) and
            Implies(n.rightChild is not None, tree(n.rightChild) and
                    getParent(n.rightChild) is n))


@Pure
def sorted(n: TreeNode, upper: Optional[int], lower: Optional[int]) -> bool:
    Requires(tree(n))
    return (Unfolding(tree(n),
            Implies(upper is not None, n.key < upper) and
            Implies(lower is not None, n.key > lower) and
            Implies(n.leftChild is not None, sorted(n.leftChild, n.key, lower)) and
            Implies(n.rightChild is not None, sorted(n.rightChild, upper, n.key))))

@Pure
def getParent(node: TreeNode) -> Optional['TreeNode']:
    Requires(tree(node))
    return Unfolding(tree(node), node.parent)


class BinarySearchTree:

    def __init__(self) -> None:
        self.root = None  # type: Optional[TreeNode]
        self.size = 0
        Fold(bst(self))
        Ensures(bst(self))

    def put(self, key: int, val: str) -> None:
        Requires(bst(self))
        Ensures(bst(self))
        Unfold(bst(self))
        if self.root:
            increased_size = self._put(key, val, self.root, None, None)
        else:
            self.root = TreeNode(key,val)
            Fold(tree(self.root))
            increased_size = True
        if increased_size:
            self.size = self.size + 1
        Fold(bst(self))

    def _put(self, key: int, val: str, currentNode: TreeNode,
             upper: Optional[int], lower: Optional[int]) -> bool:
        Requires(tree(currentNode) and sorted(currentNode, upper, lower))
        Requires(Implies(upper is not None, key < upper))
        Requires(Implies(lower is not None, key > lower))
        Ensures(tree(currentNode) and sorted(currentNode, upper, lower))
        Ensures(getParent(currentNode) is
                Old(getParent(currentNode)))
        Unfold(tree(currentNode))
        res = True
        if key < currentNode.key:
            if currentNode.hasLeftChild():
                res = self._put(key, val, currentNode.leftChild, currentNode.key, lower)
            else:
                currentNode.leftChild = TreeNode(key, val, parent=currentNode)
                Fold(tree(currentNode.leftChild))
        elif key > currentNode.key:
            if currentNode.hasRightChild():
                res = self._put(key, val, currentNode.rightChild, upper, currentNode.key)
            else:
                currentNode.rightChild = TreeNode(key, val, parent=currentNode)
                Fold(tree(currentNode.rightChild))
        else:
            currentNode.payload = val
            res = False
        Fold(tree(currentNode))
        return res

    def __setitem__(self, k: int, v: str) -> None:
        Requires(bst(self))
        Ensures(bst(self))
        self.put(k,v)

    def get(self, key: int) -> Optional[str]:
        Requires(Acc(bst(self)))
        Ensures(Acc(bst(self)))
        Unfold(bst(self))
        if self.root:
            res = self._get(key, self.root, 2)
            Fold(bst(self))
            return res
        else:
            Fold(bst(self))
            return None

    def _get(self, key: int, currentNode: Optional[TreeNode], perm: int) -> Optional[str]:
        Requires(perm > 0)
        Requires(Implies(currentNode is not None, Acc(tree(currentNode), 1/perm)))
        Ensures(Implies(currentNode is not None, Acc(tree(currentNode), 1/perm)))
        if not currentNode:
            return None
        Unfold(Acc(tree(currentNode), 1/perm))
        if currentNode.key == key:
            res = currentNode.payload
        elif key < currentNode.key:
            res = self._get(key, currentNode.leftChild, perm * 2)
        else:
            res = self._get(key, currentNode.rightChild, perm * 2)
        Fold(Acc(tree(currentNode), 1/perm))
        return res

    def __getitem__(self, key: int) -> Optional[str]:
        Requires(Acc(bst(self)))
        Ensures(Acc(bst(self)))
        return self.get(key)

@Predicate
def bst(t: BinarySearchTree) -> bool:
    return (Acc(t.root) and Acc(t.size) and
            Implies(t.root is not None, tree(t.root) and sorted(t.root, None, None)))


def print(o: object) -> None:
    pass


mytree = BinarySearchTree()
mytree[3]="red"
mytree[4]="blue"
mytree[6]="yellow"
mytree[2]="at"

print(mytree[6])
print(mytree[2])