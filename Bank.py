from abc import ABC, abstractmethod
from datetime import date, datetime
from db import Database

db = Database('bank.db')

class Bank:
    def __init__(self, overall_balance=10 ** 9, withdraw_limit=10 ** 5, credit_limit=50000, commission=0.05,
                 credit_percent=0.25, invest_percent=0.20, daily_invest_percent=0.10):
        self.overall_balance = overall_balance
        self.bank_accounts = {'Debit': Debit, 'Credit': Credit, 'Invest': Invest, 'DailyInvest': DailyInvest}
        self.bank_currencies = {'rub': int(overall_balance / 3), 'usd': int(overall_balance / 3 / 81),
                                'eur': int(overall_balance / 3 / 92)}
        self.exchanges = {'rub': 1, 'usd': 81, 'eur': 92}
        self.clients = set()
        self.withdraw_limit = withdraw_limit
        self.credit_limit = credit_limit
        self.commission = commission
        self.credit_percent = credit_percent
        self.invest_percent = invest_percent
        self.daily_invest_percent = daily_invest_percent

    @property
    def rub_balance(self):
        return self.bank_currencies['rub']

    @property
    def usd_balance(self):
        return self.bank_currencies['usd']

    @property
    def eur_balance(self):
        return self.bank_currencies['eur']

    def __iadd__(self, client):
        if not isinstance(client, Client):
            raise Exception("Можем добавить только клиента")
        self.clients.add(client)
        return self

    def __isub__(self, client):
        if not isinstance(client, Client):
            raise Exception("Можем удалить только клиента")
        self.clients.discard(client)
        print(f"Клиент {client} удален")
        return self

    def change_balance(self, summa, currency, add=True):
        if currency not in self.exchanges:
            raise Exception("Неизвестная валюта")
        conv_summa = summa * self.exchanges[currency]
        if add:
            self.overall_balance += conv_summa
            self.bank_currencies[currency] += summa
        else:
            if conv_summa > self.withdraw_limit:
                raise Exception("Превышен лимит на снятие в данном банке")
            self.overall_balance -= conv_summa
            self.bank_currencies[currency] -= summa

    def get_info(self):
        print("Информация по всем клиентам банка:")
        for client in self.clients:
            print(client.get_all_info())

    @staticmethod
    def show_table(filtr, value):
        db.show_table(filtr, value)

    # @staticmethod
    # def delete_from_db(parametr=None, value=None):
    #     if parametr is None or value is None:
    #         db.delete_table()
    #     else:
    #         db.delete_rows(parametr, value)


class Client:
    def __init__(self, name, bank, accounts):
        self.name = name
        self.solvency = True  # платежеспособность, если да - кредит дадут, если нет - откажут
        self.bank = bank
        self.accounts = self.add_accounts(accounts)

    def add_accounts(self, accounts):
        accounts_obj = {}
        for el in accounts:
            if el[0] not in self.bank.bank_accounts:
                raise Exception(f"Счета {el[0]} не существует")

            name_account = el[0] + '_' + el[1]
            current_acc_obj = self.bank.bank_accounts[el[0]](self.bank, el[1])
            accounts_obj[name_account] = current_acc_obj
            current_acc_obj.client = self

        return accounts_obj

    def __iadd__(self, account_obj):
        name = account_obj.get_name()
        currency = account_obj.currency

        if name not in self.bank.bank_accounts:
            raise Exception(f"Неизвестный счет")
        if currency not in self.bank.exchanges:
            raise Exception("Неверно указана валюта")

        self.accounts[name + '_' + currency] = account_obj
        self.accounts[name + '_' + currency].client = self
        return self

    def __str__(self):
        return self.name

    def activate_account(self, name, currency):
        name_account = name + '_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name} в валюте {currency}")
        self.accounts[name_account].is_activated = True

    def transfer_to(self, summa, from_, currency, where, currency2, client=None):
        from_account = from_
        where_account = where

        if client:  # перевод другому клиенту
            if currency != currency2:
                raise Exception("Перевод другому клиенту можно совершать только в одинаковой валюте")
            if where != 'Debit_' + currency:
                raise Exception("Перевод другому клиенту можно совершать только на дебетовый счет.")
            if from_account not in self.accounts:
                raise Exception(f"Счета {from_} у клиента {self.name} не существует")
            if where_account not in client.accounts:
                raise Exception(f"Счета {where} у клиента {client.name} не существует")
            if self.accounts[where_account].is_blocked or client.accounts[from_account].is_blocked:
                raise Exception("Счет заблокирован")

            commission = self.calc_commission(summa)
            sum_com = summa + commission
            if sum_com > self.accounts[from_account].balance:
                raise Exception("Недостаточно средств на счете")

            if not client.accounts[where_account].is_activated or not self.accounts[from_account].is_activated:
                raise Exception(f"Счет неактивен")
            client.accounts[where_account].top_up_balance(summa, transact=True)
            self.accounts[from_account].balance -= sum_com

            write_down = (f"Выполнен перевод  клиенту {client.name}. Сумма перевода {summa} руб. "
                          f"Комиссия {commission} {currency}")
            db.add_entry(client_name=self.name, log=write_down, account=self.accounts[from_account].get_name(),
                     balance=self.accounts[from_account].balance, currency=currency, status=self.accounts[from_account].status)

        else:  # перевод себе
            if where_account not in self.accounts or from_account not in self.accounts:
                raise Exception(f"Счета не существует")
            if self.accounts[where_account].is_blocked or self.accounts[from_account].is_blocked:
                raise Exception("Счет заблокирован")
            if summa > self.accounts[from_account].balance:
                raise Exception("Недостаточно средств на счете")
            if not self.accounts[where_account].is_activated or not self.accounts[from_account].is_activated:
                raise Exception(f"Счет неактивен")
            
            if currency == 'rub':
                summa_where = round(summa / self.bank.exchanges[currency2], 2)
            else:
                summa_where = round(summa * self.bank.exchanges[currency] / self.bank.exchanges[currency2], 2)

            self.accounts[from_account].balance -= summa
            self.accounts[where_account].balance += summa_where
            write_down_from = (f"Выполнен перевод себе на {where} счет. Сумма перевода {summa} {currency}")
            write_down_where = (f"Выполнен перевод себе с {from_} счета. Сумма перевода {summa_where} {currency2}")

            db.add_entry(client_name=self.name, log=write_down_from, account=self.accounts[from_account].get_name(),
                     balance=self.accounts[from_account].balance, currency=currency, status=self.accounts[from_account].status)
        
            db.add_entry(client_name=self.name, log=write_down_where, account=self.accounts[where_account].get_name(),
                     balance=self.accounts[from_account].balance, currency=currency2, status=self.accounts[where_account].status)
        
    def calc_commission(self, summa):
        return summa * self.bank.commission

    def get_credit(self, summa, period, currency):
        if not self.solvency:
            raise Exception("В кредите отказано")
        if currency not in self.bank.exchanges:
            raise Exception(f"Банк не работает с {currency} валютой")
        if summa * self.bank.exchanges[currency] > self.bank.credit_limit:
            raise Exception(f"Слишком большая сумма кредита. Банк может выдать вам "
                            f"{self.bank.credit_limit // self.bank.exchanges[currency]} {currency}.")

        name_account = 'Credit' + '_' + currency
        for_trans = 'Debit' + '_' + currency
        if for_trans not in self.accounts:
            self.accounts[for_trans] = Debit(self.bank, currency)

        monthly_rate = self.bank.credit_percent / 12
        numerator = summa * monthly_rate * (1 + monthly_rate) ** period
        denominator = (1 + monthly_rate) ** period - 1

        self.accounts[for_trans].balance += summa
        self.accounts[name_account].payment = int(numerator / denominator)
        self.accounts[name_account].period = period
        self.solvency = False
        self.accounts[name_account].balance -= self.accounts[name_account].payment * period
        self.accounts[name_account].status = 'Активен'
        self.accounts[name_account].activate()

        write_down = (
            f"Выдан кредит на сумму {summa} на срок {period} месяцев. "
            f"Платеж составит {self.accounts[name_account].payment} {currency} "
            f"Процентная ставка {self.bank.credit_percent} %")

        db.add_entry(client_name=self.name, log=write_down, account='Credit',
                     balance=self.accounts[name_account].balance, currency=currency, status=self.accounts[name_account].status)

    def make_payment(self, summa, currency):
        credit_account = 'Credit' + '_' + currency
        debit_account = 'Debit' + '_' + currency
        write_down = None

        if self.accounts[credit_account].balance == 0:
            print("У вас нет задолженности")
            self.accounts[debit_account].top_up_balance(summa)

        elif abs(self.accounts[credit_account].balance) <= summa:
            self.accounts[credit_account].balance += summa
            self.accounts[credit_account].payment = 0
            self.accounts[credit_account].period = 0
            self.accounts[debit_account].balance.top_up_balance(self.accounts[credit_account].balance)
            self.accounts[credit_account].is_activated = False
            self.solvency = True
            write_down = "Кредит погашен"

        else:
            if summa == self.accounts[credit_account].payment:
                self.accounts[credit_account].balance += summa
                self.accounts[credit_account].period -= 1
            elif summa > self.accounts[credit_account].payment:
                self.accounts[credit_account].balance += summa
                self.accounts[credit_account].period -= 1
                self.accounts[credit_account].payment = self.accounts[credit_account].balance / self.accounts[
                    credit_account].period
            else:
                fine = self.accounts[credit_account].payment * 0.10  # штраф 10% от платежа
                self.accounts[credit_account].balance -= fine
                self.accounts[credit_account].payment = self.accounts[credit_account].balance / self.accounts[
                    credit_account].period
            write_down = (f"Внесен платеж в размере {summa} {currency}"
                          f"Остаток долга {self.accounts[credit_account].balance} {currency}")

        db.add_entry(client_name=self.name, log=write_down, account='Credit', balance=self.accounts[credit_account].balance, currency=currency, status=self.accounts[credit_account].status)

    def close_debit(self, name, currency):
        if name != 'Debit':
            raise Exception("Неверный счет")
        name_account = name + '_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name} в валюте {currency}")
        if self.accounts[name_account].balance > 0:
            summa = self.accounts[name_account].balance
            self.accounts[name_account].withdraw(summa)
        self.accounts[name_account].is_activated = False
        write_down = "Счет закрыт"

        db.add_entry(client_name=self.name, log=write_down, account=name, balance=self.balance, currency=currency, status=self.accounts[name_account])

    def close_credit(self, name, currency):
        write_down = None

        if name != 'Credit':
            raise Exception("Неверный счет")
        name_account = name + '_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name} в валюте {currency}")
        if self.accounts[name_account].balance < 0:
            raise Exception(
                f"Для закрытия кредитного счета погасите задолженность в размере {name_account.balance} {currency}")
        if self.accounts[name_account].balance == 0:
            self.accounts[name_account].is_activated = False
            write_down = f"Счет закрыт"
        db.add_entry(client_name=self.name, log=write_down, account='Credit',
                     balance=self.balance, currency=currency, status=self.accounts[name_account])

    def close_invest(self, currency):
        name_account = 'Invest_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {Invest} в валюте {currency}")
        if not self.accounts[name_account].is_activated:
            raise Exception("Счет неактивен")

        current_date = date.today()
        end_date = self.accounts[name_account].date_end
        if current_date >= end_date:
            summa = int(self.accounts[name_account].balance + self.accounts[name_account].profit)
        else:
            summa = self.accounts[name_account].balance
            self.accounts[
                name_account].monthly_rate = self.bank.invest_percent * 0.5 / 12  # уменьшаем ставку в два раза
            new_period = (end_date.year - current_date.year) * 12 + (end_date.month - current_date.month)
            if current_date.day > end_date.day:
                new_period -= 1
            self.accounts[name_account].period = new_period
        total = summa * (1 + self.accounts[name_account].monthly_rate) ** self.accounts[name_account].period
        profit = total - summa
        summa += int(profit)
        self.accounts[name_account].top_up_balance(summa, transact=True)
        self.accounts[name_account].is_activated = False
        self.accounts[name_account].balance = 0
        write_down = f"Вывод денежных средств в размере {summa} {currency}. Счет закрыт."

        db.add_entry(client_name=self.name, log=write_down, account='Invest',
                     balance=self.accounts[name_account].balance, currency=currency, status=self.accounts[name_account].status)

    def close_daily_invest(self, currency):
        name_account = 'DailyInvest_' + currency
        self.accounts[name_account].accrue_daily_interest()
        summa = self.accounts[name_account].balance

        if self.accounts[name_account].balance > 0:
            for_trans = 'Debit_' + currency
            self.accounts[for_trans].top_up_balance(summa, transact=True)

        self.accounts[name_account].is_activated = False
        self.accounts[name_account].balance = 0
        self.accounts[name_account].is_activated = False
        write_down = f"Вывод денежных средств в размере {summa} {currency}. Счет закрыт."
        db.add_entry(client_name=self.name, log=write_down, account='Invest',
                     balance=self.balance, currency=currency, status=self.accounts[name_account])


class Base(ABC):
    def __init__(self, bank, currency):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.bank = bank
        self.currency = currency
        self.client = None
        self.status = 'Неактивен'

    def check_block(self):
        if self.is_blocked:
            raise Exception("Счет заблокирован")

    def activate(self):
        self.check_block()
        self.is_activated = True
        self.status = 'Активен'

    def withdraw(self, summa):
        if not isinstance(summa, (int, float)) or summa <= 0:
            raise ValueError("Сумма должна быть положительным числом")
        self.check_block()
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if self.get_name() == 'Credit':
            summa += self.calc_commission(summa)
        if summa > self.balance:
            raise ValueError(f"Недостаточно средств на счете")
        if summa == self.balance:  # ПРИ ПОПЫТКЕ СНЯТЬ ВСЕ ДЕНЬГИ СЧЕТ БЛОКИРУЕТСЯ
            self.block_account()
        self.balance -= summa
        self.bank.change_balance(summa, self.currency, add=False)
        write_down = (f"Снятие наличных в размере {summa} {self.currency}")

        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def top_up_balance(self, summa, transact=False):
        self.check_block()
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self.balance += summa
        write_down = f"Пополнение в размере {summa} {self.currency}"
        if not transact:  # если это не перевод
            self.bank.change_balance(summa, self.currency, add=True)
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def purchase(self, summa, name):
        self.check_block()
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if summa > self.balance:
            raise Exception(f"Недостаточно средств на счете на покупку {name}")
        self.balance -= summa
        write_down = f"Покупка {name} в размере {summa} {self.currency}"
        self.bank.change_balance(summa, self.currency, add=False)
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    @abstractmethod
    def get_name(self):
        pass

    def get_info(self):
        return (
            f"Наименование счета: {self.get_name()}. Статус: {'активен' if self.is_activated else 'неактивен'}. "
            f"Текущий баланс: {self.balance} {self.currency}")

    def block_account(self):
        self.is_blocked = True
        self.is_activated = False
        self.status = 'Заблокирован'
        write_down = "Cчет заблокирован"
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)


class Debit(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)

    def withdraw(self, summa):
        super().withdraw(summa)

    def top_up_balance(self, summa, transact=False):
        super().top_up_balance(summa, transact)

    def get_name(self):
        return 'Debit'


class Credit(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.payment = 0
        self.period = 0

    def withdraw(self, summa):
        raise Exception("Снятие наличных с кредитного счета недоступно")

    def purchase(self, *args):
        raise Exception("Операция недоступна")

    # def credit_info(self):
    #     print(f"Сумма задолженности {self.balance} {self.currency}")
    #     print(f"Общий срок кредита {self.period} месяцев")
    #     print(f"Ежемесячный платеж {self.payment} {self.currency}")
    #     print(f"Процентная ставка {int(self.bank.credit_percent * 100)} %")

    def get_name(self):
        return 'Credit'


class Invest(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.percents = 0
        self.period = 0
        self.profit = 0
        self.date_start = None
        self.date_end = None

    def lets_invest(self, summa, period):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.activate()
        monthly_rate = self.bank.invest_percent / 12
        total = summa * (1 + monthly_rate) ** period
        self.profit = total - summa

        self.percents = (summa * self.bank.invest_percent * period) / 365
        self.period = period
        self.date_start = date.today()
        self.date_end = self.calculate_date(period)
        write_down = f"""Инвестиции на суммму {summa} {self.currency} на срок {self.period} месяцев под {int(self.bank.invest_percent * 100)} %. Прибыль за весь период составит {int(self.balance + self.profit)} {self.currency}."""
        self.balance += summa
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def calculate_date(self, period):
        try:
            year = self.date_start.year + (self.date_start.month + period - 1) // 12
            month = (self.date_start.month + period - 1) % 12 + 1
            day = min(self.date_start.day,
                      [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            end_date = datetime(year, month, day).date()
            return end_date
        except Exception as e:
            print(f"Ошибка при расчете даты: {e}")

    def withdraw(self, summa):
        raise Exception("Снятие наличных с инвестиционного счета недоступно")

    def purchase(self, *args):
        raise Exception("Операция недоступна")

    def get_name(self):
        return 'Invest'


class DailyInvest(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.last_interest_date = date.today()  # Дата последнего начисления процентов

    def accrue_daily_interest(self):
        today = date.today()
        # today = date(2025, 10, 15)
        days_passed = (today - self.last_interest_date).days
        if days_passed < 1:
            return  # 'Проценты уже начислялись сегодня'

        for _ in range(days_passed):
            profit = (self.balance * self.bank.daily_invest_percent) / 365
            self.balance += profit
            self.balance = round(self.balance, 2)
            write_down = (f"Начисление процентов по инвестиционному счету в размере {profit} {self.currency} "
                          f"за период {days_passed} дн.")
            db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                         balance=self.balance, currency=self.currency, status=self.status)

        self.last_interest_date = today

    def lets_invest(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        # days_rate = self.bank.daily_invest_percent / 365
        write_down = (
            f"Инвестиции в размере {summa} {self.currency} под {int(self.bank.daily_invest_percent * 100)} %.")
        self.balance += summa
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def withdraw(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa > self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        self.bank.bank_currencies[self.currency] -= summa
        write_down = f"Снятие наличных в размере {summa} {self.currency}"
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def purchase(self, summa, name):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa > self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        self.bank.bank_currencies[self.currency] -= summa
        write_down = f"Покупка {name} в размере {summa} {self.currency}"
        db.add_entry(client_name=self.client.name, log=write_down, account=self.get_name(), 
                     balance=self.balance, currency=self.currency, status=self.status)

    def get_name(self):
        return 'DailyInvest'
