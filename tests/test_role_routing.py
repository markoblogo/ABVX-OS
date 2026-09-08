from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

from abvx_harness.__main__ import main
from abvx_harness.roles import list_roles, route_role


ROOT = Path(__file__).resolve().parents[1]


class ProfessionalRoleRoutingTests(unittest.TestCase):
    def test_routes_job_search_to_career_advisor(self):
        result = route_role(ROOT, "Найди подходящие вакансии и помоги подготовиться к интервью")

        self.assertEqual(result["primary_role"]["id"], "career-advisor")
        self.assertIn("вакансии", result["primary_role"]["matched_triggers"])
        self.assertEqual(result["authority_effect"], "none")

    def test_routes_cross_role_book_work_with_research_support(self):
        result = route_role(ROOT, "Исследуй рынок Amazon, затем помоги написать книгу")

        self.assertEqual(result["primary_role"]["id"], "researcher")
        self.assertIn("writer", [role["id"] for role in result["supporting_roles"]])

    def test_routes_architecture_and_implementation_to_two_engineering_roles(self):
        result = route_role(ROOT, "Спроектируй архитектуру сервиса и реализуй изменения в коде")

        self.assertEqual(result["primary_role"]["id"], "software-architect")
        self.assertIn("senior-software-engineer", [role["id"] for role in result["supporting_roles"]])

    def test_uses_personal_assistant_when_no_specialist_matches(self):
        result = route_role(ROOT, "Разбери это и помоги определить следующий шаг")

        self.assertEqual(result["primary_role"]["id"], "personal-assistant")
        self.assertEqual(result["primary_role"]["matched_triggers"], [])

    def test_routes_emotional_reflection_to_wellbeing_coach(self):
        result = route_role(ROOT, "Помоги спокойно разобрать тревогу и эмоциональное состояние")

        self.assertEqual(result["primary_role"]["id"], "wellbeing-coach")
        self.assertIn("тревогу", result["primary_role"]["matched_triggers"])

    def test_registry_exposes_declared_roles_without_claiming_runtime_agents(self):
        roles = list_roles(ROOT)

        self.assertGreaterEqual(len(roles), 10)
        self.assertTrue(all(role["status"] == "ROUTABLE_PROFILE" for role in roles))
        self.assertTrue(all(role["authority_effect"] == "none" for role in roles))

    def test_cli_route_outputs_machine_readable_packet(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["role", "route", "--text", "Мне нужен план тренировок", "--json"], root=ROOT)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["primary_role"]["id"], "fitness-coach")


if __name__ == "__main__":
    unittest.main()
