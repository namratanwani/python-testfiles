# import sys
from collections import deque
from copy import deepcopy
from queue import PriorityQueue

# import time
# from collections import Counter


class Node:
    def __init__(self, state, depth=0, moves=None, optimizer=0):
        """
        Takes in state, depth, moves, and optimizer parameters and creates a Node
        object representing that state with specified depth in a search tree, and
        stores the movies list for reaching that state from the initial state.

        Args:
            state (`object`.): initial state of the puzzle that is being analyzed
                and documented, which is passed to the function as an object
                containing the state's information.
                
                		- State: This is a sequence of length `self.size` representing
                the current state of the puzzle.
                		- Depth: This is an integer indicating the depth of the state
                in the search tree, where the root node has depth 0.
                		- Moves: If provided, this is a list of moves that were used to
                reach this state from the initial state. If not provided, this
                list will be empty.
                		- Optimizer: This is an integer indicating the optimization
                algorithm used for UCS (Upper Confidence Bound) calculations, with
                valid values of 0 (Manhattan Distance), 1 (Hamming Distance), and
                2 (a combination of 0 and 1).
            depth (int): 0-based index of the current state in the space search
                tree, indicating the position of the node in the tree structure.
            moves (list): 1-dimensional move vector from the initial state to the
                provided state, allowing for efficient computation of distances
                and heuristics in the UCS algorithm.
            optimizer (int): used for UCS (Union-Find algorithm) in Puzzle Solver,
                with possible values of 0 - Manhattan Distance, 1 - Hamming Distance
                and 2 - Combination of 0 and 1.

        """
        self.state = state
        self.size = len(state)
        self.depth = depth
        self.optimizer = optimizer
        if moves is None:
            self.moves = list()
        else:
            self.moves = moves

    def getAvailableActions(self):
        """
        Generates an action list based on the current state matrix of size `self.size
        x self.size`. The function checks each cell of the matrix and recursively
        calls itself for cells that have a value of 0, taking into account the row
        and column index of the cell. It returns an array of actions that correspond
        to valid movements in the game.

        Returns:
            list: an array of integers representing the available actions for the
            current state of the game.

        """
        action = list()
        for i in range(self.size):
            for j in range(self.size):
                if self.state[i][j] == 0:
                    if i > 0:
                        action.append(2)
                    if j > 0:
                        action.append(0)
                    if i < self.size - 1:
                        action.append(3)
                    if j < self.size - 1:
                        action.append(1)
                    return action
        return action

    def getResultFromAction(self, action):
        """
        Takes a game state and an action as input, generates a new state by applying
        the given action, and returns a `Node` object representing the new state
        with its updated moves.

        Args:
            action (int): 1-based integer input value that specifies which cell
                to move the game piece on the board, and the function determines
                the new state of the game board based on the selected action and
                the current state of the board.

        Returns:
            Node: a new node object representing the updated state of the game
            after a player has taken an action.
            
            		- `Node`: This is the type of object returned by the function, which
            represents a state in the game. It has several attributes, including
            `state`, `depth`, `moves`, and `optimizer`.
            		+ `state`: This is an array of size `self.size x self.size` representing
            the current state of the game.
            		+ `depth`: This is an integer representing the depth of the node in
            the game tree.
            		+ `moves`: This is a list of integers representing the possible moves
            that can be taken from this node. The values in the list correspond
            to the actions passed as input to the function.
            		+ `optimizer`: This is an instance of an optimizer class, which is
            used to search for the best move.
            		- None: This is the value returned when no valid moves are found
            from the current state.

        """
        newstate = deepcopy(self.state)
        newMoves = deepcopy(self.moves)
        for i in range(self.size):
            for j in range(self.size):
                if newstate[i][j] == 0:
                    if action == 2:
                        newstate[i][j], newstate[i - 1][j] = (
                            newstate[i - 1][j],
                            newstate[i][j],
                        )
                        newMoves.append(2)
                        return Node(
                            newstate,
                            depth=self.depth + 1,
                            moves=newMoves,
                            optimizer=self.optimizer,
                        )
                    if action == 3:
                        newstate[i][j], newstate[i + 1][j] = (
                            newstate[i + 1][j],
                            newstate[i][j],
                        )
                        newMoves.append(3)
                        return Node(
                            newstate,
                            depth=self.depth + 1,
                            moves=newMoves,
                            optimizer=self.optimizer,
                        )
                    if action == 0:
                        newstate[i][j], newstate[i][j - 1] = (
                            newstate[i][j - 1],
                            newstate[i][j],
                        )
                        newMoves.append(0)
                        return Node(
                            newstate,
                            depth=self.depth + 1,
                            moves=newMoves,
                            optimizer=self.optimizer,
                        )
                    if action == 1:
                        newstate[i][j], newstate[i][j + 1] = (
                            newstate[i][j + 1],
                            newstate[i][j],
                        )
                        newMoves.append(1)
                        return Node(
                            newstate,
                            depth=self.depth + 1,
                            moves=newMoves,
                            optimizer=self.optimizer,
                        )
        return None

    def isGoalState(self):
        """
        Checks if an array represents a goal state by iterating through each cell
        and comparing it to the previous cells, using the equation `(i*size + j +
        1)`. If any cell does not match, the function returns `False`. If all cells
        match, the function returns `True`.

        Returns:
            bool: a boolean value indicating whether the provided state is a goal
            state or not.

        """
        for i in range(self.size):
            for j in range(self.size):
                if i == j and j == self.size - 1:
                    continue
                if self.state[i][j] != (i) * self.size + (j + 1):
                    return False
        return True

    def getManhattanDistance(self):
        """
        Computes the Manhattan distance between the current state and a goal state
        represented as an array of size self.size x self.size, by iterating over
        the pixels and computing the absolute differences between their values and
        the goal state value.

        Returns:
            int: the Manhattan distance between the current state and the goal state.

        """
        ans = 0
        for i in range(self.size):
            for j in range(self.size):
                if self.state[i][j] != 0:
                    ans = (
                        ans
                        + abs((self.state[i][j] - 1) % self.size - j)
                        + abs((self.state[i][j] - 1) // self.size - i)
                    )

        return ans

    def getHammingDistance(self):
        """
        Computes the Hamming distance of a bitstring by iterating over its elements
        and counting the number of positions where the bits differ from their
        expected values.

        Returns:
            int: the number of positions where two strings of length `self.size`
            differ.

        """
        ans = 0
        for i in range(self.size):
            for j in range(self.size):
                if self.state[i][j] != 0 and self.state[i][j] != i * 3 + (j + 1):
                    ans = ans + 1
        return ans

    def __hash__(self):
        """
        Flattens the state of an object into a tuple and returns its hash value
        using the `hash()` function.

        Returns:
            int: a hash value representing the concatenation of the flat states
            of all sub-objects within the object.

        """
        flatState = [j for sub in self.state for j in sub]
        flatState = tuple(flatState)
        return hash(flatState)

    def __gt__(self, other):
        """
        Compares two instances of a class and determines if one is better than the
        other based on their optimizer values and corresponding distance metrics
        (Manhattan or Hamming).

        Args:
            other (instance of `self.Class`.): 2D vector that the current vector
                is being compared to.
                
                		- `optimizer`: an integer attribute representing the optimizer
                used in the comparison (0, 1, or 2)

        Returns:
            bool: a boolean indicating whether the object's optimization score is
            greater than the other object's score.

        """
        if self.optimizer == 0:
            if self.getManhattanDistance() > other.getManhattanDistance():
                return True
            else:
                return False
        elif self.optimizer == 1:
            if self.getHammingDistance() > other.getHammingDistance():
                return True
            else:
                return False
        elif self.optimizer == 2:
            if (
                self.getHammingDistance() + self.getManhattanDistance()
                > other.getHammingDistance() + self.getManhattanDistance()
            ):
                return True
            else:
                return False
        return True

    def __ge__(self, other):
        """
        Compares two objects and returns `True` if one is greater than or equal
        to the other, based on their optimization values and Manhattan or Hamming
        distances.

        Args:
            other (`Algorithm` object in this code.): 2D point or rectangle used
                for comparison with the current point or rectangle.
                
                		- `other`: This is the other instance to be compared with the
                current instance. It can have any of the three optimizers (0, 1,
                or 2) set.
                		- `optimizer`: A variable that determines the comparison strategy
                used in the function. It can take on values of 0, 1, or 2.

        Returns:
            bool: a boolean value indicating whether the distance between the two
            objects is greater than or equal to the distance between them.

        """
        if self.optimizer == 0:
            if self.getManhattanDistance() >= other.getManhattanDistance():
                return True
            else:
                return False
        elif self.optimizer == 1:
            if self.getHammingDistance() >= other.getHammingDistance():
                return True
            else:
                return False
        elif self.optimizer == 2:
            if (
                self.getHammingDistance() + self.getManhattanDistance()
                >= other.getHammingDistance() + self.getManhattanDistance()
            ):
                return True
            else:
                return False
        return True

    def __lt__(self, other):
        """
        Compares two `Optimization` objects based on their optimization score and
        manhattan distance. It returns `True` if the first object is better, and
        `False` otherwise.

        Args:
            other (instance/objects of the class or object type used as a parameter.):
                2D vector that is being compared to the current vector in the given
                optimization level.
                
                		- `optimizer`: An integer value representing the optimizer type
                (0, 1, or 2) passed to the function.

        Returns:
            bool: a boolean value indicating whether the current instance is less
            than the provided other instance based on their respective optimizer
            values and distance metrics.

        """
        if self.optimizer == 0:
            if self.getManhattanDistance() < other.getManhattanDistance():
                return True
            else:
                return False
        elif self.optimizer == 1:
            if self.getHammingDistance() < other.getHammingDistance():
                return True
            else:
                return False
        elif self.optimizer == 2:
            if (
                self.getHammingDistance() + self.getManhattanDistance()
                < other.getHammingDistance() + self.getManhattanDistance()
            ):
                return True
            else:
                return False
        return True

    def __le__(self, other):
        """
        Compares two optimization objects based on their distance metrics (Manhattan
        or Hamming). It returns `True` if the distance metric of the current object
        is smaller, and `False` otherwise.

        Args:
            other (int): 2nd sequence in the sequence distance comparison operation
                conducted by the function.

        Returns:
            bool: a boolean indicating whether the instance is less than or equal
            to the other instance.

        """
        if self.optimizer == 0:
            if self.getManhattanDistance() <= other.getManhattanDistance():
                return True
            else:
                return False
        elif self.optimizer == 1:
            if self.getHammingDistance() <= other.getHammingDistance():
                return True
            else:
                return False
        elif self.optimizer == 2:
            if (
                self.getHammingDistance() + self.getManhattanDistance()
                <= other.getHammingDistance() + self.getManhattanDistance()
            ):
                return True
            else:
                return False
        return True

    def __eq__(self, other):
        """
        Compares two Optimizer objects and returns True if their optimization types
        match and their distances are equal, otherwise it returns False.

        Args:
            other (instance/object of the `Algorithm` class, or any other object
                that supports the `__eq__()` method.): object being compared to
                the current object in the `eq` method.
                
                		- If `self.optimizer` is 0, then `other.getManhattanDistance()`
                represents the Manhattan distance between the two inputs.
                		- If `self.optimizer` is 1, then `other.getHammingDistance()`
                represents the Hamming distance between the two inputs.
                		- If `self.optimizer` is 2, then the sum of the Manhattan and
                Hamming distances between the two inputs represents the overall
                distance between them.

        Returns:
            bool: a boolean value indicating whether the given object and another
            object are equal based on their optimizer values and distance metrics.

        """
        if self.optimizer == 0:
            if self.getManhattanDistance() == other.getManhattanDistance():
                return True
            else:
                return False
        elif self.optimizer == 1:
            if self.getHammingDistance() == other.getHammingDistance():
                return True
            else:
                return False
        elif self.optimizer == 2:
            if (
                self.getHammingDistance() + self.getManhattanDistance()
                == other.getHammingDistance() + self.getManhattanDistance()
            ):
                return True
            else:
                return False
        return True


class Solver:
    def __init__(self, state):
        self.state = state

    def isSolvable(self):
        """
        Evaluates the solvability of a state by counting the number of inversions
        in the flat state, and returning `True` if the count is even and `False`
        otherwise.

        Returns:
            int: a boolean indicating whether the state is solvable.

        """
        flatState = [j for sub in self.state for j in sub]
        inversions = 0
        for i in range(len(flatState) - 1):
            for j in range(i + 1, len(flatState)):
                if (
                    flatState[i] != 0
                    and flatState[j] != 0
                    and flatState[i] > flatState[j]
                ):
                    inversions = inversions + 1
        return inversions % 2 == 0

    def breadth_first_search(self):
        """
        Takes a state as input and returns a list of moves to solve it or an
        indication that the state is unsolvable. It does this by iteratively
        exploring the state from a given starting node using depth-first search,
        storing the visited states in a list called `closed`, and returning the
        list of moves when the goal state is reached.

        Returns:
            list: a pair of tuples containing the list of moves and the depth of
            the shortest solution.

        """
        if self.isSolvable() == False:
            return (None, None)

        closed = list()
        q = deque()
        q.append(Node(state=self.state, depth=0))
        while q:
            node = q.popleft()

            if node.isGoalState():
                return (node.moves, len(closed))
            if node.state not in closed:
                closed.append(node.state)
                for action in node.getAvailableActions():
                    q.append(node.getResultFromAction(action))

        return (None, None)

    def depth_first_search(self):
        """
        Solves a state by applying actions to reach the goal state, maintaining a
        list of closed states and a queue of nodes to explore. It returns a list
        of moves and the depth reached.

        Returns:
            list: a tuple of two elements: `(List of moves to solve the state,
            Integer indicating the number of closed states)`

        """
        if self.isSolvable() == False:
            return (None, None)
        closed = list()
        q = list()
        q.append(Node(state=self.state, depth=0))
        while q:
            node = q.pop()
            if node.isGoalState():
                return (node.moves, len(closed))
            if node.state not in closed:
                closed.append(node.state)
                for action in node.getAvailableActions():
                    q.append(node.getResultFromAction(action))

        return (None, None)

    def uniform_cost_search(self, optimizer=0):
        """
        Determines whether a state can be solved and generates moves to reach a
        goal state if solvable, using a priority queue to efficiently explore the
        search space.

        Args:
            optimizer (int): 0-based index of an optimizer class to use for
                generating moves to solve the state, where the default is no optimizer.

        Returns:
            list: a list of moves to solve the given state, or `None` if the state
            is unsolvable.

        """
        if self.isSolvable() == False:
            return (None, None)
        closed = list()
        q = PriorityQueue()
        q.put(Node(state=self.state, depth=0, optimizer=optimizer))
        while q:
            node = q.get()
            if node.isGoalState():
                return (node.moves, len(closed))
            if node.state not in closed:
                closed.append(node.state)
                for action in node.getAvailableActions():
                    q.put(node.getResultFromAction(action))

        return (None, None)

    def a_star(self):
        """
        Takes in a `State` object and an `Optimizer`, it returns a list of moves
        to reach the goal state or `None` if unsolvable, by iteratively exploring
        the node's neighborhood using a priority queue and storing the manhattan
        distance and corresponding nodes in a dictionary.

        Returns:
            list: a list of moves to solve the state or `None` if unsolvable.

        """
        if self.isSolvable() == False:
            return (None, None)
        closed = dict()
        q = PriorityQueue()
        node = Node(state=self.state, depth=0)
        q.put((node.getManhattanDistance(), node))
        while q:
            dist, node = q.get()
            closed[node] = dist
            if node.isGoalState():
                return (node.moves, len(closed))
            for action in node.getAvailableActions():
                nextNode = node.getResultFromAction(action)
                nextDist = nextNode.getManhattanDistance()
                if (
                    nextNode not in closed
                    or nextNode.depth + nextDist < closed[nextNode]
                ):
                    q.put((nextNode.depth + nextDist, nextNode))
        return (None, None)

#testing comment
def toWord(action):
    """
    Takes a list of moves as input and converts them to their corresponding Word
    actions (Left, Right, Top, or Bottom).

    Args:
        action (int): 0-indexed move instruction, with values of 0 for left, 1 for
            right, 2 for top, and 3 for bottom, which determines the corresponding
            word to return.

    Returns:
        list: a list of moves translated from actions to words.

    """
    if action == 0:
        return "Left"
    if action == 1:
        return "Right"
    if action == 2:
        return "Top"
    if action == 3:
        return "Bottom"


# initialState =  [[1,8,4],[3,6,0],[2,7,5]]
# # [[1,2,3],[4,5,6],[0,7,8]]
# # [[6,8,5],[2,3,4],[1,0,7]]
# # [[13,11,10,7],[6,0,15,2],[14,1,8,12],[5,3,4,9]]
# # [[8,2,3],[4,6,5],[7,8,0]]
# solver = Solver(initialState)
# print("Initial State:- {}".format(initialState))
# n = Node(state=initialState,depth=0)

# print('-------------------------A Star--------------------------------')
# startTime = time.time()
# moves,nodesGenerated = solver.a_star()
# endTime = time.time()
# if moves is None:
#     print("Given State is Unsolvable!")
# else:
#     wordMoves = list(map(toWord,moves))
#     print("Nodes Generated:- {}".format(nodesGenerated))
#     print("No. of moves:- {}".format(len(moves)))
#     print("Required Moves:- {}".format(wordMoves))
#     print("Execution Time:- {:.2f} ms".format((endTime-startTime)*1000))


# print('-------------------------UCS--------------------------------')
# startTime = time.time()
# moves,nodesGenerated = solver.uniform_cost_search()
# endTime = time.time()
# if moves is None:
#     print("Given State is Unsolvable!")
# else:
#     wordMoves = list(map(toWord,moves))
#     print("Nodes Generated:- {}".format(nodesGenerated))
#     print("No. of moves:- {}".format(len(moves)))
#     print("Required Moves:- {}".format(wordMoves))
#     print("Execution Time:- {:.2f} ms".format((endTime-startTime)*1000))


# print('-------------------------BFS--------------------------------')
# startTime = time.time()
# moves,nodesGenerated = (solver.breadth_first_search())
# endTime = time.time()
# if moves is None:
#     print("Given State is Unsolvable!")
# else:
#     wordMoves = list(map(toWord,moves))
#     print("Nodes Generated:- {}".format(nodesGenerated))
#     print("No. of moves:- {}".format(len(moves)))
#     print("Required Moves:- {}".format(wordMoves))
#     print("Execution Time:- {:.2f} ms".format((endTime-startTime)*1000))


# print('-------------------------DFS--------------------------------')
# startTime = time.time()
# moves,nodesGenerated = (solver.depth_first_search())
# endTime = time.time()
# if moves is None:
#     print("Given State is Unsolvable!")
# else:
#     wordMoves = list(map(toWord,moves))
#     print("Nodes Generated:- {}".format(nodesGenerated))
#     print("No. of moves:- {}".format(len(moves)))
#     print("Required Moves:- {}".format(wordMoves))
#     print("Execution Time:- {:.2f} ms".format((endTime-startTime)*1000))