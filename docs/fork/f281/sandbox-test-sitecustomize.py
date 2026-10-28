# Test process only: asyncio self-pipe writes are EPERM in this sandbox.
# Poll the existing selector so in-process AnyIO/TestClient thread work can run.
import selectors
_original=selectors.EpollSelector.select
def polling(self,timeout=None):return _original(self,0.02 if timeout is None else min(timeout,0.02))
selectors.EpollSelector.select=polling
