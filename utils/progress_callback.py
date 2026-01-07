"""Thread-safe progress reporting for GUI updates."""

import queue


class ProgressCallback:
    """
    Thread-safe progress reporting mechanism for long-running operations.

    Uses a queue to send messages from worker threads to the main GUI thread.
    This is necessary because Tkinter is not thread-safe and all UI updates
    must happen in the main thread.

    Message Types:
        - progress: Progress update with current/total values
        - log: Log message with severity level
        - complete: Operation completion signal
        - error: Error message

    Example:
        # In worker thread
        callback = ProgressCallback(queue_obj)
        callback.log("Starting download...")
        callback.update('download', 1024, 10240, "Downloaded 1KB/10KB")
        callback.complete(True, "Download successful")

        # In main thread (poll queue)
        while not queue.empty():
            msg = queue.get_nowait()
            if msg['type'] == 'progress':
                progress_bar.set(msg['current'] / msg['total'] * 100)
    """

    def __init__(self, queue_obj):
        """
        Initialize progress callback with a queue.

        Args:
            queue_obj (queue.Queue): Thread-safe queue for message passing
        """
        self.queue = queue_obj

    def update(self, operation, current, total, message=""):
        """
        Send progress update to GUI thread.

        Args:
            operation (str): Operation identifier (e.g., 'download', 'transcribe', 'analyze')
            current (int/float): Current progress value
            total (int/float): Total progress value
            message (str, optional): Additional context message
        """
        self.queue.put({
            'type': 'progress',
            'operation': operation,
            'current': current,
            'total': total,
            'message': message,
            'percent': (current / total * 100) if total > 0 else 0
        })

    def log(self, message, level='info'):
        """
        Send log message to GUI thread.

        Args:
            message (str): Log message text
            level (str): Log level - 'info', 'warning', 'error', 'debug'
        """
        self.queue.put({
            'type': 'log',
            'message': message,
            'level': level
        })

    def complete(self, success, message=""):
        """
        Signal operation completion.

        Args:
            success (bool): Whether operation completed successfully
            message (str, optional): Completion message (success or error details)
        """
        self.queue.put({
            'type': 'complete',
            'success': success,
            'message': message
        })

    def error(self, message, exception=None):
        """
        Send error message to GUI thread.

        Args:
            message (str): Error description
            exception (Exception, optional): Exception object for details
        """
        error_details = f"{message}"
        if exception:
            error_details += f"\n\nException: {type(exception).__name__}: {str(exception)}"

        self.queue.put({
            'type': 'error',
            'message': error_details
        })
