from abc import ABC, abstractmethod
from datetime import date, datetime


class Bank:
    ACCOUNTS = ['Debit', 'Credit', 'Invest', 'DailyInvest']

    def __init__(self, overall_balance=10 ** 9, withdraw_limit=10 ** 5, credit_limit=50000, commission=0.05,
                 credit_percent=0.25, invest_percent=0.20, daily_invest_percent=0.10):

        self.overall_balance = overall_balance  # общий баланс
        self.rub_balance = int(overall_balance / 3)
        self.usd_balance = int(overall_balance / 3 / self.usd)
        self.euro_balance = int(overall_balance / 3 / self.eur)
        self.bank_accounts = {'Debit': Debit, 'Invest': Invest, 'Credit': Credit}
        self.bank_currencies = {'rub': self.rub_balance, 'usd': self.usd_balance, 'eur': self.euro_balance}
        self.clients = set()
        self.withdraw_limit = withdraw_limit
        self.credit_limit = credit_limit
        self.commission = commission
        self.credit_percent = credit_percent
        self.invest_percent = invest_percent
        self.daily_invest_percent = daily_invest_percent

    @property
    def rub(self):
        return 1

    @property
    def usd(self):
        return 81

    @property
    def eur(self):
        return 92

    def __iadd__(self, client):
        if not isinstance(client, Client):
            raise Exception("Можем добавить только клиента")
        self.clients.add(client)
        print(f"Клиент {client} добавлен")
        return self

    def __isub__(self, client):
        if not isinstance(client, Client):
            raise Exception("Можем удалить только клиента")
        self.clients.discard(client)
        print(f"Клиент {client} удален")
        return self

    def change_balance(self, summa, currency='rub', add=True):
        quotes = {'rub': self.rub, 'usd': self.usd, 'eur': self.eur}
        if currency not in quotes:
            raise Exception("Неизвестная валюта")
        conv_summa = summa * quotes[currency]
        if add:
            self.overall_balance += conv_summa
            self.bank_currencies[currency] += summa
        else:
            if conv_summa > self.withdraw_limit:
                raise Exception("Превышен лимит на снятие в данном банке")
            self.overall_balance -= conv_summa
            self.bank_currencies[currency] -= summa

    def get_info(self):
        for client in self.clients:
            print(client.get_all_info())


class Client:
    def __init__(self, name, bank, accounts):
        self.name = name
        self.solvency = True  # платежеспособность, если да - кредит дадут, если нет - откажут
        self.bank = bank
        self.filenames = []
        self.accounts = self.add_accounts(accounts)
        for name, obj in self.accounts.items():
            self.create_filename(name)
            self.accounts[name].create_history(f'Открыт {name} счет в валюте {obj.currency}')

    def add_accounts(self, accounts):
        accounts_obj = {}
        for el in accounts:
            if el[0] not in Bank.ACCOUNTS:
                raise Exception(f"Счета {el[0]} не существует")
            accounts_dict = {'Debit': Debit, 'Credit': Credit, 'Invest': Invest, 'DailyInvest': DailyInvest}
            accounts_obj[el[0]] = accounts_dict[el[0]](self.bank, el[1])
        return accounts_obj

    def create_filename(self, other):
        f_name = f"{self.name.split()[0]}_{self.name.split()[1]}_{self.accounts[other].get_name()}.txt'"
        self.accounts[other].filename = f_name
        self.filenames.append(self.accounts[other].filename)
        return f_name

    def __iadd__(self, other):
        if other not in self.bank.EXCHANGE_RATES:
            raise Exception(f"Неизвестный счет")
        self.accounts[other] = self.bank.EXCHANGE_RATES[other]
        self.create_filename(other)
        return self

    def __str__(self):
        return self.name

    def activate_account(self, name_account):
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name_account}")
        self.accounts[name_account].is_activated = True

    # def close_account(self, name_account):
    #     if name_account in self.accounts:
    #         del self.accounts[name_account]

    def close_invest(self, account):
        '''Метод закрывает счет Invest'''
        accounts = {'Invest': 'Debit', 'InvestUSD': 'DebitUSD', 'InvestEUR': 'DebitEUR'}
        if account not in accounts:
            raise Exception(f"Неверный счет")
        if not self.accounts[account].is_activated:
            raise Exception("Счет неактивен")

        current_date = date.today()
        end_date = self.accounts[account].date_end
        if current_date >= end_date:
            summa = int(self.accounts[account].balance + self.accounts[account].profit)
        else:
            summa = self.accounts[account].balance
            self.accounts[account].monthly_rate = self.bank.invest_percent * 0.5 / 12  # уменьшаем ставку в два раза
            new_period = (end_date.year - current_date.year) * 12 + (end_date.month - current_date.month)
            if current_date.day > end_date.day:
                new_period -= 1
            self.accounts[account].period = new_period
        total = summa * (1 + self.accounts[account].monthly_rate) ** self.accounts[account].period
        profit = total - summa
        summa += int(profit)
        self.accounts[accounts[account]].top_up_balance(summa, transact=True)
        self.accounts[account].is_activated = False
        self.accounts[account].balance = 0
        print(f"Вывод денежных средств с инвестиционного счета в размере {summa} руб. Счет закрыт.")

    def close_daily_invest(self, account):
        accounts = {'Invest': 'Debit', 'InvestUSD': 'DebitUSD', 'InvestEUR': 'DebitEUR'}
        self.accounts[account].accrue_daily_interest()
        summa = self.accounts[account].balance
        if self.accounts[account].balance > 0:
            self.accounts[accounts[account]].top_up_balance(summa, transact=True)
        self.accounts[account].is_activated = False
        self.accounts[account].balance = 0
        self.accounts[account].is_activated = False
        currency = self.accounts[account].currency
        print(f"Вывод денежных средств с инвестиционного счета в размере {summa} {currency}. Счет закрыт.")

    def get_credit(self, summa, period, account):
        if not self.solvency:
            raise Exception("В кредите отказано")
        if summa > self.bank.credit_limit:
            raise Exception(f"Слишком большая сумма кредита. Банк может выдать вам {self.bank.credit_limit} руб.")
        for_trans = self.join_accounts[account]  # дебетовый счет для перевода в той же валюте

        self.accounts[account].period = period
        monthly_rate = self.bank.credit_percent / 12
        numerator = summa * monthly_rate * (1 + monthly_rate) ** period
        denominator = (1 + monthly_rate) ** period - 1
        self.accounts[account].payment = int(numerator / denominator)
        self.transfer_to(summa, for_trans, from_=account, client=self)
        self.accounts[account].balance -= (self.accounts[account].payment * period)
        self.solvency = False
        write_down = (
            f"Выдан кредит на сумму {summa} на срок {period} месяцев. "
            f"Платеж составит {self.accounts[account].payment} {self.accounts[account].currency} "
            f"Процентная ставка {self.bank.credit_percent} %")
        self.solvency = False
        self.accounts[account].create_history(write_down)

    def make_payment(self, summa, account):  # account в виде строки 'Credit', 'CreditUSD', 'CreditEUR'
        for_trans = self.join_accounts[account]  # дебетовый счет для перевода в той же валюте
        if self.accounts[account].balance == 0:
            print("У вас нет задолженности")
            self.accounts[for_trans].top_up_balance(summa)
        elif abs(self.accounts[account].balance) <= summa:
            self.accounts[account].balance += summa
            self.accounts[account].payment = 0
            self.accounts[account].period = 0
            self.accounts[for_trans].balance.top_up_balance(self.accounts[account].balance)
            self.accounts[account].balance = 0
            self.accounts[account].is_activated = False
            self.solvency = True
            write_down = "Кредит погашен"
            self.accounts[account].create_history(write_down)
        elif abs(self.accounts[account].balance) > summa:
            if summa == self.accounts[account].payment:
                self.accounts[account].balance += summa
                self.accounts[account].period -= 1
            elif summa > self.accounts[account].payment:
                self.accounts[account].balance += summa
                self.accounts[account].payment = self.accounts[account].balance / self.accounts[account].period
                self.accounts[account].period -= 1
            else:
                fine = self.accounts[account].payment * 0.10  # штраф 10% от платежа
                self.accounts[account].balance -= fine
                self.accounts[account].payment = self.accounts[account].balance / self.accounts[account].period
            write_down = f"Внесен платеж в размере {summa} руб.Остаток долга {self.accounts[account].balance} руб."
            self.accounts[account].create_history(write_down)

    def transfer_to(self, summa, where, from_='Debit', client=None, period=None):
        if client.accounts[where].is_blocked or client.accounts[from_].is_blocked:
            raise Exception("Счет заблокирован")
        if client:  # перевод другому клиенту
            if where not in ('Debit', 'DebitUSD', 'DebitEUR'):
                raise Exception("Перевод другому клиенту можно совершать только на дебетовый счет.")
            if client.accounts[where].currency != client.accounts[from_].currency:
                raise Exception("Переводы можно совершать только в одной валюте")
            commission = self.calc_commission(summa)
            sum_com = summa + commission
            if sum_com > self.accounts['Debit'].balance:
                raise Exception("Недостаточно средств на счете")

            if not client.accounts[where].is_activated:
                raise Exception(f"Счет {where} клиента {client} неактивен")
            client.accounts[where].top_up_balance(summa, transact=True)
            self.accounts[from_].balance -= sum_com

            res = (f"Выполнен перевод  клиенту {client.name}. Сумма перевода {summa} руб. Комиссия {commission} руб. "
                   f"Баланс {from_} счета {self.accounts['Debit'].balance} руб.")

        else:  # перевод себе
            if where not in self.accounts or from_ not in self.accounts:
                raise Exception(f"Счета не существует")
            if summa > self.accounts[from_].balance:
                raise Exception("Недостаточно средств на счете")

            self.accounts[from_].balance -= summa
            to_rub = summa * EXCHANGE_RATES[from_]
            to_exchange = to_rub * EXCHANGE_RATES[where]
            self.accounts[where].activate()
            if where in ('DailyInvest', 'DailyInvestUSD', 'DailyInvestEUR'):
                self.accounts[where].balance -= to_exchange
                self.accounts[where].lets_invest(summa, period)
            res = (f"Выполнен перевод себе с {from_} счета на {where} счет. "
                   f"Сумма перевода {summa} руб. Баланс {from_} счета {self.accounts['Debit'].balance} руб.")
        self.accounts[from_].create_history(res)
        # TODO не записывается в историю

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def get_all_info(self):
        return f"Данные клиента: {self.name}\nИнформация по счетам:\n{[el.get_info() for el in self.accounts.values()]}"


class Base(ABC):
    def __init__(self, bank, currency):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.bank = bank
        self.filename = None
        self.currency = currency
        self.first_log = False

    def withdraw(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if self.get_name() in ('Credit', 'CreditUSD', 'CreditEUR'):
            summa += self.calc_commission(summa)
        if summa > self.balance:
            raise ValueError(f"Недостаточно средств на счете")
        if summa == self.balance:  # ПРИ ПОПЫТКЕ СНЯТЬ ВСЕ ДЕНЬГИ СЧЕТ БЛОКИРУЕТСЯ
            self.block_account()
        self.balance -= summa
        self.bank.change_balance(summa, self.currency, add=False)
        self.create_history(
            f"Снятие наличных с {self.get_name()} счета в размере {summa} usd. Доступно {self.balance} {self.currency}.")

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def activate(self):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.is_activated = True

    def top_up_balance(self, summa, transact=False):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self.balance += summa
        self.create_history(f"Пополнение {self.get_name()} счета в размере {summa} rub. Доступно {self.balance} rub.")
        if not transact:  # если это не перевод
            self.bank.change_balance(summa, self.currency, add=True)

    # TODO при пополнении с банкомата общий счет банка меняется, а счет в валюте нет
    # TODO неправильно вычитаются суммы с банковских счетов при снятии

    def purchase(self, summa, name):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if summa > self.balance:
            raise Exception(f"Недостаточно средств на счете на покупку {name}")
        self.balance -= summa
        self.create_history(f"Покупка {name} в размере {summa} {self.currency} Доступно {self.balance} {self.currency}")
        self.bank.change_balance(summa, add=False)
        # TODO прописать метод __iadd__/__isub__(self.balance -= summa/ self.bank.change_balance(summa, add=False)
        # TODO в классах счетов

    @abstractmethod
    def get_name(self):
        pass

    def show_balance(self):
        print(self.balance)

    def get_info(self):
        return (
            f"Наименование счета: {self.get_name()}. Статус: {'активен' if self.is_activated else 'неактивен'}. "
            f"Текущий баланс: {self.balance} {self.currency}")

    def create_history(self, info):
        try:
            if not self.first_log:
                with open(f"history/{self.filename}", 'w', encoding='UTF-8') as file:
                    file.write(f"{info.rstrip()}\n")
                self.first_log = True
            else:
                with open(f"history/{self.filename}", 'a', encoding='UTF-8') as file:
                    file.write(f"{info.rstrip()}\n")
        except Exception as e:
            print(f"При добавлении записи в историю операций произошла ошибка: '{e}'")
            # TODO оформить в виде классового декоратора

    def block_account(self):
        self.is_blocked = True
        self.is_activated = False
        print(f"Ваш счет заблокирован. Обратитесь в банк или по телефону +7(495)567-67-76 для разблокировки.")


class Debit(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)

    def withdraw(self, summa):
        super().withdraw(summa)

    def top_up_balance(self, summa, transact=False):
        super().top_up_balance(summa, transact)

    def get_name(self):
        return 'Debit'


# class DebitUSD(Debit):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'usd'
#
#     def withdraw(self, summa):
#         super().withdraw(summa)
#
#     def top_up_balance(self, summa, transact=False):
#         super().top_up_balance(summa, transact)
#
#     def get_name(self):
#         return 'DebitUSD'
#
#
# class DebitEUR(Debit):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'eur'
#
#     def withdraw(self, summa):
#         super().withdraw(summa)
#
#     def top_up_balance(self, summa, transact=False):
#         super().top_up_balance(summa, transact)
#
#     def get_name(self):
#         return 'DebitEUR'


class Credit(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.balance = -1 * self.balance
        self.payment = 0
        self.period = 0

    def withdraw(self, summa):
        raise Exception("Снятие наличных с кредитного счета недоступно")

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    def credit_info(self):
        print(
            f"Сумма задолженности {self.balance} {self.currency} Общий срок кредита {self.period} месяцев. "
            f"Ежемесячный платеж {self.payment} {self.currency} Процентная ставка {self.bank.credit_percent}%")

    def get_name(self):
        return 'Credit'


# class CreditUSD(Credit):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'usd'
#
#
# class CreditEUR(Credit):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'usd'


class BaseInvest(Base):
    def __init__(self, bank, currency):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.history = []
        self.bank = bank
        self.percents = 0
        self.period = 0
        self.profit = 0
        self.filename = None
        self.currency = currency
        self.date_start = None
        self.date_end = None

    def activate(self):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.is_activated = True

    def block_account(self):
        self.is_blocked = True
        self.is_activated = False
        print(f"Ваш счет заблокирован. Обратитесь в банк или по телефону +7(495)567-67-76 для разблокировки.")

    def lets_invest(self, summa, period):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        monthly_rate = self.bank.invest_percent / 12
        total = summa * (1 + monthly_rate) ** period
        self.profit = total - summa

        self.percents = (summa * self.bank.invest_percent * period) / 365
        self.period = period
        self.date_start = date.today()
        self.date_end = self.calculate_date(period)
        result = (
            f"Вы инвестировали {summa} {self.currency}. на срок {self.period} месяцев под {int(self.bank.invest_percent * 100)} %. "
            f"Прибыль за весь период составит {int(self.balance + self.profit)} {self.currency}.")
        self.create_history(result)
        self.balance += summa
        print(result)

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

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    def top_up_balance(self, summa, transact=False):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self.balance += summa
        self.create_history(f"Пополнение {self.get_name()} счета в размере {summa} rub. Доступно {self.balance} rub.")
        if not transact:  # если это не перевод
            self.bank.change_balance(summa, self.currency, add=True)

    @abstractmethod
    def get_name(self):
        pass

    def create_history(self, info):
        try:
            with open(f"history/{self.filename}", 'a', encoding='UTF-8') as file:
                file.write(f"{info.rstrip()}\n")
        except Exception as e:
            print(e)

    def show_balance(self):
        print(self.balance)

    def get_info(self):
        return (
            f"Наименование счета: {self.get_name()}. Статус: {'активен' if self.is_activated else 'неактивен'}. "
            f"Текущий баланс: {self.balance} руб. ")


class Invest(BaseInvest):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)

    def withdraw(self, summa):
        raise Exception("Снятие наличных с инвестиционного счета недоступно")

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    def get_name(self):
        return 'Invest'


# class InvestUSD(Invest):
#     def __init__(self, bank):
#         super().__init__(bank)
#
#
# class InvestEUR(Invest):
#     def __init__(self, bank):
#         super().__init__(bank)


class DailyInvest(BaseInvest):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.last_interest_date = date.today()  # Дата последнего начисления процентов

    def accrue_daily_interest(self):
        today = date.today()
        days_passed = (today - self.last_interest_date).days
        if days_passed < 1:
            return  # Проценты уже начислялись сегодня

        for _ in range(days_passed):
            interest = self.balance * self.bank.daily_invest_percent
            self.balance += interest
        self.last_interest_date = today

    def lets_invest(self, summa, period):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        days_rate = self.bank.daily_invest_percent / 365
        result = (
            f"Вы инвестировали {summa} {self.currency} под {int(self.bank.daily_invest_percent * 100)}%. ")
        self.create_history(result)
        self.balance += summa
        print(result)

    def withdraw(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa < self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        bank.bank_currencies[self.currency] -= summa
        result = f"Снятие наличных в размере {summa} {self.currency}"
        self.create_history(result)

    def purchase(self, summa, name):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa < self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        bank.bank_currencies[self.currency] -= summa
        result = f"Покупка {name} в размере {summa} {self.currency}"
        self.create_history(result)

    def get_name(self):
        return 'DailyInvest'


# class DailyInvestUSD(DailyInvest):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'usd'
#
#     def get_name(self):
#         return 'DailyInvestUSD'
#
#
# class DailyInvestEUR(DailyInvest):
#     def __init__(self, bank):
#         super().__init__(bank)
#         self.currency = 'eur'
#
#     def get_name(self):
#         return 'DailyInvestEUR'


bank = Bank()

client1 = Client("Иванов Иван", bank, [('Debit', 'rub'), ('Invest', 'eur'), ('Credit', 'usd')])

