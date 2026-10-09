import json
from pathlib import Path
import unittest
class EcosystemTests(unittest.TestCase):
    def test_dependencies_resolve_without_cycles(self):
        rows=json.loads((Path(__file__).parents[1]/'ecosystem.json').read_text())['repositories']
        graph={r['name']:r['depends_on'] for r in rows};self.assertEqual(len(graph),len(rows))
        def visit(node, ancestors):
            self.assertNotIn(node,ancestors)
            for target in graph[node]:self.assertIn(target,graph);visit(target,ancestors|{node})
        for node in graph:visit(node,set())
    def test_pins_cover_all_sibling_repositories(self):
        root=Path(__file__).parents[1]
        expected={r['name'] for r in json.loads((root/'ecosystem.json').read_text())['repositories']} - {'cybOS'}
        pins=json.loads((root/'ecosystem.lock.json').read_text())['repositories']
        self.assertEqual(len(pins),len(expected))
        self.assertEqual({p['name'] for p in pins},expected)
        for pin in pins:self.assertRegex(pin['commit'],r'^[0-9a-f]{40}$')
    def test_catalog_uses_real_owner_and_declared_commands(self):
        rows=json.loads((Path(__file__).parents[1]/'ecosystem.json').read_text())['repositories']
        for r in rows:
            self.assertEqual(r['url'],'https://github.com/c1cad4/'+r['name'])
            self.assertNotEqual(r['name'],'CybBrowser-')
            if r['test_command'] is not None:self.assertIsInstance(r['test_command'],list)
if __name__=='__main__':unittest.main()
