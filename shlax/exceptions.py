class ShlaxException(Exception):
    pass


class Mistake(ShlaxException):
    pass


class WrongResult(ShlaxException):
    def __init__(self, proc):
        self.proc = proc

        msg = f'FAIL exit with {proc.rc} ' + proc.args[0]

        if not proc.debug or 'cmd' not in str(proc.debug):
            msg += '\n' + proc.cmd

        if not proc.debug or 'out' not in str(proc.debug):
            msg += '\n' + proc.out
            msg += '\n' + proc.err

        super().__init__(msg)
