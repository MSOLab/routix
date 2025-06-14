from collections import defaultdict


class DepthIndexTracker:
    """
    Tracks the number of method calls at each depth level in the call stack.
    """

    _depth_index: dict[int, int]
    """A dictionary that maps depth levels to their current call counts."""

    def __init__(self):
        self._depth_index = defaultdict(int)

    def next_call_count(self, depth: int) -> int:
        """
        Returns the next index value for a given depth level (starting from 1),
        and increments the internal counter.

        Args:
            depth (int): The depth level in the call stack.

        Returns:
            int: The next index for this depth level.
        """
        self._depth_index[depth] += 1
        return self._depth_index[depth]

    def reset_above_depth(self, depth: int):
        """
        Resets the call count for all depths greater than the specified depth.

        Args:
            depth (int): The depth level from which to reset counts.
        """
        to_delete = [d for d in self._depth_index if d > depth]
        for d in to_delete:
            del self._depth_index[d]


class MethodContextManager:
    """
    Manages the call stack of method names and generates hierarchical context strings
    based on depth-level indexing (rather than method name-based counting).
    """

    _call_stack: list[tuple[str, int]]
    """A stack of (method name, index) tuples representing the current call path."""

    __root: str = "ROOT"
    """A constant representing the root context name when the stack is empty."""

    @property
    def root(self) -> str:
        """
        Returns the root context name.

        Returns:
            str: The root context name.
        """
        return self.__root

    def __init__(self):
        self._call_stack = []
        """Initializes an empty call stack."""
        self._depth_tracker = DepthIndexTracker()
        """Initializes a tracker to assign unique indices per depth level."""

    def push(self, name: str):
        """
        Pushes a method name onto the call stack, assigning it an index based on depth.

        Args:
            name (str): The method name to push onto the call stack.
        """
        depth = len(self._call_stack)
        call_count = self._depth_tracker.next_call_count(depth + 1)
        self._call_stack.append((name, call_count))

    def pop(self) -> str:
        """
        Pops the top method name from the call stack.

        Returns:
            str: The method name that was popped.
                 If the stack is empty, returns the root context name.
        """
        if not self._call_stack:
            return self.__root
        popped = self._call_stack.pop()
        self._depth_tracker.reset_above_depth(len(self._call_stack) + 1)
        return popped[0]

    def peek(self) -> str:
        """
        Peeks at the current (top) method name on the call stack without removing it.

        Returns:
            str: The top method name, or the root context name if the stack is empty.
        """
        return self._call_stack[-1][0] if self._call_stack else self.__root

    @property
    def context_of_current_method(self) -> str:
        """
        Builds a hierarchical context string based on the current call stack.

        The format is "index-name.index-name..." from root to the current depth.

        Returns:
            str: The constructed context string.
                 If the stack is empty, returns the root context name.
        """
        return (
            ".".join(f"{index}-{name}" for name, index in self._call_stack)
            if self._call_stack
            else self.__root
        )
