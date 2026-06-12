"""Invalid block access list storage-root tests for EIP-8268."""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    Hash,
    Op,
    Storage,
    Transaction,
)
from execution_testing.base_types import HashInt
from execution_testing.test_types.block_access_list import (
    BlockAccessList,
    StorageRoot,
)

from .spec import Spec, ref_spec_8268

REFERENCE_SPEC_GIT_PATH = ref_spec_8268.git_path
REFERENCE_SPEC_VERSION = ref_spec_8268.version

pytestmark = [pytest.mark.valid_from("Amsterdam"), pytest.mark.exception_test]


def modify_storage_root(
    address: Address,
    storage_root: StorageRoot,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Set an incorrect storage_root for a BAL account entry."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        found_address = False
        new_root = []
        for account_change in bal.root:
            if account_change.address == address:
                found_address = True
                new_account = account_change.model_copy(deep=True)
                new_account.storage_root = storage_root
                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found_address:
            raise ValueError(
                f"Address {address!r} not found in BAL to modify storage_root"
            )

        return BlockAccessList(root=new_root)

    return transform


def test_invalid_non_empty_storage_root(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A state-changing account with non-empty post-block storage must carry the
    actual post-block storage trie root.
    """
    sender = pre.fund_eoa(amount=10**18)
    storage = Storage({HashInt(1): HashInt(1)})
    contract = pre.deploy_contract(
        code=Op.STOP,
        storage=storage,
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=100_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            contract: Account(storage=storage),
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=1,
                                )
                            ],
                        ),
                    }
                ).modify(modify_storage_root(contract, Hash(b"\x99" * 32))),
            )
        ],
    )


def test_invalid_empty_storage_root_encoded_as_empty_trie_hash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A state-changing account with empty post-block storage must encode
    storage_root as the empty byte string, not the canonical empty trie hash.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=1,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=1,
                                )
                            ],
                        ),
                    }
                ).modify(
                    modify_storage_root(
                        receiver, Bytes(Spec.EMPTY_STORAGE_ROOT)
                    )
                ),
            )
        ],
    )
