from abc import ABC, abstractmethod
from datetime import date

EXCHANGE_RATES = {'Debit': 1, 'Credit': 1, 'Invest': 1, 'DailyInvest': 1,
                  'DebitUSD': 81, 'CreditUSD': 81, 'InvestUSD': 81, 'DailyInvestUSD': 81,
                  'DebitEUR': 92,  'CreditEUR': 92,  'InvestEUR': 92,  'DailyInvestEUR': 92}
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
        # TODO self.transfer_money(client) дописать метод
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
        self.accounts = {}
        if not accounts:
            self.accounts['Debit'] = Debit(bank)
        else:
            for el in accounts:
                if el not in ACCOUNTS:
                    raise Exception(f"Счета {el} не существует")
                self.accounts[el] = ACCOUNTS[el]
        if 'Debit' not in self.accounts:  # если нет дебетового счета - добавляем
            self.accounts['Debit'] = Debit(bank)
        self.name = name
        self.solvency = True  # платежеспособность, если да - кредит дадут, если нет - откажут
        self.bank = bank

    def __iadd__(self, other):
        if other not in ACCOUNTS:
            raise Exception(f"Неизвестный счет")
        self.accounts[other] = ACCOUNTS[other]
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

    def close_invest(self, period):
        if not self.accounts['Invest'].is_activated:
            raise Exception("Счет неактивен")
        if period >= self.accounts['Invest'].period:
            summa = int(self.accounts['Invest'].balance + self.accounts['Invest'].profit)
        else:
            summa = self.accounts['Invest'].balance
            monthly_rate = self.bank.invest_percent * 0.5 / 12  # уменьшаем ставку в два раза
            total = summa * (1 + monthly_rate) ** period
            profit = total - summa
            summa += int(profit)
        self.accounts['Debit'].top_up_balance(summa)
        self.accounts['Invest'].is_activated = False
        # (классовый) декоратор для каждого класса отдельный, который логирует файлики (для каждого клиента история операций,
        # для каждого клиента - отдельный файлик. Создать вручную папку и в ней создавать/ изменять файлики)
        self.accounts['Invest'].balance = 0
        print(f"Вывод денежных средств с инвестиционного счета в размере {summa} руб. Счет закрыт.")

    def get_credit(self, summa, time):
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
            self.accounts['Debit'].top_up_balance(summa)
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
                fine = self.accounts['Credit'].payment * 0.10 # штраф 10% от платежа
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
            client.accounts[where].top_up_balance(summa)
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
        self.history = []
        self.bank = bank
        self.currency = None

    def withdraw(self, summa):
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if self.get_name() == 'Credit':
            summa += self.calc_commission(summa)
        if summa > self.balance:
            raise ValueError(f"Недостаточно средств на счете")
        if summa == self.balance:  # ПРИ ПОПЫТКЕ СНЯТЬ ВСЕ ДЕНЬГИ СЧЕТ БЛОКИРУЕТСЯ
            self.block_account()
        self.balance -= summa
        self.bank.change_balance(summa, add=False)

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def activate(self):
        self.is_activated = True

    def top_up_balance(self, summa):
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self.balance += summa
        self.bank.change_balance(summa, add=True)
        print(f"Пополнение баланса на сумму {summa} {self.currency} Баланс {self.balance} {self.currency}")

    def purchase(self, summa, name):
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if summa > self.balance:
            raise Exception(f"Недостаточно средств на счете на покупку {name}")
        self.balance -= summa
        self.create_history(f"Покупка {name} в размере {summa} {self.currency} Доступно {self.balance} {self.currency}")
        self.bank.change_balance(summa, add=False)
        print(f"Покупка {name} на сумму {summa} {self.currency} Баланс {self.balance} {self.currency}")

    @abstractmethod
    def get_name(self):
        pass

    def show_balance(self):
        print(self.balance)

    def get_info(self):
        return (
            f"Наименование счета: {self.get_name()}. Статус: {'активен' if self.is_activated else 'неактивен'}. "
            f"Текущий баланс: {self.balance} руб. "
            f"История операций: {self.history if self.history else 'По данному счету не было совершено операций'}")

    def create_history(self, info):
        self.history.append(info)

    def block_account(self):
        self.is_blocked = True
        print(f"Ваш счет заблокирован. Обратитесь в банк или по телефону +7(495)567-67-76 для разблокировки.")


class Debit(Base):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'rub'

    def withdraw(self, summa):
        super().withdraw(summa)
        self.create_history(f"Снятие наличных с депозитного счета в размере {summa} руб. Доступно {self.balance} руб.")

    def top_up_balance(self, summa):
        super().top_up_balance(summa)
        self.create_history(f"Пополнение депозитного счета в размере {summa} руб. Доступно {self.balance} руб.")

    def get_name(self):
        return 'Debit'



class DebitUSD(Debit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'usd'

class DebitEUR(Debit):
    def __init__(self, bank):
        super().__init__(bank)
        self.currency = 'eur'


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

    @abstractmethod
    def lets_invest(self, summa, period):
        pass

    def withdraw(self, summa):
        raise Exception("Снятие наличных с инвестиционного счета недоступно")

    def purchase(self, summa, name):
        raise Exception("Операция недоступна")

    @abstractmethod
    def get_name(self):
        pass

    def activate(self):
        self.is_activated = True


class Invest(BaseInvest):
    def __init__(self, bank):
        super().__init__(bank)

    def lets_invest(self, summa, period):
        monthly_rate = self.bank.invest_percent / 12
        total = summa * (1 + monthly_rate) ** period
        self.profit = total - summa

        self.percents = (summa * self.bank.invest_percent * period) / 365
        self.period = period
        result = (
            f"Вы инвестировали {summa} руб. на срок {self.period} месяцев под {int(self.bank.invest_percent * 100)}%. "
            f"Прибыль за весь период составит {int(self.balance + self.profit)} руб.")
        # self.create_history(result)
        self.balance += summa
        print(result)

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
# client1 = Client(name, ('Debit', 'rub'), ('Debit', 'euro')) # комиссия в той валюте, с какого счета мы переводим


bank += client1
bank += client2
bank += client3
bank += client4

# ПОПОЛНЕНИЕ БАЛАНСА И ПЕРЕВОД ДРУГОМУ КЛИЕНТУ
client1.accounts['Debit'].top_up_balance(5000)
# print(client1.accounts['Debit'].balance)
# print(client1.accounts['Debit'].history)

client2.accounts['Debit'].activate()
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
client3.close_invest(2)

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
