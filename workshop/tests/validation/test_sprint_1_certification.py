#!/usr/bin/env python3
"""Git-backed adversarial tests for the Sprint 1 certification boundary."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class CertificationFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sprint-certification-")
        self.root = Path(self.temp.name)
        shutil.copytree(REPO_ROOT / "workshop", self.root / "workshop")
        self.project = self.root / "workshop" / "projects" / "the-myr-singularity"
        self.cert_path = self.project / "reports" / "sprint_1_certification.json"
        self.backlog_path = self.project / "notes" / "backlog.json"
        self.validator = self.root / "workshop" / "tests" / "validation" / "validate_sprint_1_certification.py"
        self.renderer = self.root / "workshop" / "scripts" / "render_sprint_1_closure.py"
        self.git("init")
        self.git("config", "user.email", "certification@example.invalid")
        self.git("config", "user.name", "Certification Fixture")
        self.git("add", "workshop")
        self.git("commit", "-m", "fixture base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        cert = self.load(self.cert_path)
        cert["candidate_base_commit"] = self.base
        self.write(self.cert_path, cert)
        self.render()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.temp.cleanup()

    def git(self, *args):
        result = subprocess.run(
            ["git", *args], cwd=self.root, text=True, encoding="utf-8",
            capture_output=True, check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return result

    @staticmethod
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    @staticmethod
    def write(path, value):
        Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def render(self):
        result = subprocess.run(
            [sys.executable, str(self.renderer)], cwd=self.root,
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_validator(self, *, skip_lower=True):
        spec = importlib.util.spec_from_file_location("fixture_certification", self.validator)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = module.validate_certification(
                self.root,
                expected_base_commit=self.base,
                run_lower_regressions=not skip_lower,
            )
        return subprocess.CompletedProcess([], code, output.getvalue(), "")

    def mutate_cert(self, mutate, *, render=True):
        cert = self.load(self.cert_path)
        mutate(cert)
        self.write(self.cert_path, cert)
        if render:
            self.render()

    def mutate_backlog(self, mutate):
        backlog = self.load(self.backlog_path)
        mutate(backlog)
        self.write(self.backlog_path, backlog)
        self.render()

    def complete_review(self, *, status="certified", verdict="APPROVE", followups=None, blockers=None, rationale=None, reviewed_commit=None, source=True):
        followups = [] if followups is None else followups
        blockers = [] if blockers is None else blockers
        reviewed_commit = reviewed_commit or self.base
        review_path = self.project / "reports" / "sprint_1_certification_review.json"
        review_doc = {
            "artifact_type": "sprint_certification_review",
            "certification_id": "sprint-1-certification-candidate",
            "project_id": "the-myr-singularity",
            "reviewer": "Sol",
            "reviewer_role": "independent_reviewer",
            "verdict": verdict,
            "reviewed_commit": reviewed_commit,
            "reviewed_at": "2026-07-12T12:00:00Z",
            "blocking_findings": blockers,
            "non_blocking_followups": followups,
        }
        if source:
            self.write(review_path, review_doc)
        def mutate(cert):
            cert["certification_status"] = status
            actions = {
                "certified": {"action_id": "merge_and_record_certification", "description": "Merge, record certification closure, and synchronize external RFC documentation."},
                "certified_with_non_blocking_followups": {"action_id": "merge_record_and_track_followups", "description": "Merge, record certification, and track non-blocking follow-ups."},
                "not_certified": {"action_id": "remediate_and_request_new_review", "description": "Remediate blocking findings and request a new independent review."},
            }
            cert["next_action"] = actions[status]
            for gate in cert["quality_gates"]:
                gate["limitations"] = None
            cert["independent_review"] = {
                "status": "completed", "reviewer": "Sol",
                "reviewer_role": "independent_reviewer", "verdict": verdict,
                "reviewed_commit": reviewed_commit, "reviewed_at": "2026-07-12T12:00:00Z",
                "review_source": {"path": "workshop/projects/the-myr-singularity/reports/sprint_1_certification_review.json"},
                "blocking_findings": blockers, "non_blocking_followups": followups,
                "rationale": rationale,
            }
        self.mutate_cert(mutate)


class SprintCertificationTests(unittest.TestCase):
    def test_00_production_environment_bypasses_are_ignored(self):
        env = os.environ.copy()
        env["WORKSHOP_CERTIFICATION_EXPECTED_BASE"] = "0000000000000000000000000000000000000000"
        env["WORKSHOP_CERTIFICATION_SKIP_LOWER_REGRESSIONS"] = "1"
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "workshop" / "tests" / "validation" / "validate_sprint_1_certification.py")],
            cwd=REPO_ROOT, env=env, text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_fails(self, fixture, expected, *, skip_lower=True):
        result = fixture.run_validator(skip_lower=skip_lower)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn(expected, output)

    def test_01_production_candidate_passes(self):
        with CertificationFixture() as fixture:
            result = fixture.run_validator()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_02_source_and_base_mutations(self):
        cases = [
            ("wrong source", lambda f: f.mutate_cert(lambda c: c["source_references"]["project_report"].update(path="workshop/projects/the-myr-singularity/project.json")), "project report source identity"),
            ("wrong source ID", lambda f: f.mutate_cert(lambda c: c["source_references"]["rec_002"].update(id="rec-999")), "rec-002 source identity"),
            ("arbitrary base", lambda f: f.mutate_cert(lambda c: c.update(candidate_base_commit="a" * 40)), "candidate_base_commit"),
            ("protected change", self._commit_protected_change, "protected artifacts changed"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                mutate(fixture)
                self.assert_fails(fixture, expected)

    @staticmethod
    def _commit_protected_change(fixture):
        path = fixture.project / "deck" / "current.txt"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        fixture.git("add", str(path.relative_to(fixture.root)))
        fixture.git("commit", "-m", "protected mutation")

    def test_03_product_loop_mutations(self):
        cases = [
            ("missing analysis evidence", lambda c: c["product_loop"][6].update(source_keys=[]), "loop-07"),
            ("missing decisions", lambda c: c["source_references"].update(decisions=[]), "loop-11"),
            ("wrong report source", lambda c: c["product_loop"][14].update(source_keys=["project"]), "loop-15"),
            ("reordered", lambda c: c["product_loop"].__setitem__(slice(0, 2), list(reversed(c["product_loop"][:2]))), "stage order"),
            ("empty source keys", lambda c: c["product_loop"][0].update(source_keys=[]), "loop-01"),
            ("empty boundary", lambda c: c["product_loop"][0].update(input_boundary=""), "loop-01"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                fixture.mutate_cert(mutate)
                self.assert_fails(fixture, expected)

    def test_04_exit_criterion_mutations(self):
        cases = [
            ("false current deck", self._break_current_deck, "exit-19"),
            ("false baseline retention", self._break_parent, "exit-06"),
            ("wrong criterion sources", lambda f: f.mutate_cert(lambda c: c["sprint_exit_criteria"][18].update(evidence_source_keys=["project"])), "exit-19 evidence"),
            ("wrong requirement", lambda f: f.mutate_cert(lambda c: c["sprint_exit_criteria"][0].update(requirement_level="optional")), "exit-01 requirement metadata"),
            ("missing limitation", lambda f: f.mutate_cert(lambda c: c["sprint_exit_criteria"][23].update(limitations=None)), "exit-24 requirement metadata"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                mutate(fixture)
                self.assert_fails(fixture, expected)

    @staticmethod
    def _break_current_deck(fixture):
        path = fixture.project / "deck" / "current.txt"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("1 Arcane Signet", "1 Wrong Card"), encoding="utf-8")

    @staticmethod
    def _break_parent(fixture):
        path = fixture.project / "versions" / "v1.1.json"
        doc = fixture.load(path)
        doc["parent_version_id"] = "v9.9"
        fixture.write(path, doc)

    def test_05_gate_and_done_mutations(self):
        cases = [
            ("false gate", lambda f: f.mutate_cert(lambda c: c["quality_gates"][0].update(status="fail")), "gate-project"),
            ("false gate outcome", lambda f: f.mutate_cert(lambda c: c["quality_gates"][0].update(outcome="claimed")), "gate-project"),
            ("false gate limitation", lambda f: f.mutate_cert(lambda c: c["quality_gates"][0].update(limitations=None)), "gate-project"),
            ("broken gate dependency", self._break_current_deck, "gate-decision-versioning"),
            ("false functional", lambda f: f.mutate_cert(lambda c: c["definition_of_done"][0].update(functional_done="fail")), "functional_done"),
            ("false structural", lambda f: f.mutate_cert(lambda c: c["definition_of_done"][0].update(structural_done="fail")), "structural_done"),
            ("false product", lambda f: f.mutate_cert(lambda c: c["definition_of_done"][0].update(product_done="fail")), "product_done"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                mutate(fixture)
                self.assert_fails(fixture, expected)

    def test_06_orchestration_and_renderer_drift(self):
        cases = [
            ("rec-001", lambda f: (f.project / "recommendations" / "rec-001.md").write_text("drift", encoding="utf-8"), "rec-001 validator failed"),
            ("rec-002", lambda f: (f.project / "recommendations" / "rec-002.md").write_text("drift", encoding="utf-8"), "rec-002 validator failed"),
            ("all JSON", lambda f: (f.root / "workshop" / "unrelated.json").write_text("{ invalid", encoding="utf-8"), "invalid Workshop JSON"),
            ("cert Markdown", lambda f: f.cert_path.with_suffix(".md").write_text("drift", encoding="utf-8"), "certification Markdown differs"),
            ("backlog Markdown", lambda f: f.backlog_path.with_suffix(".md").write_text("drift", encoding="utf-8"), "backlog Markdown differs"),
            ("report Markdown", lambda f: (f.project / "reports" / "project_report_v1.1.md").write_text("drift", encoding="utf-8"), "project report Markdown differs"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                mutate(fixture)
                self.assert_fails(fixture, expected)

    def test_07_lower_level_regression_orchestration(self):
        with CertificationFixture() as fixture:
            path = fixture.root / "workshop" / "tests" / "validation" / "test_validation_architecture.py"
            text = path.read_text(encoding="utf-8")
            injection = "\n    def test_forced_certification_fixture_failure(self):\n        self.fail('forced lower-level failure')\n"
            path.write_text(text.replace("\nif __name__ == \"__main__\":", injection + "\nif __name__ == \"__main__\":"), encoding="utf-8")
            self.assert_fails(fixture, "lower-level regression suite failed", skip_lower=False)

    def test_08_renderer_is_data_driven(self):
        with CertificationFixture() as fixture:
            spec = importlib.util.spec_from_file_location("closure_renderer_test", fixture.renderer)
            renderer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(renderer)
            cert = fixture.load(fixture.cert_path)
            cases = []
            changed = json.loads(json.dumps(cert)); changed["project_name"] = "Different Project"; cases.append(("project", changed, "Different Project"))
            changed = json.loads(json.dumps(cert)); changed["version_state"].update(baseline_version_id="v8.0", resulting_version_id="v8.1", current_version_id="v8.1"); cases.append(("versions", changed, "Baseline: v8.0"))
            cases.append(("pending", cert, "independent review pending"))
            changed = self._renderer_review(cert, "certified", "APPROVE", [], []); cases.append(("certified", changed, "Reviewer: Sol"))
            changed = self._renderer_review(cert, "not_certified", "REQUEST CHANGES", [], ["Blocking"]); changed["independent_review"]["rationale"] = "Rejected"; cases.append(("not certified", changed, "Blocking findings"))
            changed = json.loads(json.dumps(cert)); changed["external_documentation"]["backlog_work_type"] = "different-doc-sync"; cases.append(("external docs", changed, "different-doc-sync"))
            for name, document, expected in cases:
                with self.subTest(name=name):
                    self.assertIn(expected, renderer.render_certification(document))

    @staticmethod
    def _renderer_review(cert, status, verdict, followups, blockers):
        changed = json.loads(json.dumps(cert))
        changed["certification_status"] = status
        changed["independent_review"] = {
            "status": "completed", "reviewer": "Sol", "reviewer_role": "independent_reviewer",
            "verdict": verdict, "reviewed_commit": "abc", "reviewed_at": "now",
            "review_source": {"path": "review.json"}, "blocking_findings": blockers,
            "non_blocking_followups": followups, "rationale": None,
        }
        return changed

    def test_09_review_lifecycle_mutations(self):
        cases = [
            ("random commit", lambda f: f.complete_review(reviewed_commit="a" * 40), "reviewed_commit"),
            ("missing source", lambda f: f.complete_review(source=False), "review source does not resolve"),
            ("followups missing", lambda f: f.complete_review(status="certified_with_non_blocking_followups"), "requires approval and explicit"),
            ("not certified no blockers", lambda f: f.complete_review(status="not_certified", verdict="REQUEST CHANGES", rationale="Rejected"), "requires rejection rationale and blocking"),
            ("not certified pending", lambda f: f.mutate_cert(lambda c: c.update(certification_status="not_certified")), "lacks independent review identity"),
            ("pending reviewer", lambda f: f.mutate_cert(lambda c: c["independent_review"].update(reviewer="Sol")), "pending independent review"),
            ("pending blockers", lambda f: f.mutate_cert(lambda c: c["independent_review"].update(blocking_findings=["Blocking"])), "pending independent review"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                mutate(fixture)
                self.assert_fails(fixture, expected)
        with self.subTest(name="valid completed"), CertificationFixture() as fixture:
            fixture.complete_review()
            result = fixture.run_validator()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_10_backlog_mutations(self):
        def item(work_type):
            return lambda backlog: next(value for value in backlog["items"] if value["work_type"] == work_type)
        cases = [
            ("duplicate", lambda b: b["items"].append(dict(b["items"][0])), "backlog IDs must be unique"),
            ("project", lambda b: b["items"][0].update(project_id="wrong"), "wrong project ID"),
            ("missing KCI", lambda b: item("candidate_testing_kci")(b).pop("related_candidate_id"), "candidate_testing_kci"),
            ("wrong KCI", lambda b: item("candidate_testing_kci")(b).update(related_candidate_id="cand-010"), "candidate_testing_kci"),
            ("authorized KCI", lambda b: item("candidate_testing_kci")(b).update(implementation_authorized=True), "candidate_testing_kci"),
            ("analysis version", lambda b: item("post_implementation_analysis")(b).pop("related_version_id"), "must target v1.1"),
            ("simulation assumptions", lambda b: item("mana_color_simulation")(b).update(required_assumptions=[]), "lacks required pending assumptions"),
            ("RFCs", lambda b: item("external_rfc_sync")(b).update(external_rfc_ids=[]), "does not cover RFC"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                fixture.mutate_backlog(mutate)
                self.assert_fails(fixture, expected)

    def test_11_checklist_mutations(self):
        cases = [
            ("section", "product_principles.md", lambda text: text.replace("## Required Checks", "## Missing"), "missing required checklist sections"),
            ("evidence", "data_model.md", lambda text: text.replace("workshop/card-data/cards.json", "missing.json"), "evidence does not resolve"),
            ("simulation complete", "simulation.md", lambda text: text.replace("[~] SIM-01", "[x] SIM-01"), "must be not required"),
            ("fail item", "reasoning.md", lambda text: text.replace("[x] RS-01", "[ ] RS-01"), "is failing"),
            ("no items", "reasoning.md", lambda _: "# Reasoning Regression Checklist\n\n## Required Checks\n", "contains no checklist items"),
        ]
        for name, filename, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                path = fixture.root / "workshop" / "tests" / "regression" / filename
                path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
                self.assert_fails(fixture, expected)

    def test_12_closure_document_mutations(self):
        cases = [
            ("README", "README.md", lambda _: "placeholder", "README is missing"),
            ("scope", "project.json", None, "project scope"),
            ("notes", "notes/notes.md", lambda text: text.replace("# 2026-07-12 - Sprint 1 Certification Candidate", "# Removed"), "certification-candidate checkpoint"),
            ("handoff", "notes/sprint_1_documentation_handoff.md", lambda text: text.replace("## RFC-013", "## Removed"), "missing RFC-013"),
            ("validation docs", "../../tests/validation/README.md", lambda text: text.replace("candidate_base_commit", "removed-base-marker"), "validation documentation lacks"),
            ("changelog", "reports/changelog.md", lambda text: text.replace("Sprint 1", "Iteration One"), "changelog does not identify"),
        ]
        for name, relative, mutate, expected in cases:
            with self.subTest(name=name), CertificationFixture() as fixture:
                path = fixture.project / relative
                if name == "scope":
                    doc = fixture.load(path); doc["scope"]["phase"] = "wrong"; fixture.write(path, doc)
                else:
                    path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
                self.assert_fails(fixture, expected)

    def test_13_candidate_evidence_mutations(self):
        cases = [
            ("KCI name", lambda item: item.update(name="Mana Echoes")),
            ("KCI review", lambda item: item.update(review_status="accepted_for_decision")),
            ("KCI implementation", lambda item: item.update(implementation_status="implemented")),
            ("KCI source", lambda item: item.update(source_candidate_reference="candidate:scryfall:wrong")),
            ("Mana state", lambda item: item.update(name="Wrong", implementation_status="implemented")),
        ]
        for index, (name, mutate) in enumerate(cases):
            with self.subTest(name=name), CertificationFixture() as fixture:
                target = 1 if name == "Mana state" else 0
                fixture.mutate_cert(lambda cert, target=target, mutate=mutate: mutate(cert["evidence_boundary"]["needs_testing_candidates"][target]))
                self.assert_fails(fixture, "does not match active candidate facts")

    def test_14_simulation_absence_remains_valid(self):
        with CertificationFixture() as fixture:
            result = fixture.run_validator()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
