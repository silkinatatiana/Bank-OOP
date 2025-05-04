from abc import ABC, abstractmethod
from datetime import date, datetime

EXCHANGE_RATES = {'Debit': 1, 'Credit': 1, 'Invest': 1, 'DailyInvest': 1,
                  'DebitUSD': 81, 'CreditUSD': 81, 'InvestUSD': 81, 'DailyInvestUSD': 81,
                  'DebitEUR': 92, 'CreditEUR': 92, 'InvestEUR': 92, 'DailyInvestEUR': 92}
CURRENCY = {'RUB': 1, 'USD': 81, 'EUR': 92}


class Bank:
    def __init__(self, overall_balance=10 ** 9, withdraw_limit=10 ** 7, credit_limit=50000, commission=0.05,
                 credit_percent=0.25, invest_percent=0.20, daily_invest_percent=0.10):

        self.overall_balance = overall_balance  # общий баланс в долларах
        self.rub_balance = int(overall_balance / 3 * CURRENCY['USD'])
        self.usd_balance = int(overall_balance / 3)
        self.euro_balance = int(overall_balance / 3 * CURRENCY['USD'] / CURRENCY['EUR'])
        self.bank_accounts = {'Debit': Debit, 'Invest': Invest, 'Credit': Credit}
        self.clients = set()
        self.withdraw_limit = withdraw_limit
        self.credit_limit = credit_limit
        self.commission = commission
        self.credit_percent = credit_percent
        self.invest_percent = invest_percent
        self.daily_invest_percent = daily_invest_percent

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

    def change_balance(self, summa, add=True):
        if add:
            self.overall_balance += summa
        else:
            if summa > self.withdraw_limit:
                raise Exception("Превышен лимит на снятие в данном банке")
            self.overall_balance -= summa

    def transfer_money(self, client):
        pass

    def get_info(self):
        for client in self.clients:
            print(client.get_all_info())


class Client:
    def __init__(self, name, bank, accounts=None):
        self.name = name
        self.solvency = True  # платежеспособность, если да - кредит дадут, если нет - откажут
        self.bank = bank
        self.filenames = []
        self.accounts = {}
        self.add_accounts(accounts)  # метод добавляет счета при инициализации

    def add_accounts(self, accounts):
        if not accounts:
            self.accounts['Debit'] = Debit(bank)
            self.create_filename('Debit')
            self.accounts['Debit'].create_history('Открыт Debit счет')
        if accounts:
            for el in accounts:
                if el not in ACCOUNTS:
                    raise Exception(f"Счета {el} не существует")
                self.accounts[el] = ACCOUNTS[el]
                self.create_filename(el)
                self.accounts['Debit'].create_history(f'Открыт {el} счет')
        if 'Debit' not in self.accounts:  # если нет дебетового счета - добавляем
            self.accounts['Debit'] = Debit(bank)
            self.create_filename('Debit')
            self.accounts['Debit'].create_history('Открыт Debit счет')

    def create_filename(self, other):
        f_name = f"{self.name.split()[0]}_{self.name.split()[1]}_{self.accounts[other].get_name()}.txt'"
        self.accounts[other].filename = f_name
        self.filenames.append(self.accounts[other].filename)
        return f_name

    def __iadd__(self, other):
        if other not in ACCOUNTS:
            raise Exception(f"Неизвестный счет")
        self.accounts[other] = ACCOUNTS[other]
        self.create_filename(other)
        return self

    def __str__(self):
        return self.name

    def activate_account(self, name_account):
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name_account}")
        self.accounts[name_account].is_activated = True

    def close_account(self, name_account):
        if name_account in self.accounts:
            del self.accounts[name_account]

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

    def get_credit(self, summa, time, currency='RUB'):
        if not self.solvency:
            raise Exception("В кредите отказано")
        if summa > self.bank.credit_limit:
            raise Exception(f"Слишком большая сумма кредита. Банк может выдать вам {self.bank.credit_limit} руб.")
        self.accounts['Debit'].balance += summa
        self.accounts['Credit'].balance -= summa
        self.accounts['Credit'].time = time

        monthly_rate = self.bank.credit_percent / 12
        numerator = summa * monthly_rate * (1 + monthly_rate) ** time
        denominator = (1 + monthly_rate) ** time - 1
        self.accounts['Credit'].payment = int(numerator / denominator)

        result = (
            f"Выдан кредит на сумму {summa} на срок {time} месяцев. Платеж составит {self.accounts['Credit'].payment} руб. "
            f"Процентная ставка {self.bank.credit_percent} %")
        self.solvency = False
        self.accounts['Credit'].create_history(result)
        self.accounts['Debit'].create_history(f"Перевод {summa} руб. с кредитного счета")
        print(result)

    def make_payment(self, summa):
        if self.accounts['Credit'].balance == 0:
            print("У вас нет задолженности")
            self.accounts['Debit'].top_up_balance(summa, transact=True)
        elif abs(self.accounts['Credit'].balance) <= summa:
            self.accounts['Credit'].balance += summa
            self.accounts['Credit'].payment = 0
            self.accounts['Credit'].period = 0
            self.accounts['Debit'].balance += self.accounts['Credit'].balance
            self.accounts['Credit'].balance = 0
            self.accounts['Credit'].is_activated = False
            self.solvency = True
            print("Кредит погашен")
        elif abs(self.accounts['Credit'].balance) > summa:
            if summa == self.accounts['Credit'].payment:
                self.accounts['Credit'].balance += summa
                self.accounts['Credit'].period -= 1
            elif summa > self.accounts['Credit'].payment:
                self.accounts['Credit'].balance += summa
                self.accounts['Credit'].payment = self.accounts['Credit'].balance / self.accounts['Credit'].time
                self.accounts['Credit'].period -= 1
            else:
                fine = self.accounts['Credit'].payment * 0.10  # штраф 10% от платежа
                self.accounts['Credit'].balance -= fine
                self.accounts['Credit'].payment = self.accounts['Credit'].balance / self.accounts['Credit'].time
            print(f"Внесен платеж в размере {summa} руб.Остаток долга {self.accounts['Credit'].balance} руб.")

    def transfer_to(self, summa, where, from_='Debit', currency='RUB', client=None, period=None):
        if client:  # перевод другому клиенту
            if where != 'Debit':
                raise Exception("Перевод другому клиенту можно совершать только на дебетовый счет.")
            commission = self.calc_commission(summa)
            sum_com = summa + commission
            if sum_com > self.accounts['Debit'].balance:
                raise Exception("Недостаточно средств на счете")

            if not client.accounts[where].is_activated:
                raise Exception(f"Счет {where} клиента {client} неактивен")
            client.accounts[where].top_up_balance(summa, transact=True)
            self.accounts['Debit'].balance -= sum_com

            print(
                f"Выполнен перевод  клиенту {client.name}. "
                f"Сумма перевода {summa} руб. Комиссия {commission} руб. Баланс депозитного счета {self.accounts['Debit'].balance} руб.")

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
            print(f"Выполнен перевод себе с депозитного счета на кредитный счет. "
                  f"Сумма перевода {summa} руб. Баланс депозитного счета {self.accounts['Debit'].balance} руб.")

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def get_all_info(self):
        return f"Данные клиента: {self.name}\nИнформация по счетам:\n{[el.get_info() for el in self.accounts.values()]}"


class Base(ABC):
    def __init__(self, bank):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.bank = bank
        self.filename = None
        self.currency = None

    def withdraw(self, summa):
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
        self.is_activated = True

    def top_up_balance(self, summa, transact=False):
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self.balance += summa
        self.create_history(f"Пополнение {self.get_name()} счета в размере {summa} rub. Доступно {self.balance} rub.")
        if not transact:  # если это не перевод
            self.bank.change_balance(summa, self.currency, add=True)

    def purchase(self, summa, name):
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if summa > self.balance:
            raise Exception(f"Недостаточно средств на счете на покупку {name}")
        self.balance -= summa
        self.create_history(f"Покупка {name} в размере {summa} {self.currency} Доступно {self.balance} {self.currency}")
        self.bank.change_balance(summa, add=False)

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
            with open(f"history/{self.filename}", 'a', encoding='UTF-8') as file:
                file.write(f"{info.rstrip()}\n")
        except Exception as e:
            print(f"При добавлении записи в историю операций произошла ошибка: '{e}'")

    def block_account(self):
        self.is_blocked = True
        print(f"Ваш счет заблокирован. Обратитесь в банк или по телефону +7(495)567-67-76 для разблокировки.")


class Debit(Base):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'rub'

    def withdraw(self, summa):
        super().withdraw(summa)

    def top_up_balance(self, summa, transact):
        super().top_up_balance(summa, transact)

    def get_name(self):
        return 'Debit'


class DebitUSD(Debit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'usd'

    def withdraw(self, summa):
        super().withdraw(summa)

    def top_up_balance(self, summa, transact):
        super().top_up_balance(summa, transact)

    def get_name(self):
        return 'DebitUSD'


class DebitEUR(Debit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'eur'

    def withdraw(self, summa):
        super().withdraw(summa)

    def top_up_balance(self, summa, transact):
        super().top_up_balance(summa, transact)

    def get_name(self):
        return 'DebitEUR'


class Credit(Base):
    def __init__(self, bank):
        super().__init__(bank)
        self.balance = -1 * self.balance
        self.payment = 0
        self.time = 0
        self.currency = 'rub'

    def withdraw(self, summa):
        raise Exception("Снятие наличных с кредитного счета недоступно")

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    def credit_info(self):
        print(
            f"Сумма задолженности {self.balance} {self.currency} Общий срок кредита {self.time} месяцев. "
            f"Ежемесячный платеж {self.payment} {self.currency} Процентная ставка {self.bank.credit_percent}%")

    def get_name(self):
        return 'Credit'


class CreditUSD(Credit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'usd'


class CreditEUR(Credit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'usd'


class BaseInvest(ABC):
    def __init__(self, bank):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.history = []
        self.bank = bank
        self.percents = 0
        self.period = 0
        self.profit = 0
        self.filename = None
        self.currency = None
        self.date_start = None
        self.date_end = None


    def activate(self):
        self.is_activated = True

    def block_account(self):
        self.is_blocked = True
        print(f"Ваш счет заблокирован. Обратитесь в банк или по телефону +7(495)567-67-76 для разблокировки.")

    def lets_invest(self, summa, period):
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
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'rub'

    def withdraw(self, summa):
        raise Exception("Снятие наличных с инвестиционного счета недоступно")

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    def get_name(self):
        return 'Invest'


class InvestUSD(Invest):
    def __init__(self, bank):
        super().__init__(bank)


class InvestEUR(Invest):
    def __init__(self, bank):
        super().__init__(bank)

class DailyInvest(BaseInvest):
    def __init__(self, bank):
        super().__init__(bank)

    def get_name(self):
        return 'DailyInvest'

    # TODO подумать про наследование от инвест, выделить общую логику и добавить в один из классов
    # TODO возможно, создать абстрактный класс именно для инвестиционных счетов.
    # TODO при открытии счета указывать текущую дату с помощью дэйттайм и указывать срок инвестиций(дельта).
    # TODO метод принимает (1, 11, 26) один год 11 мес 26 дн.

    def lets_invest(self, summa, period):
        monthly_rate = self.bank.daily_invest_percent / 12
        total = summa * (1 + monthly_rate) ** period
        self.profit = total - summa

        self.percents = (summa * self.bank.daily_invest_percent * period) / 365
        self.period = period
        result = (
            f"Вы инвестировали {summa} руб. на срок {self.period} месяцев под {int(self.bank.daily_invest_percent * 100)}%. "
            f"Прибыль за весь период составит {int(self.balance + self.profit)} руб.")
        self.create_history(result)
        self.balance += summa
        print(result)


class DailyInvestUSD(DailyInvest):
    def __init__(self, bank):
        super().__init__(bank)


class DailyInvestEUR(DailyInvest):
    def __init__(self, bank):
        super().__init__(bank)


# TODO написать класс, который наследуется от инвест и проценты приходят на ежедневный остаток, можно пополнять и снимать без ограничений
# TODO создать класс-конвертер для валюты. Разширить наш класс банк и при создания клиента указывать, какие счета в каких валютах мы хотим создать
# client1 = Client(name, ('Debit', 'rub'), ('Debit', 'euro')) # комиссия в той валюте, с какого счета мы переводим
# bank += сlient1
# курсы валют должны быть константами (вне класса капсом)
# создать классовые свойства в банке под балансы разных валют и общий баланс банка в долларах
# Изначально общий баланс - сумма балансов с конвертацией в доллары, при изменении любого из балансов - общий баланс перерасчитывается отдельным методом.


bank = Bank()
ACCOUNTS = {'Debit': Debit(bank), 'Credit': Credit(bank), 'Invest': Invest(bank), 'DailyInvest': DailyInvest(Bank),
            'DebitUSD': DebitUSD(bank),
            'CreditUSD': CreditUSD(bank), 'InvestUSD': InvestUSD(bank), 'DailyInvestUSD': DailyInvestUSD(Bank),
            'DebitEUR': DebitEUR(bank), 'CreditEUR': CreditEUR(bank),
            'InvestEUR': InvestEUR(bank), 'DailyInvestEUR': DailyInvestEUR(Bank)}

client1 = Client("Иванов Иван", bank)
client2 = Client("Захарова Дарья", bank)
client3 = Client("Власов Юрий", bank, ('Debit', 'Invest', 'Credit'))
client4 = Client("Алексеева Анна", bank)
client3 += 'DailyInvestEUR'

bank += client1
bank += client2
bank += client3
bank += client4

# ПОПОЛНЕНИЕ БАЛАНСА И ПЕРЕВОД ДРУГОМУ КЛИЕНТУ
# client1.accounts['Debit'].top_up_balance(5000)
# print(client1.accounts['Debit'].balance)
# print(client1.accounts['Debit'].history)

# client2.accounts['Debit'].activate()
# client1.transfer_to(500, 'Debit', client2)
# print(client2.accounts['Debit'].balance)
# print(client2.accounts['Debit'].history)

# ВЗЯТЬ КРЕДИТ И ИНВЕСТИРОВАТЬ ДЕНЬГИ
client3.accounts['Debit'].activate()
client3.accounts['Invest'].activate()
# client3.accounts['Credit'].activate()
# client3.get_credit(700000, 24) # Exception: Слишком большая сумма кредита. Банк может выдать вам 50000 руб.
client3.get_credit(30000, 12)
# print(client3.accounts['Debit'].balance)
client3.accounts['Invest'].lets_invest(15000, 6)
# ПОГАСИТЬ КРЕДИТ
# client3.accounts['Credit'].make_payment(33000)
# print(client3.get_all_info())
# print()
print(client3.accounts['Debit'].balance)
client3.close_invest('Invest')
client3.get_all_info()

# # ПОПОЛНЕНИЕ/ СНЯТИЕ/ ПОКУПКИ
# client4.accounts['Debit'].activate()
# client4.accounts['Debit'].top_up_balance(100000)
# try:
#     client4.accounts['Debit'].withdraw(12000)
#     client4.accounts['Debit'].purchase(157, 'coca-cola')
#     client4.accounts['Debit'].purchase(212000, 'iphone 16 PROMAX')
#     client4.accounts['Debit'].purchase(8560, 'АЗС Lukoil')
# except Exception as e:
#     print(e)
# # print(client4.accounts['Debit'].balance)
# print(client4.get_all_info())
#
# bank.get_info()
