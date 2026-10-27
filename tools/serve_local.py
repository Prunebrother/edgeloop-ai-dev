"""AGPL-3.0-only. Local static UI only: never serve AI memory, Git or Python."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
PUBLIC={'index.html','sw.js','manifest.json','README.md','CHANGELOG.md','LICENSE','FORK_README.md','NOTICE_FORK.md'}

def public_file(raw, root=ROOT):
    path=unquote(urlsplit(raw).path).lstrip('/') or 'index.html'
    parts=PurePosixPath(path).parts
    if any(p.startswith('.') for p in parts): return None
    allowed=path in PUBLIC or (len(parts)==1 and parts[0].startswith('icon') and Path(path).suffix in {'.svg','.png'}) or (path.startswith('src/js/') and path.endswith('.js')) or (path.startswith('src/css/') and path.endswith('.css')) or (path.startswith('src/assets/characters/') and Path(path).suffix in {'.png','.webp','.jpg','.jpeg','.svg'})
    target=root/path
    if target.absolute()!=target.resolve():return None
    if not allowed or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()): return None
    if any(p.startswith('.') for p in target.resolve().relative_to(root.resolve()).parts):return None
    return target if target.is_file() else None

class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        if public_file(self.path,Path(self.directory)) is None:
            self.send_error(404);return None
        return super().send_head()
    def list_directory(self,path):self.send_error(404);return None

if __name__=='__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8770
    with ThreadingHTTPServer(('127.0.0.1',port),partial(Handler,directory=str(ROOT))) as server:
        print(f'Original EdgeLoop: http://127.0.0.1:{port}/ (AI optional)',flush=True)
        server.serve_forever()
