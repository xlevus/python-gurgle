from functools import wraps

from colours import colour


def requires_gurgle(func):
    @wraps(func)
    def _inner(args, daemon):
        if not daemon.status():
            print colour.red("Gurgle is not running.")
            exit(1)
        return func(args, daemon)
    return _inner


def start(args, daemon):
    if not daemon.status():
        print colour.blue("Starting Gurgle...")
        daemon.start(
            gurglefile=args.gurglefile,
            port=args.port)
    else:
        print colour.red("Gurgle is already running.")


@requires_gurgle
def terminate(args, daemon):
    print colour.blue("Terminating Gurgle...")
    daemon.stop()


@requires_gurgle
def status(args, daemon):
    pass
