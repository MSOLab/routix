import unittest

from ortools.sat.python.cp_model import LinearExpr

from clad.custom_cp_model import CustomCpModel


class TestCustomCpModel(unittest.TestCase):
    def setUp(self):
        """Set up a CustomCpModel instance for testing."""
        self.model = CustomCpModel()

    def test_change_domain(self):
        """Test the change_domain method."""
        var = self.model.NewIntVar(0, 10, "x")
        self.model.change_domain(var, [5, 15])
        self.assertEqual(var.Proto().domain, [5, 15])

    def test_add_linear_constraint_fast(self):
        """Test the add_linear_constraint_fast method."""
        x = self.model.NewIntVar(0, 10, "x")
        y = self.model.NewIntVar(0, 10, "y")
        self.model.add_linear_constraint_fast([x, y], [1, 2], (5, 20))
        constraints = self.model._CpModel__model.constraints
        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0].linear.vars, [x.Index(), y.Index()])
        self.assertEqual(constraints[0].linear.coeffs, [1, 2])
        self.assertEqual(constraints[0].linear.domain, [5, 20])

    def test_add_temporal_linear_constraints(self):
        """Test the add_temporal_linear_constraints method."""
        x = self.model.NewIntVar(0, 10, "x")
        y = self.model.NewIntVar(0, 10, "y")
        args_list = [([x, y], [1, 2], (5, 20)), ([x], [3], (0, 10))]
        self.model.add_temporal_linear_constraints(args_list)
        constraints = self.model._CpModel__model.constraints
        self.assertEqual(len(constraints), 2)
        self.assertEqual(self.model.idx_added_constraints, [(0, 2)])

    def test_add_temporal_abs_equality_constraints(self):
        """Test the add_temporal_abs_equality_constraints method."""
        x = self.model.NewIntVar(0, 10, "x")
        expr = LinearExpr.Sum([x])
        args_list = [(x, expr)]
        self.model.add_temporal_abs_equality_constraints(args_list)
        constraints = self.model._CpModel__model.constraints
        self.assertEqual(len(constraints), 1)
        self.assertEqual(self.model.idx_added_constraints, [(0, 1)])

    def test_delete_constraints(self):
        """Test the delete_constraints method."""
        x = self.model.NewIntVar(0, 10, "x")
        y = self.model.NewIntVar(0, 10, "y")
        self.model.add_linear_constraint_fast([x, y], [1, 2], (5, 20))
        self.model.delete_constraints(0, 1)
        constraints = self.model._CpModel__model.constraints
        self.assertEqual(len(constraints), 0)

    def test_delete_added_constraints(self):
        """Test the delete_added_constraints method."""
        x = self.model.NewIntVar(0, 10, "x")
        y = self.model.NewIntVar(0, 10, "y")
        self.model.add_temporal_linear_constraints([([x, y], [1, 2], (5, 20))])
        self.model.delete_added_constraints()
        constraints = self.model._CpModel__model.constraints
        self.assertEqual(len(constraints), 0)
        self.assertEqual(len(self.model.added_constraints), 0)
        self.assertEqual(len(self.model.idx_added_constraints), 0)


if __name__ == "__main__":
    unittest.main()
