"""Tests for DepartmentService."""

import pytest

from apps.accounts.services import DepartmentService
from apps.core.exceptions import BusinessValidationError

from .factories import DepartmentFactory


@pytest.mark.django_db
class TestDepartmentService:
    def test_get_department_tree_returns_roots(self):
        eng = DepartmentFactory(name='Engineering')
        DepartmentFactory(name='Frontend', parent=eng)
        DepartmentFactory(name='Backend', parent=eng)
        DepartmentFactory(name='Marketing')

        tree = DepartmentService.get_department_tree()

        root_names = [node['department'].name for node in tree]
        assert 'Engineering' in root_names
        assert 'Marketing' in root_names
        assert len(tree) == 2

    def test_get_department_tree_nests_children(self):
        eng = DepartmentFactory(name='Engineering')
        DepartmentFactory(name='Frontend', parent=eng)
        DepartmentFactory(name='Backend', parent=eng)

        tree = DepartmentService.get_department_tree()
        eng_node = next(n for n in tree if n['department'].name == 'Engineering')

        child_names = [c['department'].name for c in eng_node['children']]
        assert 'Frontend' in child_names
        assert 'Backend' in child_names

    def test_get_ancestors(self):
        company = DepartmentFactory(name='Company')
        eng = DepartmentFactory(name='Engineering', parent=company)
        frontend = DepartmentFactory(name='Frontend', parent=eng)

        ancestors = DepartmentService.get_ancestors(frontend)
        ancestor_names = [a.name for a in ancestors]

        assert ancestor_names == ['Company', 'Engineering']

    def test_get_ancestors_root_returns_empty(self):
        root = DepartmentFactory(name='Root')
        assert DepartmentService.get_ancestors(root) == []

    def test_validate_parent_prevents_self_reference(self):
        dept = DepartmentFactory(name='Engineering')

        with pytest.raises(BusinessValidationError, match='own parent'):
            DepartmentService.validate_parent(dept, dept)

    def test_validate_parent_prevents_circular_reference(self):
        grandparent = DepartmentFactory(name='Company')
        parent = DepartmentFactory(name='Engineering', parent=grandparent)
        child = DepartmentFactory(name='Frontend', parent=parent)

        with pytest.raises(BusinessValidationError, match='circular'):
            DepartmentService.validate_parent(grandparent, child)

    def test_validate_parent_allows_valid_parent(self):
        dept1 = DepartmentFactory(name='Engineering')
        dept2 = DepartmentFactory(name='Marketing')

        # Should not raise
        DepartmentService.validate_parent(dept1, dept2)

    def test_validate_parent_allows_none(self):
        dept = DepartmentFactory(name='Engineering')
        DepartmentService.validate_parent(dept, None)
