"""AGPL-3.0-only. Install the complete Windows bundle. Run by the setup program with its own Python.

Downloads the release parts (resuming, checked against the SHA-256 sums built into the setup
program), streams them through one tar extraction, verifies every bundled file, then prepares the
offline Python environment. Parts placed next to the setup program are used instead of downloading.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
from urllib.request import Request, build_opener

CHUNK = 1 << 20
HTTP = build_opener()


LOG = None


def say(text, end='\n'):
    print(text, end=end, flush=True)
    if LOG and end == '\n':
        LOG.write(text.lstrip('\r') + '\n')
        LOG.flush()


def gib(n):
    return f'{n / 2**30:.2f} GB'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(url, target, size, sha256, attempts=5):
    partial = target.with_name(target.name + '.partial')
    for attempt in range(1, attempts + 1):
        have = partial.stat().st_size if partial.exists() else 0
        if have > size:
            partial.unlink()
            have = 0
        try:
            if have < size:
                request = Request(url, headers={'Range': f'bytes={have}-'} if have else {})
                with HTTP.open(request, timeout=60) as response:
                    if have and response.status != 206:
                        have = 0  # The server ignored the range: start over.
                    with partial.open('ab' if have else 'wb') as stream:
                        last = 0
                        while chunk := response.read(CHUNK):
                            stream.write(chunk)
                            have += len(chunk)
                            if time.monotonic() - last > 1:
                                last = time.monotonic()
                                say(f'\r  {target.name}: {have * 100 // size}% ({gib(have)} of {gib(size)})   ', end='')
            say(f'\r  {target.name}: checking...                              ', end='')
            if partial.stat().st_size == size and digest(partial) == sha256:
                partial.replace(target)
                say(f'\r  {target.name}: done                                    ')
                return
            partial.unlink()
            say(f'\n  {target.name} failed its checksum; downloading again.')
        except OSError as exc:
            say(f'\n  Download interrupted ({exc}); retrying ({attempt}/{attempts})...')
            time.sleep(min(30, 3 * attempt))
    raise RuntimeError(f'Could not download {target.name}. Check the connection and run setup again; finished parts are kept.')


def acquire(parts, base_url, cache, offline):
    found = []
    for index, part in enumerate(parts, 1):
        say(f'Part {index} of {len(parts)}:')
        for folder in [offline, cache]:
            candidate = folder / part['name'] if folder else None
            if candidate and candidate.is_file() and candidate.stat().st_size == part['bytes']:
                say(f'  {part["name"]}: checking existing file...')
                if digest(candidate) == part['sha256']:
                    found.append(candidate)
                    break
        else:
            target = cache / part['name']
            download(f'{base_url}/{part["name"]}', target, part['bytes'], part['sha256'])
            found.append(target)
    return found


class Chain:
    """The parts read back to back as one stream, without first joining them on disk."""

    def __init__(self, paths):
        self.paths, self.stream = list(paths), None

    def read(self, n=-1):
        while self.paths or self.stream:
            if self.stream is None:
                self.stream = self.paths.pop(0).open('rb')
            data = self.stream.read(n)
            if data:
                return data
            self.stream.close()
            self.stream = None
        return b''


def extract(parts, destination):
    incoming = destination.with_name(destination.name + '.incoming')
    if incoming.exists():
        shutil.rmtree(incoming)
    incoming.mkdir(parents=True)
    say('Extracting...')
    count = 0
    with tarfile.open(fileobj=Chain(parts), mode='r|gz') as archive:
        for member in archive:
            archive.extract(member, incoming, filter='data')
            count += 1
            if count % 500 == 0:
                say(f'\r  {count} files', end='')
    say(f'\r  {count} files extracted.')
    return incoming


def verify(root):
    spec = importlib.util.spec_from_file_location('edgeloop_bundle', root / 'tools/bundle.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    say('Verifying bundled files...')
    module.verify(root)


def prepare_python(root):
    say('Installing the offline Python environment...')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PIP_DISABLE_PIP_VERSION_CHECK='1')

    def run(*args):
        result = subprocess.run([str(a) for a in args], cwd=root, env=env, capture_output=True, text=True, errors='replace')
        if result.returncode:
            # The tool's own output is the reason; keep it in the setup log.
            say((result.stdout + result.stderr).strip()[-4000:])
            result.check_returncode()
    extra = json.loads((root / 'release-inputs.json').read_text()).get('windows', {}).get('extra_requirements', [])
    run(root / 'runtime/python/python.exe', '-m', 'venv', root / '.venv')
    python = root / '.venv/Scripts/python.exe'
    run(python, '-m', 'pip', 'install', '--no-index', '--find-links', root / 'wheelhouse', '-r', root / 'requirements.lock',
        'setuptools==84.2.1', 'wheel==0.48.0', *extra)
    run(python, '-m', 'pip', 'install', '--no-index', '--find-links', root / 'wheelhouse', '--no-build-isolation', '--no-deps', '-e', root)


def configure(root, data):
    # New installs start with a real companion. Existing settings are never changed.
    data.mkdir(parents=True, exist_ok=True)
    config = data / 'selection.json'
    if not config.exists():
        default = json.loads((root / 'release-inputs.json').read_text())['default_model']
        config.write_text(json.dumps({'config': {'model': default, 'thinking': False}}) + '\n')


def stop_installed(folder):
    """Stop a running EdgeLoop AI before its files are replaced (running programs lock files on Windows)."""
    for release in sorted(folder.glob('v*')):
        python = release / '.venv/Scripts/python.exe'
        launcher = release / 'tools/windows/edgeloop_ai_windows.py'
        if python.is_file() and launcher.is_file():
            subprocess.run([str(python), str(launcher), 'stop', '--quiet'], check=False)


def remove_older(folder, keep):
    for release in folder.glob('v*'):
        if release.is_dir() and release.name != keep.name and not release.name.endswith(('.incoming', '.previous')):
            say(f'Removing the previous version {release.name}...')
            shutil.rmtree(release, ignore_errors=True)


def install(manifest, destination, cache, offline, data):
    cache.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    parts = acquire(manifest['parts'], manifest['base_url'], cache, offline)
    incoming = extract(parts, destination)
    try:
        verify(incoming)
    except BaseException:
        shutil.rmtree(incoming, ignore_errors=True)
        raise
    stop_installed(destination.parent)
    # Python and pip record absolute paths, so the environment is built in its final place.
    previous = destination.with_name(destination.name + '.previous')
    if previous.exists():
        shutil.rmtree(previous)
    if destination.exists():
        destination.rename(previous)
    incoming.rename(destination)
    try:
        prepare_python(destination)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        if previous.exists():
            previous.rename(destination)
        raise
    shutil.rmtree(previous, ignore_errors=True)
    remove_older(destination.parent, destination)
    configure(destination, data)
    for part in parts:
        if part.parent == cache:
            part.unlink()
    say('EdgeLoop AI is installed.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--dest', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--offline', type=Path, help='Folder that may already hold the parts')
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--log', type=Path, help='Also write progress to this file')
    args = parser.parse_args(argv)
    global LOG
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        LOG = args.log.open('a', encoding='utf-8')
    manifest = json.loads(args.manifest.read_text())
    say(f'EdgeLoop AI {manifest["version"]} setup. Download about {gib(sum(p["bytes"] for p in manifest["parts"]))}.')
    install(manifest, args.dest, args.cache, args.offline, args.data)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as exc:
        say(f'\nInstallation failed: {exc}')
        sys.exit(1)
