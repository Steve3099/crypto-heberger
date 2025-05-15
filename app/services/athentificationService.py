class AuthenticationService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def authenticate(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user and user.check_password(password):
            return user
        return None

    def register(self, username, password):
        if self.user_repository.find_by_username(username):
            raise ValueError("Username already exists")
        new_user = self.user_repository.create_user(username, password)
        return new_user