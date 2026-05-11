"""线程池与主线程 UI 通信"""

import queue
import threading
import traceback
from typing import Callable, Any


class ThreadPool:
    """简易线程池：管理工作线程，通过 Queue 将结果安全传回主线程"""

    def __init__(self, on_error: Callable[[Exception], None] | None = None):
        self._queue: queue.Queue = queue.Queue()
        self._threads: list[threading.Thread] = []
        self._on_error = on_error or (lambda e: print(f"[Thread Error] {e}"))

    def submit(self, task: Callable, *args, callback: Callable[[Any], None] | None = None, **kwargs):
        """
        在后台线程执行 task(*args, **kwargs)。
        完成后通过 callback 在 poll() 调用时返回主线程结果。
        """

        def _wrapper():
            try:
                result = task(*args, **kwargs)
                self._queue.put(("done", result, callback))
            except Exception as e:
                traceback.print_exc()
                self._queue.put(("error", e, callback))

        t = threading.Thread(target=_wrapper, daemon=True)
        self._threads.append(t)
        t.start()

    def poll(self):
        """在主线程中调用（如通过 root.after），处理已完成的任务回调"""
        while not self._queue.empty():
            status, data, callback = self._queue.get_nowait()
            if status == "error":
                self._on_error(data)
            elif callback is not None:
                try:
                    callback(data)
                except Exception as e:
                    self._on_error(e)

    def shutdown(self, wait: bool = True):
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=1 if not wait else None)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown(wait=False)
