from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    verify_password,
    decode_token,
    get_current_user
)
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.services.email_service import send_password_reset_email
from app.schemas.user import (
    UserCreate, UserResponse, Token, LoginRequest, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username),
        User.deleted_at.is_(None)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.USER,
        is_active=True,
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration
    audit_log = AuditLog(
        user_id=new_user.id,
        action="user_registered",
        resource_type="user",
        resource_id=new_user.id
    )
    db.add(audit_log)
    db.commit()

    return new_user


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT tokens"""
    user = authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Log login
    audit_log = AuditLog(
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=user.id
    )
    db.add(audit_log)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        payload = decode_token(refresh_data.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Verify user exists and is active
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        access_token = create_access_token(data={"sub": user.id})
        new_refresh_token = create_refresh_token(data={"sub": user.id})

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user (client should discard tokens)"""
    # Log logout
    audit_log = AuditLog(
        user_id=current_user.id,
        action="user_logout",
        resource_type="user",
        resource_id=current_user.id
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email.

    Always returns the same response regardless of whether the email exists,
    to prevent account enumeration. The reset link is sent by background task
    so the response is immediate. If SMTP is not configured, the link is
    printed to the server console instead.
    """
    _SAFE_RESPONSE = {"message": "If an account exists with this email, a password reset link has been sent."}

    user = db.query(User).filter(
        User.email == request.email,
        User.deleted_at.is_(None)
    ).first()

    if not user or not user.is_active:
        return _SAFE_RESPONSE

    # Create password reset token (JWT, 1-hour expiry)
    reset_token = create_password_reset_token(user.id)

    # Log the request
    db.add(AuditLog(
        user_id=user.id,
        action="password_reset_requested",
        resource_type="user",
        resource_id=user.id,
    ))
    db.commit()

    # Send the email in the background so the response is instant
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)

    return _SAFE_RESPONSE


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid reset token"""
    # Verify the token
    user_id = verify_password_reset_token(request.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    # Validate new password (minimum 8 characters)
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    # Log password reset
    audit_log = AuditLog(
        user_id=user.id,
        action="password_reset_completed",
        resource_type="user",
        resource_id=user.id
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Password has been reset successfully"}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    # Log password change
    audit_log = AuditLog(
        user_id=current_user.id,
        action="password_changed",
        resource_type="user",
        resource_id=current_user.id
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Password changed successfully"}
