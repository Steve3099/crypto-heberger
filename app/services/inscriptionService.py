class InscriptionService:
    async def make_inscription(self, email: str, password: str,nom: str, prenom: str, pseudo: str):
        """Create a new user account."""
        # Here you would typically hash the password and save the user to a database.
        
        
        
        
        # For this example, we'll just return a success message.
        return {
            "message": "User registered successfully",
            "email": email,
            "nom": nom,
            "prenom": prenom,
            "pseudo": pseudo
        }