"""Reference spec for EIP-8268: Storage Roots in Block Access Lists."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8268 = ReferenceSpec(
    git_path="EIPS/eip-8268.md",
    version="2026-05-21 draft",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-8268."""

    EMPTY_STORAGE_ROOT = bytes.fromhex(
        "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    )
