from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, BigInteger, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.transfers import TransferStatus
from app.infrastructure.db.base import Base, TimestampMixin


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    folders: Mapped[list[FolderModel]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    transfers: Mapped[list[TransferModel]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class FolderModel(TimestampMixin, Base):
    __tablename__ = "folders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    owner: Mapped[UserModel] = relationship(back_populates="folders", foreign_keys=[owner_id])
    parent: Mapped[FolderModel | None] = relationship(remote_side="FolderModel.id")
    transfers: Mapped[list[TransferModel]] = relationship(back_populates="folder")


class TransferModel(TimestampMixin, Base):
    __tablename__ = "transfers"
    __table_args__ = (
        UniqueConstraint("transfer_code", name="uq_transfers_transfer_code"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    folder_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"), index=True)
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transfer_code: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=TransferStatus.UPLOADING.value, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sha256_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    owner: Mapped[UserModel] = relationship(back_populates="transfers", foreign_keys=[owner_id])
    folder: Mapped[FolderModel | None] = relationship(back_populates="transfers", foreign_keys=[folder_id])
