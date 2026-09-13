import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from grok_codex_bridge import context as subject


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.root / 'AGENTS.md').write_text('Workspace current rule', encoding='utf-8')
        (self.project / 'AGENTS.md').write_text('项目规则 A', encoding='utf-8')

    def snapshot(self, **kwargs):
        return subject.instruction_context(self.project, workspace_root=self.root, **kwargs)

    def test_same_canonical_paths_and_stable_fingerprint(self):
        first = self.snapshot()
        second = self.snapshot()
        self.assertEqual(first['fingerprint'], second['fingerprint'])
        self.assertEqual([Path(r['path']) for r in first['files']],
                         [self.root / 'AGENTS.md', self.project / 'AGENTS.md'])
        self.assertFalse(first['modelHasReadThisContext'])
        self.assertEqual(first['modelCallsStarted'], 0)

    def test_two_updates_are_read_even_with_same_length(self):
        seen = []
        for revision in ('A', 'B', 'C'):
            (self.project / 'AGENTS.md').write_text('项目规则 ' + revision, encoding='utf-8')
            current = self.snapshot()
            self.assertIn('项目规则 ' + revision, subject.context_prompt(current))
            seen.append(current['fingerprint'])
        self.assertEqual(len(set(seen)), 3)

    def test_override_wins_and_empty_override_falls_back(self):
        override = self.project / 'AGENTS.override.md'
        override.write_text('Override', encoding='utf-8')
        self.assertEqual(self.snapshot()['files'][-1]['content'], 'Override')
        override.write_text(' \n', encoding='utf-8')
        self.assertEqual(self.snapshot()['files'][-1]['content'], '项目规则 A')

    def test_selected_current_document_changes_fingerprint(self):
        current = self.project / 'CURRENT.md'
        current.write_text('stage A', encoding='utf-8')
        before = self.snapshot(extra_docs=['CURRENT.md'])
        current.write_text('stage B', encoding='utf-8')
        after = self.snapshot(extra_docs=['CURRENT.md'])
        self.assertNotEqual(before['fingerprint'], after['fingerprint'])
        self.assertEqual(after['files'][-1]['role'], 'selected-document')

    def test_missing_selected_document_is_error_not_empty_success(self):
        with self.assertRaises(FileNotFoundError):
            self.snapshot(extra_docs=['missing.md'])

    def test_outside_document_is_rejected(self):
        with self.assertRaises(ValueError):
            self.snapshot(extra_docs=[self.root.parent / 'outside.md'])

    def test_non_document_is_rejected(self):
        secret = self.project / 'auth.json'
        secret.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.snapshot(extra_docs=['auth.json'])

    def test_duplicate_selected_document_not_copied_twice(self):
        context = self.snapshot(extra_docs=['AGENTS.md', 'AGENTS.md'])
        self.assertEqual(len(context['files']), 2)

    def test_metadata_omits_body_but_includes_identity(self):
        context = self.snapshot()
        metadata = subject.public_context(context)
        self.assertNotIn('content', metadata['files'][0])
        self.assertEqual(metadata['fingerprint'], context['fingerprint'])
        self.assertIn('content', subject.public_context(context, True)['files'][0])

    def test_alias_is_reported_not_silently_merged(self):
        alias = self.project / 'AGENT.md'
        alias.write_text('stale alias', encoding='utf-8')
        context = self.snapshot()
        self.assertIn(str(alias), context['alternateInstructionPathsNotMerged'])
        self.assertNotIn('stale alias', subject.context_prompt(context))

    def test_large_file_fails_without_truncation(self):
        (self.project / 'AGENTS.md').write_bytes(b'x' * (subject.MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError):
            self.snapshot()

    def test_relative_cwd_rejected(self):
        with self.assertRaises(ValueError):
            subject.instruction_context('project', workspace_root=self.root)

    def test_outside_workspace_uses_only_explicit_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            selected = Path(folder).resolve()
            (selected / 'AGENTS.md').write_text('independent', encoding='utf-8')
            context = subject.instruction_context(selected, workspace_root=self.root)
        self.assertIsNone(context['workspaceRoot'])
        self.assertEqual([r['content'] for r in context['files']], ['independent'])

    def test_content_bytes_match_full_utf8_files(self):
        context = self.snapshot()
        expected = sum(Path(row['path']).stat().st_size for row in context['files'])
        self.assertEqual(context['contentBytes'], expected)

    def test_total_budget_fails_without_partial_success(self):
        with patch.object(subject, 'MAX_TOTAL_BYTES', 8), self.assertRaises(ValueError):
            self.snapshot()

    def test_file_count_budget_fails_without_partial_success(self):
        with patch.object(subject, 'MAX_FILES', 1), self.assertRaises(ValueError):
            self.snapshot()

    def test_bad_utf8_is_not_silently_replaced(self):
        (self.project / 'AGENTS.md').write_bytes(b'\xff\xfe\xff')
        with self.assertRaises(UnicodeDecodeError):
            self.snapshot()

    def test_changed_during_read_is_not_a_valid_snapshot(self):
        path = self.project / 'AGENTS.md'
        before = path.stat()
        from types import SimpleNamespace
        after = SimpleNamespace(st_size=before.st_size, st_mtime_ns=before.st_mtime_ns + 1,
                                st_ino=before.st_ino)
        with patch.object(Path, 'stat', side_effect=[before, after]), self.assertRaises(ValueError):
            subject._read(path)


if __name__ == '__main__':
    unittest.main()
