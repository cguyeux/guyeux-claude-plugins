import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path.home() / ".agents" / "skills" / "init-project" / "init_project.py"


class AgentsInitProjectRuntimeTests(unittest.TestCase):
    def test_migrate_preserves_existing_files_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "existing_project"
            (project / "article").mkdir(parents=True)
            (project / "analyses").mkdir()
            (project / "AGENTS.md").write_text("AGENTS PREEXISTANT\n", encoding="utf-8")
            (project / "article" / "main.tex").write_text("MAIN PREEXISTANT\n", encoding="utf-8")
            (project / "cahier_de_labo.md").write_text(
                "# Cahier existant\n\n## 2026-01-01\n\n- fait acquis\n",
                encoding="utf-8",
            )

            command = [
                sys.executable,
                str(SCRIPT),
                "--migrate",
                str(project),
                "--title",
                "Existing_Project & migration",
                "--no-git",
                "--no-parent-gitignore",
            ]
            subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.assertEqual("AGENTS PREEXISTANT\n", (project / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual("MAIN PREEXISTANT\n", (project / "article" / "main.tex").read_text(encoding="utf-8"))
            self.assertTrue((project / "etat_des_decouvertes.md").is_file())
            self.assertTrue((project / "pistes.md").is_file())
            self.assertTrue((project / "article" / "references.bib").is_file())
            self.assertTrue((project / "litterature_review" / "index.md").is_file())
            self.assertIn(
                "À régénérer depuis le cahier",
                (project / "etat_des_decouvertes.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Reconstruire l'arbre des pistes",
                (project / "pistes.md").read_text(encoding="utf-8"),
            )

    def test_from_piste_mutates_only_target_block_and_seeds_cahier(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "pistes.md"
            registry.write_text(
                "# Pistes parent\n\n"
                "## P1. Première piste [à faire]\n"
                "  origine : test\n"
                "  - garder cette matière\n"
                "  - sous-point important\n\n"
                "## P2. Deuxième piste [en cours]\n"
                "  origine : test\n"
                "  - ne doit pas changer\n",
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "migrated_project",
                    "--title",
                    "Projet migré depuis piste",
                    "--at",
                    str(base),
                    "--from-piste",
                    "P1",
                    "--registry",
                    str(registry),
                    "--no-git",
                    "--no-parent-gitignore",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            registry_text = registry.read_text(encoding="utf-8")
            cahier = (base / "migrated_project" / "cahier_de_labo.md").read_text(encoding="utf-8")
            self.assertIn("## P1. Première piste [abandonné]", registry_text)
            self.assertIn("MIGRÉ vers migrated_project", registry_text)
            self.assertIn("## P2. Deuxième piste [en cours]", registry_text)
            self.assertEqual(1, registry_text.count("MIGRÉ vers migrated_project"))
            self.assertIn("## P1. Première piste [à faire]", cahier)
            self.assertNotIn("## P2. Deuxième piste", cahier)


if __name__ == "__main__":
    unittest.main()
