Gurgle
======

A simple process runner, akin to Foreman/Honcho.


Why not Foreman/Honcho?
-----------------------
 * Procfiles aren't scriptable
 * You can't restart individual processes

Additionally, I was intending to add support for healthchecks, auto-restarts,
and a web UI.


Installation
------------
```
pip install git+ssh://git@github.com/xlevus/python-gurgle.git
```

Running
-------

1. Create a `gurglefile.py` file in your project (see `example/gurglefile.py`)

2. Start the daemon:
   ```
   $ gurgle daemon
   ```

3. Start your processes:
   ```
   $ gurgle start
   ```
   
4. Check the status:
   ```
   $ gurgle status
   ```
   
4. Watch the output:
   ```
   $ gurgle watch
   ```
