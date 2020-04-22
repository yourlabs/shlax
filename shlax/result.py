class Result:
    def __init__(self, target, action):
        self.target = target
        self.action = action
        self.status = 'pending'
        self.exception = None


class Results(list):
    def new(self, target, action):
        result = Result(target, action)
        self.append(result)
        return result
