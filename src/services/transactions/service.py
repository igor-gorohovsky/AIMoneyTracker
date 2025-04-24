from db.manager import DBManager
from db.models import Transaction


class TransactionsService:
    def __init__(self, db_manager: DBManager) -> None:
        self._db_manager = db_manager

    def create_transaction(
        self,
        from_account_id: int,
        currency_iso_code: str,
        base_currency_amount: float,
        account_currency_amount: float,
    ) -> Transaction:
        pass
