# Shlax: Pythonic automation tool

Shlax is a Python framework for system automation, initially with the purpose
of replacing docker, docker-compose and ansible with a single tool, with the
purpose of code-reuse. It may be viewed as "async fabric rewrite by a
megalomanic Django fanboy".

The pattern resolves around two moving parts: Actions and Targets.

## Action

An action is a function that takes a target argument, it may execute nested
actions by passing over the target argument which collects the results.

Example:

```python
async def hello_world(target):
    """Bunch of silly commands to demonstrate action programming."""
    await target.mkdir('foo')
    python = await target.which('python3', 'python')
    await target.exec(f'{python} --version > foo/test')
    version = target.exec('cat foo/test').output
    print('version')
```

### Recursion

An action may call other actions recursively. There are two ways:

```python
async def something(target):
    # just run the other action code
    hello_world(target)

    # or delegate the call to target
    target(hello_world)
```

In the first case, the resulting count of ran actions will remain 1:
"something" action.

In the second case, the resulting count of ran actions will be 2: "something"
and "hello_world".

### Callable classes

Actually in practice, Actions are basic callable Python classes, here's a basic
example to run a command:

```python
class Run:
    def __init__(self, cmd):
        self.cmd = cmd

    async def __call__(self, target):
        return await target.exec(self.cmd)
```

This allows to create callable objects which may be called just like functions
and as such be appropriate actions, instead of:

```python
async def one(target):
    target.exec('one')

async def two(target):
    target.exec('two')
```

You can do:

```python
one = Run('one')
two = Run('two')
```

### Parallel execution

Actions may be executed in parallel with an action named ... Parallel. This
defines an action that will execute three actions in parallel:

```python
action = Parallel(
    hello_world,
    something,
    Run('echo hi'),
)
```

In this case, all actions must succeed for the parallel action to be considered
a success.

### Methods

An action may also be a method, as long as it just takes a target argument, for
example:

```python
class Thing:
    def start(self, target):
        """Starts thing"""

    def stop(self, target):
        """Stops thing"""

action = Thing().start
```

### Cleaning

If an action defines a `clean` method, it will always be called wether or not
the action succeeded. Example:

```python
class Thing:
    def __call__(self, target):
        """Do some thing"""

    def clean(self, target):
        """Clean-up target after __call__"""
```

## Target

A Target is mainly an object providing an abstraction layer over the system we
want to automate with actions. It defines functions to execute a command, mount
a directory, copy a file, manage environment variables and so on.

### Pre-configuration

A Target can be pre-configured with a list of Actions in which case calling the
target without argument will execute its Actions until one fails by raising an
Exception:

```python
say_hello = Localhost(
    hello_world,
    Run('echo hi'),
)
await say_hello()
```

### Results

Every time a target execute an action, it will set the "status" attribute on it
to "success" or "failure", and add it to the "results" attribute:

```
say_hello = Localhost(Run('echo hi'))
await say_hello()
say_hello.results  # contains the action with status="success"
```
