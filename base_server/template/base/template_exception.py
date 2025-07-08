class TemplateException(Exception):
    def __init__(self, error_code: int, message: str = "", response=None):
        super().__init__(message)
        self.error_code = error_code
        self.response = response
        self.stack_trace = ""