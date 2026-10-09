import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cyb


def row(name, dependencies=(), **extra):
    return {'name': name, 'depends_on': list(dependencies), 'status': 'library',
            'role': 'test', 'test_command': None, **extra}


class ProductCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_dependencies_are_installed_first_once(self):
        graph = {r['name']: r for r in [row('CybCore', ['Swarm', 'Memory']),
                 row('Swarm', ['Memory']), row('Memory')]}
        self.assertEqual([r['name'] for r in cyb.select(graph, ['CybCore'])],
                         ['Memory', 'Swarm', 'CybCore'])

    def test_missing_dependencies_and_cycles_are_rejected(self):
        for graph in ({'a': row('a', ['missing'])},
                      {'a': row('a', ['b']), 'b': row('b', ['a'])}):
            with self.assertRaises(cyb.SetupError):
                cyb.select(graph, ['a'])

    def test_all_profile_excludes_planned_components(self):
        graph = {'a': row('a'), 'future': row('future', status='planned')}
        self.assertEqual([r['name'] for r in cyb.profile(graph, 'all')], ['a'])

    def test_python_launcher_uses_real_environment_without_activation(self):
        target = self.root / 'app'
        target.mkdir()
        (target / 'requirements.lock.txt').write_text('')
        subprocess.run([sys.executable, '-m', 'venv', str(target / '.venv'), '--without-pip'], check=True)
        (target / 'run.py').write_text('import sys, pathlib; pathlib.Path("prefix.txt").write_text(sys.prefix)')
        command = cyb.python_command(['python3', 'run.py'], target)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cyb.run_command(command, target), 0)
        self.assertEqual(Path((target / 'prefix.txt').read_text()), target / '.venv')

    def test_missing_python_environment_reports_setup(self):
        (self.root / 'requirements.lock.txt').write_text('')
        with self.assertRaisesRegex(cyb.SetupError, 'setup first'):
            cyb.python_command(['python3', 'run.py'], self.root)

    def test_source_setup_still_checks_existing_revision(self):
        home = self.root / 'cybOS'
        home.mkdir()
        pins = [{'name': 'app', 'commit': 'a' * 40}]
        (home / 'ecosystem.lock.json').write_text(json.dumps({'repositories': pins}))
        (self.root / 'app').mkdir()
        with patch('cyb.bootstrap') as bootstrap, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cyb.setup(self.root, [row('app')], home, build=False), 0)
        self.assertEqual(bootstrap.call_count, 2)
        self.assertTrue(bootstrap.call_args.kwargs['verify'])

    def test_missing_pin_fails_before_bootstrap(self):
        (self.root / 'ecosystem.lock.json').write_text('{"repositories": []}')
        with patch('cyb.bootstrap') as bootstrap, self.assertRaisesRegex(cyb.SetupError, 'Missing pinned'):
            cyb.setup(self.root, [row('app')], self.root)
        bootstrap.assert_not_called()

    def test_setup_reports_failed_build_instead_of_success(self):
        home = self.root / 'cybOS'
        home.mkdir()
        (home / 'ecosystem.lock.json').write_text(json.dumps({'repositories': [{'name': 'app', 'commit': 'a' * 40}]}))
        target = self.root / 'app'
        target.mkdir()
        (target / 'Cargo.toml').write_text('[package]\nname="app"\n')
        with patch('cyb.bootstrap'), patch('cyb.run_command', return_value=1), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cyb.setup(self.root, [row('app')], home), 1)

    def test_planned_component_cannot_launch(self):
        with patch('cyb.catalog', return_value={'future': row('future', status='planned')}), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cyb.main(['run', 'future']), 1)

    def test_static_server_is_loopback_only_and_checks_entry(self):
        target = self.root / 'web'
        target.mkdir()
        (target / 'index.html').write_text('<h1>test</h1>')
        with patch('cyb.catalog', return_value={'web': row('web', web_entry='index.html')}), patch('cyb.run_command', return_value=0) as run:
            self.assertEqual(cyb.main(['--root', str(self.root), 'serve', 'web', '--port', '8123']), 0)
            self.assertIn('127.0.0.1', run.call_args.args[0])
            self.assertEqual(run.call_args.args[1], target)
        (target / 'index.html').unlink()
        with patch('cyb.catalog', return_value={'web': row('web', web_entry='index.html')}), patch('cyb.run_command') as run, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cyb.main(['--root', str(self.root), 'serve', 'web']), 1)
            run.assert_not_called()

    def test_missing_command_is_an_actionable_error(self):
        with self.assertRaisesRegex(cyb.SetupError, 'missing'):
            cyb.run_command(['cyb-nonexistent-tool-98364'], self.root)

    def test_symlink_checkout_is_rejected(self):
        if os.name == 'nt':
            self.skipTest('Windows symlinks may require developer mode')
        (self.root / 'linked').symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(cyb.SetupError, 'symbolic'):
            cyb.checkout(self.root, row('linked'))
