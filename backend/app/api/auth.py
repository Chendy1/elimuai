from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import (
    SESSION_COOKIE,
    client_ip,
    enforce_rate_limit,
    get_session_context,
    require_csrf,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    SessionResponse,
    UserOut,
)
from app.services import auth as auth_service
from app.services.email import EmailSender, get_email_sender

router = APIRouter(prefix="/auth", tags=["auth"])

HOUR = 3600


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(f"register:ip:{client_ip(request)}", 10, HOUR)
    try:
        user = auth_service.create_user(
            db, email=body.email, password=body.password, display_name=body.display_name
        )
    except auth_service.EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="Unable to register with these details.")
    return user


@router.post("/login", response_model=SessionResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_rate_limit(f"login:ip:{client_ip(request)}", 30, 60)
    enforce_rate_limit(f"login:email:{body.email}", 8, 15 * 60)
    user = auth_service.authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    session, raw_token = auth_service.create_session(db, user)
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        raw_token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return SessionResponse(user=UserOut.model_validate(user), csrf_token=session.csrf_token)


@router.get("/me", response_model=SessionResponse)
def me(ctx: auth_service.AuthContext = Depends(get_session_context)):
    return SessionResponse(user=UserOut.model_validate(ctx.user), csrf_token=ctx.session.csrf_token)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    ctx: auth_service.AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> None:
    auth_service.revoke_session(db, ctx.session)
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post("/password-reset/request", response_model=MessageResponse, status_code=202)
def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
):
    enforce_rate_limit(f"reset:ip:{client_ip(request)}", 5, HOUR)
    enforce_rate_limit(f"reset:email:{body.email}", 3, HOUR)
    user = auth_service.get_user_by_email(db, body.email)
    if user is not None and user.is_active:
        token = auth_service.create_reset_token(db, user)
        base = get_settings().frontend_url.rstrip("/")
        sender.send_password_reset(user.email, f"{base}/reset-password?token={token}")
    return MessageResponse(message="If an account exists for that email, a reset link has been sent.")


@router.post("/password-reset/confirm", status_code=204)
def confirm_password_reset(
    body: PasswordResetConfirm, request: Request, db: Session = Depends(get_db)
) -> None:
    enforce_rate_limit(f"reset-confirm:ip:{client_ip(request)}", 10, HOUR)
    if not auth_service.consume_reset_token(db, body.token, body.new_password):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")
