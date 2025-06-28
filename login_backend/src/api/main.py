from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="Login Backend API",
    description=(
        "API for login authentication. Accepts email and password, "
        "validates against a dummy account, and returns JSON results."
    ),
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Login endpoints",
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev you can specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy credentials for authentication
DUMMY_EMAIL = "test@example.com"
DUMMY_PASSWORD = "password123"


class LoginRequest(BaseModel):
    """Request body for login endpoint."""
    email: EmailStr = Field(
        ...,
        description="The user's email address."
    )
    password: str = Field(
        ...,
        min_length=1,
        description="The user's password."
    )


class LoginResponse(BaseModel):
    """Response body for a successful login."""
    success: bool = Field(
        ...,
        description="Whether the login was successful."
    )
    message: str = Field(
        ...,
        description="A message describing the login result."
    )


# PUBLIC_INTERFACE
@app.post(
    "/api/login",
    response_model=LoginResponse,
    tags=["Authentication"],
    summary="Login with email and password",
    description=(
        "Accepts email and password in the request body, validates against a dummy account.<br>"
        "Returns success (true/false) and a message describing the result."
    ),
    responses={
        200: {
            "description": "Login result (success or failure)",
            "model": LoginResponse,
        },
        400: {
            "description": "Missing or invalid input"
        }
    }
)
async def login_endpoint(
    login_req: LoginRequest = Body(..., description="The user's credentials (email and password)")
) -> LoginResponse:
    """
    Handles user login by validating the provided email and password against a dummy account.

    Args:
        login_req (LoginRequest): The login credentials.

    Returns:
        LoginResponse: Success status and message.
    """
    # Validate credentials
    if login_req.email == DUMMY_EMAIL and login_req.password == DUMMY_PASSWORD:
        return LoginResponse(success=True, message="Login successful!")
    # Explicitly check the dummy email for clearer errors:
    if login_req.email != DUMMY_EMAIL:
        return LoginResponse(success=False, message="Invalid email or password.")
    return LoginResponse(success=False, message="Invalid email or password.")


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Basic health check endpoint",
    response_description="Service status",
)
def health_check():
    """Health check for service liveness."""
    return {"message": "Healthy"}
