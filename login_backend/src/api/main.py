import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, status, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Dict
from threading import Lock

app = FastAPI(
    title="Login Backend API",
    description=(
        "API for login authentication and registration. "
        "Accepts email and password, "
        "validates against static and in-memory accounts, "
        "and returns JSON results."
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
# (emails stored in lowercase for case-insensitive comparison)
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


# Setup basic logging (you can adjust level or handlers as needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("register_logger")


# PUBLIC_INTERFACE
@app.post(
    "/api/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    summary="Register a new user account",
    description=(
        "Accepts email and password (len \u2265 6), performs basic validation, stores in memory, "
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

    Validates email format and minimum password length (\u2265 6).
    Prevents registration if the email is already registered (either as dummy or in-memory,
    case-insensitive).
    Stores accounts in-memory (lost on backend restart).

    Args:
        reg_req (RegisterRequest): The registration fields.

    Returns:
        RegisterResponse: Success or error message.
    """
    # Extra logging for debugging registration flow

    logger.info("--- REGISTER ENDPOINT CALLED ---")
    # Log the full payload received
    logger.info("Raw registration request payload (RegisterRequest): %s", reg_req)
    # Log current registered users before registration
    logger.info("Registered users BEFORE: %s", _registered_users)

    # Normalize email to lowercase for consistent duplicate checks
    normalized_email = reg_req.email.lower()

    logger.info("Attempting registration for: %s", normalized_email)

    if normalized_email == DUMMY_EMAIL.lower():
        logger.warning(
            "Registration attempt with dummy email: %s", normalized_email
        )
        logger.info(
            "Registered users AFTER (no change): %s", _registered_users
        )
        return RegisterResponse(
            success=False,
            message="This email is already registered (dummy account)."
        )

    with _reg_lock:
        # Log the keys being compared
        logger.info("Registered user keys: %s", list(_registered_users.keys()))
        if normalized_email in (mail.lower() for mail in _registered_users.keys()):
            logger.warning(
                "Duplicate registration attempt: %s", normalized_email
            )
            logger.info(
                "Registered users AFTER (no change): %s", _registered_users
            )
            return RegisterResponse(
                success=False,
                message="This email is already registered."
            )
        # Store user (password must meet min_length=6, enforced by Pydantic)
        _registered_users[normalized_email] = reg_req.password
        logger.info(
            "User %s registered successfully.",
            normalized_email
        )
        logger.info("Registered users AFTER: %s", _registered_users)

    return RegisterResponse(
        success=True,
        message="Registration successful."
    )


# PUBLIC_INTERFACE
@app.post(
    "/api/register-debug",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    summary="Register a new user account (debug logging version)",
    description=(
        "**Debug version** of registration endpoint. "
        "Logs the incoming raw JSON body and shows matched/mismatched fields "
        "for troubleshooting. "
        "All behaviors except logging are identical to "
        "`/api/register`."
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
async def register_endpoint_debug(
    request: Request,
    reg_req: RegisterRequest = Body(
        ...,
        description="Registration request containing email and password"
    ),
) -> RegisterResponse:
    """
    Handles user registration with **extra logging** of the raw incoming body for debugging field names and request parsing.
    Otherwise identical to /api/register.

    Args:
        request (Request): The incoming FastAPI request object (for logging raw body).
        reg_req (RegisterRequest): The registration fields.

    Returns:
        RegisterResponse: Success or error message.
    """
    logger.info("--- REGISTER ENDPOINT (DEBUG) CALLED ---")

    # Log the raw body (will work as long as this is the first body read!)
    raw_bytes = await request.body()
    try:
        raw_str = raw_bytes.decode("utf-8")
    except Exception:
        raw_str = str(raw_bytes)
    logger.info("Raw JSON received: %s", raw_str)

    try:
        import json
        json_obj = json.loads(raw_str)
        logger.info("Parsed incoming fields: %s", list(json_obj.keys()))
    except Exception as e:
        logger.error("Could not parse body as JSON: %s", e)

    logger.info("Parsed RegisterRequest model: %s", reg_req.dict())

    # Duplicate logic from original register handler:
    normalized_email = reg_req.email.lower()
    logger.info("Attempting registration for: %s", normalized_email)
    logger.info("Registered users BEFORE: %s", _registered_users)

    if normalized_email == DUMMY_EMAIL.lower():
        logger.warning(
            "Registration attempt with dummy email: %s", normalized_email
        )
        logger.info(
            "Registered users AFTER (no change): %s", _registered_users
        )
        return RegisterResponse(
            success=False,
            message="This email is already registered (dummy account)."
        )

    with _reg_lock:
        logger.info("Registered user keys: %s", list(_registered_users.keys()))
        if normalized_email in (mail.lower() for mail in _registered_users.keys()):
            logger.warning(
                "Duplicate registration attempt: %s", normalized_email
            )
            logger.info(
                "Registered users AFTER (no change): %s", _registered_users
            )
            return RegisterResponse(
                success=False,
                message="This email is already registered."
            )
        _registered_users[normalized_email] = reg_req.password
        logger.info(
            "User %s registered successfully.",
            normalized_email
        )
        logger.info("Registered users AFTER: %s", _registered_users)

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
