from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from decouple import config

class Auth:

    security = HTTPBearer()

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        if credentials.scheme != "Bearer" or credentials.credentials != config('MAGENTO_TOKEN'):
            raise HTTPException(status_code=401, detail="Token non valido o mancante")
        return credentials.credentials
