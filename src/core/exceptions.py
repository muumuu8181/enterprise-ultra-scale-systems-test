class BankingException(Exception):
    """銀行システム基底例外"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AccountNotFound(BankingException):
    """口座が存在しない場合"""
    pass

class CustomerNotFound(BankingException):
    """顧客が存在しない場合"""
    pass

class InsufficientFunds(BankingException):
    """残高不足の場合"""
    pass

class TransactionFailed(BankingException):
    """取引失敗の場合"""
    pass
