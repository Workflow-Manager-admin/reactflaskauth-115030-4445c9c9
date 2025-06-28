from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, status
from pydantic import BaseModel, EmailStr, Field
from typing import Dict
from threading import Lock

app = FastAPI(
    title="Login Backend API",
    description=(
        "API for login authentication and registration. Accepts email and password, "
        "validates against static and in-memory accounts, and returns JSON results."
    ),
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Login and registration endpoints",
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

# In-memory storage for registered users
_registered_users: Dict[str, str] = {}
_reg_lock = Lock()


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
class RegisterRequest(BaseModel):
    """Request body for register endpoint."""
    email: EmailStr = Field(
        ...,
        description="The user's email address."
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Password. Must be at least 6 characters."
    )


# PUBLIC_INTERFACE
class RegisterResponse(BaseModel):
    """Response for user registration attempts."""
    success: bool = Field(..., description="Indicates if registration succeeded")
    message: str = Field(..., description="A descriptive result message")


# PUBLIC_INTERFACE
@app.post(
    "/api/login",
    response_model=LoginResponse,
    tags=["Authentication"],
    summary="Login with email and password",
    description=(
        "Accepts email and password in the request body, validates against a dummy account."
        "<br>Returns success (true/false) and a message describing the result."
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
    # Validate credentials against static dummy account
    if login_req.email == DUMMY_EMAIL and login_req.password == DUMMY_PASSWORD:
        return LoginResponse(success=True, message="Login successful!")
    # Check in-memory registered users
    with _reg_lock:
        if (
            login_req.email in _registered_users
            and _registered_users[login_req.email] == login_req.password
        ):
            return LoginResponse(success=True, message="Login successful (registered user)!")
    # Invalid credentials
    return LoginResponse(success=False, message="Invalid email or password.")


# PUBLIC_INTERFACE
@app.post(
    "/api/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    summary="Register a new user account",
    description=(
        "Accepts email and password (len ≥ 6), performs basic validation, stores in memory, "
        "prevents duplicates. Returns a clear success or error message."
    ),
    responses={
        200: {
            "description": "Registration result (success or error)",
            "model": RegisterResponse,
        },
        400: {
            "description": "Invalid input or duplicate email",
        }
    }
)
async def register_endpoint(
    reg_req: RegisterRequest = Body(
        ...,
        description="Registration request containing email and password"
    )
) -> RegisterResponse:
    """
    Handles user registration.

    Validates email format and minimum password length (≥ 6).
    Prevents registration if the email is already registered (either as dummy or in-memory).
    Stores accounts in-memory (lost on backend restart).

    Args:
        reg_req (RegisterRequest): The registration fields.

    Returns:
        RegisterResponse: Success or error message.
    """
    if reg_req.email == DUMMY_EMAIL:
        return RegisterResponse(
            success=False,
            message="This email is already registered (dummy account)."
        )

    with _reg_lock:
        if reg_req.email in _registered_users:
            return RegisterResponse(
                success=False,
                message="This email is already registered."
            )
        # Store user (password must meet min_length=6, enforced by Pydantic)
        _registered_users[reg_req.email] = reg_req.password

    return RegisterResponse(
        success=True,
        message="Registration successful."
    )


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
