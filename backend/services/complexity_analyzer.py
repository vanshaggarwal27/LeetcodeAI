import ast


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.sorting = False
        self.hash_usage = False
        self.recursion = False
        self.function_names = set()

    # Detect function definitions
    def visit_FunctionDef(self, node):
        self.function_names.add(node.name)
        self.generic_visit(node)

    # Detect nested for loops
    def visit_For(self, node):
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        self.generic_visit(node)

        self.loop_depth -= 1

    # Detect nested while loops
    def visit_While(self, node):
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        self.generic_visit(node)

        self.loop_depth -= 1

    # Detect sorting + recursion
    def visit_Call(self, node):
        # Detect sorted()
        if isinstance(node.func, ast.Name):
            if node.func.id == "sorted":
                self.sorting = True

            # Detect recursion
            if node.func.id in self.function_names:
                self.recursion = True

        # Detect list.sort()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "sort":
                self.sorting = True

        self.generic_visit(node)

    # Detect dictionary usage
    def visit_Dict(self, node):
        self.hash_usage = True
        self.generic_visit(node)

    # Detect set usage
    def visit_Set(self, node):
        self.hash_usage = True
        self.generic_visit(node)


def analyze_code(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "error": "Invalid Python syntax"
        }

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    time_complexity = "O(n)"
    space_complexity = "O(1)"
    pattern = "Basic Iteration"
    suggestions = []

    # Nested loops
    if visitor.max_loop_depth >= 2:
        time_complexity = "O(n²)"
        pattern = "Nested Loop"
        suggestions.append(
            "Consider reducing nested loop operations for better performance."
        )

    # Sorting
    elif visitor.sorting:
        time_complexity = "O(n log n)"
        pattern = "Sorting"
        suggestions.append(
            "Sorting operation detected which increases time complexity."
        )

    # Recursion
    elif visitor.recursion:
        pattern = "Recursion"
        suggestions.append(
            "Consider memoization if overlapping recursive calls exist."
        )

    # Hash-based structures
    if visitor.hash_usage:
        suggestions.append(
            "Efficient hash-based data structure detected."
        )

    # Default suggestion
    if not suggestions:
        suggestions.append(
            "Code structure looks efficient."
        )

    return {
        "timeComplexity": time_complexity,
        "spaceComplexity": space_complexity,
        "pattern": pattern,
        "suggestions": suggestions,
    }
