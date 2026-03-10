class AppError(Exception):
    def __init__(self, user_message, *, detail=""):
        super().__init__(detail or user_message)
        self.user_message = user_message
        self.detail = detail or user_message


class GithubApiError(AppError):
    def __init__(self, user_message, *, status_code=None, detail=""):
        super().__init__(user_message, detail=detail)
        self.status_code = status_code


class GithubRateLimitError(GithubApiError):
    def __init__(self, user_message, *, status_code=None, detail="", reset_at=None):
        super().__init__(user_message, status_code=status_code, detail=detail)
        self.reset_at = reset_at


class GithubResourceNotFoundError(GithubApiError):
    pass


class GithubOAuthError(AppError):
    pass


class OpenAIAnalysisError(AppError):
    pass


class ExportError(AppError):
    pass
