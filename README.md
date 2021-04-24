# Shlax: Pythonic automation tool

Shlax is a Python framework for system automation, initially with the purpose
of replacing docker, docker-compose and ansible with a single tool with the
purpose of code-reuse made possible by target abstraction.

## Development status: Design state

I got the thing to work with an ugly PoC that I basically brute-forced, I'm
currently rewriting the codebase with a proper design.

The stories are in development in this order:

- replacing docker build, that's in the state of polishing
- replacing docker-compose, not in use but the PoC works so far
- replacing ansible, also working in working PoC state, the shlax command line
  demonstrates

This project is supposed to unblock me from adding the CI feature to the
Sentry/GitLab/Portainer implementation I'm doing in pure python on top of
Django, CRUDLFA+ and Ryzom (isomorphic components in Python to replace
templates). So, as you can see, I'm really deep in it with a strong
determination.

Shlax builds its container itself, so check the shlaxfile.py of this repository
to see what it currently looks like, and check the build job of the CI pipeline
to see the output.

# Design

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

### Colorful actions

If an action defines a `colorize` method, it will be called with the colorset
as argument for every output, this allows to code custom output rendering.

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

```python
say_hello = Localhost(Run('echo hi'))
await say_hello()
say_hello.results  # contains the action with status="success"
```

## Targets as Actions: the nesting story

We've seen that any callable taking a target argument is good to be considered
an action, and that targets are callables.

To make a Target runnable like any action, all we had to do is add the target
keyword argument to `Target.__call__`.

But `target()` fills `self.results`, so nested action results would not
propagate to the parent target.

That's why if Target receives a non-None target argument, it will has to set
`self.parent` with it.

This allows nested targets to traverse parents and get to the root Target
with `target.caller`, where it can then attach results to.

This opens the nice side effect that a target implementation may call the
parent target if any, you could write a Docker target as such:

```python
class Docker(Target):
    def __init__(self, *actions, name):
        self.name = name
        super().__init__(*actions)

    async def exec(self, *args):
        return await self.parent.exec(*['docker', 'exec', self.name] + args)
```

This also means that you always need a parent with an exec implementation,
there are two:

- Localhost, executes on localhost
- Stub, for testing

The result of that design is that the following use cases are available:

```python
# This action installs my favorite package on any distro
action = Packages('python3')

# Run it right here: apt install python3
Localhost()(action)

# Or remotely: ssh yourhost apt install python3
Ssh(host='yourhost')(action)

# Let's make a container build receipe with that action
build = Buildah(package)

# Run it locally: buildah exec apt install python3
Localhost()(build)

# Or on a server: ssh yourhost build exec apt install python3
Ssh(host='yourhost')(build)

# Or on a server behingh a bastion:
# ssh yourbastion ssh yourhost build exec apt install python3
Localhost()(Ssh(host='bastion')(Ssh(host='yourhost')(build))

# That's going to do the same
Localhost(Ssh(
    Ssh(
        build,
        host='yourhost'
    ),
    host='bastion'
))()
```

## CLI

You can execute Shlax actions directly on the command line with the `shlax` CLI
command.

For your own Shlaxfiles, you can build your CLI with your favorite CLI
framework. If you decide to use `cli2`, then Shlax provides a thin layer on top
of it: Group and Command objects made for Shlax objects.

For example:

```python
yourcontainer = Container(
    build=Buildah(
        User('app', '/app', 1000),
        Packages('python', 'unzip', 'findutils'),
        Copy('setup.py', 'yourdir', '/app'),
        base='archlinux',
        commit='yourimage',
    ),
)


if __name__ == '__main__':
    print(Group(doc=__doc__).load(yourcontainer).entry_point())
```

The above will execute a cli2 command with each method of yourcontainer as a
sub-command.
