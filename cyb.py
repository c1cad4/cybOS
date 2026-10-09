#!/usr/bin/env python3
"""One entry point for pinned cybOS components, setup, checks and local launches."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from tools.bootstrap import bootstrap, validate_pins

REPO_DIR = Path(__file__).resolve().parent
PROFILES = {'core': ['CybCore'], 'desktop': ['CybOS-demo']}


class SetupError(ValueError):
    pass


def catalog(home=REPO_DIR):
    rows = json.loads((home / 'ecosystem.json').read_text(encoding='utf-8'))['repositories']
    graph = {}
    for row in rows:
        name = row['name']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name):
            raise SetupError('Invalid component name')
        if name.casefold() in {key.casefold() for key in graph}:
            raise SetupError('Duplicate component name')
        for field in ('test_command', 'run_command'):
            command = row.get(field)
            if command is not None and (not isinstance(command, list) or not command or
                                        not all(isinstance(arg, str) and arg for arg in command)):
                raise SetupError(f'{name}: invalid {field}')
        graph[name] = row
    select(graph, list(graph))  # Check missing dependencies and cycles before setup.
    return graph


def select(graph, names):
    ordered, complete, visiting = [], set(), set()
    def visit(name):
        if name not in graph:
            raise SetupError(f'Unknown component: {name}')
        if name in visiting:
            raise SetupError(f'Dependency cycle: {name}')
        if name in complete:
            return
        visiting.add(name)
        for dependency in graph[name]['depends_on']:
            visit(dependency)
        visiting.remove(name)
        complete.add(name)
        ordered.append(graph[name])
    for name in names:
        visit(name)
    return ordered


def profile(graph, name):
    names = [key for key, row in graph.items() if row['status'] != 'planned'] if name == 'all' else PROFILES[name]
    return select(graph, names)


def checkout(root, row, home=REPO_DIR):
    target = home if row['name'] == 'cybOS' else root / row['name']
    if target.is_symlink():
        raise SetupError(f"{row['name']}: symbolic checkout paths are not supported")
    return target


def env_python(target):
    return target / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def run_command(command, target, **kwargs):
    executable = command[0]
    if not Path(executable).is_file() and shutil.which(executable) is None:
        raise SetupError(f'{executable} is missing; install it before continuing')
    print('RUN', ' '.join(str(arg) for arg in command), flush=True)
    return subprocess.run([str(arg) for arg in command], cwd=target, **kwargs).returncode


def python_command(command, target):
    if command[0] in ('python', 'python3'):
        executable = env_python(target) if (target / 'requirements.lock.txt').is_file() else Path(sys.executable)
        if not executable.is_file():
            raise SetupError(f'{target.name}: run setup first to create its Python environment')
        return [str(executable), *command[1:]]
    return command


def setup(root, rows, home=REPO_DIR, build=True):
    pins = json.loads((home / 'ecosystem.lock.json').read_text(encoding='utf-8'))['repositories']
    validate_pins(pins)
    by_name = {pin['name']: pin for pin in pins}
    wanted = [row['name'] for row in rows if row['name'] != 'cybOS' and row['status'] != 'planned']
    missing = set(wanted) - by_name.keys()
    if missing:
        raise SetupError('Missing pinned components: ' + ', '.join(sorted(missing)))
    bootstrap(root, [by_name[name] for name in wanted])
    # Existing checkouts stay untouched, but mismatched revisions must not be
    # silently reported as a reproducible installation.
    bootstrap(root, [by_name[name] for name in wanted], verify=True)
    failures = []
    for row in rows:
        target = checkout(root, row, home)
        if row['status'] == 'planned':
            print('PLANNED', row['name'], flush=True)
            continue
        try:
            commands = []
            if (target / 'requirements.lock.txt').is_file():
                python = env_python(target)
                if not python.is_file():
                    code = run_command([sys.executable, '-m', 'venv', str(target / '.venv')], target)
                    if code:
                        raise SetupError('Could not create Python environment')
                commands.append([str(python), '-m', 'pip', 'install', '-r', 'requirements.lock.txt'])
            if (target / 'package.json').is_file():
                package = json.loads((target / 'package.json').read_text())
                has_dependencies = any(package.get(key) for key in ('dependencies', 'devDependencies', 'optionalDependencies'))
                if has_dependencies:
                    if not (target / 'package-lock.json').is_file():
                        raise SetupError('package-lock.json is required for reproducible npm setup')
                    commands.append(['npm', 'ci'])
                elif shutil.which('node') is None:
                    raise SetupError('node is missing; install Node.js 24+ to run this component')
            if build and (target / 'Cargo.toml').is_file():
                command = ['cargo', 'build', '--locked', '-j', '4']
                if row['status'] == 'workspace-limited':
                    command.extend(['--manifest-path', 'crates/cyb/Cargo.toml'])
                commands.append(command)
            if build and (target / 'go.mod').is_file():
                commands.append(['go', 'build', '-mod=readonly', '-p', '4', './...'])
            for command in commands:
                if run_command(command, target):
                    raise SetupError('Setup command failed')
            if row['status'] == 'platform-limited':
                print('MANUAL', row['name'], row.get('limitation', ''), flush=True)
            else:
                print('PREPARED', row['name'], flush=True)
        except (OSError, SetupError) as error:
            failures.append(row['name'])
            print('BLOCKED', row['name'], str(error), flush=True)
    return int(bool(failures))


def readiness(root, rows, home=REPO_DIR):
    pins = {pin['name']: pin['commit'] for pin in json.loads((home / 'ecosystem.lock.json').read_text())['repositories']}
    failures = 0
    for row in rows:
        name = row['name']
        target = checkout(root, row, home)
        problems = []
        if row['status'] == 'planned':
            print('PLANNED', name, row.get('limitation', 'No runnable implementation'))
            continue
        if not target.is_dir():
            problems.append('checkout missing; run setup')
        elif name != 'cybOS':
            result = subprocess.run(['git', '-C', str(target), 'rev-parse', 'HEAD'], capture_output=True, text=True)
            if result.returncode or result.stdout.strip() != pins.get(name):
                problems.append('checkout differs from ecosystem.lock.json; local changes preserved')
        if target.is_dir():
            if (target / 'requirements.lock.txt').is_file():
                python = env_python(target)
                if not python.is_file():
                    problems.append('Python environment missing; run setup')
                else:
                    result = subprocess.run([str(python), '-m', 'pip', 'check'], capture_output=True, text=True)
                    if result.returncode:
                        problems.append('Python dependencies inconsistent; run setup')
                    if name == 'CybCore':
                        result = subprocess.run([str(python), '-c', 'import app'], cwd=target, capture_output=True, text=True)
                        if result.returncode:
                            problems.append('API import failed; run setup and test')
            command = row.get('test_command') or row.get('run_command')
            if command and command[0] not in ('python', 'python3') and shutil.which(command[0]) is None:
                problems.append(command[0] + ' is missing')
            if (target / 'Cargo.toml').is_file() and shutil.which('rustc'):
                manifest = tomllib.loads((target / 'Cargo.toml').read_text())
                print('RUST', name, 'edition', manifest.get('package', {}).get('edition', 'workspace'))
            if row['status'] in ('platform-limited', 'workspace-limited', 'extension'):
                print('LIMITATION', name, row.get('limitation', 'Requires manual runtime verification'))
        print('BLOCKED' if problems else 'CHECKED', name, '; '.join(problems))
        failures += bool(problems)
    print('Readiness checks do not replace tests or runtime verification.')
    return int(bool(failures))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO_DIR.parent, help='Directory containing sibling components')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    for action in ('setup', 'doctor', 'test'):
        item = sub.add_parser(action)
        item.add_argument('--profile', choices=(*PROFILES, 'all'), default='core')
        item.add_argument('--component', help='One component and its dependencies instead of a profile')
        if action == 'setup':
            item.add_argument('--no-build', action='store_true', help='Prepare sources and package environments without compiling Rust/Go')
    run = sub.add_parser('run')
    run.add_argument('component', nargs='?', default='CybCore')
    serve = sub.add_parser('serve')
    serve.add_argument('component', nargs='?', default='cybOS')
    serve.add_argument('--port', type=int, default=8004)
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 12):
            raise SetupError('Python 3.12 or newer is required')
        graph = catalog()
        root = args.root.resolve()
        if args.action == 'list':
            for row in graph.values():
                print(f"{row['name']:25} {row['status']:18} {row['role']}")
            return 0
        if args.action in ('setup', 'doctor', 'test'):
            rows = select(graph, [args.component]) if args.component else profile(graph, args.profile)
            if args.action == 'setup':
                return setup(root, rows, build=not args.no_build)
            if args.action == 'doctor':
                return readiness(root, rows)
            failures = 0
            for row in rows:
                command = row.get('test_command')
                if not command:
                    print('MANUAL', row['name'], row.get('limitation', 'No automated test command'))
                    continue
                target = checkout(root, row)
                if not target.is_dir():
                    raise SetupError(f"{row['name']}: checkout missing; run setup")
                failures += run_command(python_command(command, target), target) != 0
            return int(bool(failures))
        row = graph.get(args.component)
        if row is None:
            raise SetupError('Unknown component: ' + args.component)
        if row['status'] == 'planned':
            raise SetupError(args.component + ': planned, no executable implementation')
        target = checkout(root, row)
        if not target.is_dir():
            raise SetupError(args.component + ': checkout missing; run setup')
        if args.action == 'serve':
            if not row.get('web_entry') or not (target / row['web_entry']).is_file():
                raise SetupError(args.component + ': no static web entry')
            if not 1024 <= args.port <= 65535:
                raise SetupError('Port must be between 1024 and 65535')
            return run_command([sys.executable, '-m', 'http.server', str(args.port), '--bind', '127.0.0.1'], target)
        command = row.get('run_command')
        if not command:
            raise SetupError(args.component + ': no process command; use serve for static apps or test for libraries')
        return run_command(python_command(command, target), target)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
