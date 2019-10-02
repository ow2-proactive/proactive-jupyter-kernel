class PragmaError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ParsingError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ParameterError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ConfigError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ResultError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class JobValidationError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}
