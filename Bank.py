from abc import ABC, abstractmethod
from datetime import date, datetime


class CreateHistory:
    def __init__(self, original_cls):
        self.original_cls = original_cls

    def __call__(self, *args, **kwargs):
        instance = self.original_cls(*args, **kwargs)

        def add_to_history(filename, info):
            try:
                if not instance.first_log:
                    with open(f"history/{filename}", 'w', encoding='UTF-8') as file:
                        file.write(f"{info.rstrip()}\n")
                    instance.first_log = True
                else:
                    with open(f"history/{filename}", 'a', encoding='UTF-8') as file:
                        file.write(f"{info.rstrip()}\n")
            except Exception as e:
                print(f"При добавлении записи в историю операций произошла ошибка: '{e}'")

        instance.add_to_history = add_to_history
        return instance


class Bank:

    def __init__(self, overall_balance=10 ** 9, withdraw_limit=10 ** 5, credit_limit=50000, commission=0.05,
                 credit_percent=0.25, invest_percent=0.20, daily_invest_percent=0.10):
        self.overall_balance = overall_balance  # общий баланс
        self.rub_balance = int(overall_balance / 3)
        self.usd_balance = int(overall_balance / 3 / 81)
        self.euro_balance = int(overall_balance / 3 / 92)
        self.bank_accounts = {'Debit': Debit, 'Credit': Credit, 'Invest': Invest, 'DailyInvest': DailyInvest}
        self.bank_currencies = {'rub': self.rub_balance, 'usd': self.usd_balance, 'eur': self.euro_balance}
        self.exchanges = {'rub': 1, 'usd': 81, 'eur': 92}
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
        print(f"Клиент {client} добавлен")
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


class Client:
    def __init__(self, name, bank, accounts):
        self.name = name
        self.solvency = True  # платежеспособность, если да - кредит дадут, если нет - откажут
        self.bank = bank
        self.filenames = []
        self.accounts = self.add_accounts(accounts)
        for name, obj in self.accounts.items():
            filename = self.create_filename(obj)
            self.filenames.append(filename)
            # self.accounts[name].add_to_history(filename, f'Открыт {name} счет в валюте {obj.currency}')

    def add_accounts(self, accounts):
        accounts_obj = {}
        for el in accounts:
            if el[0] not in self.bank.bank_accounts:
                raise Exception(f"Счета {el[0]} не существует")

            name_account = el[0] + '_' + el[1]
            accounts_obj[name_account] = self.bank.bank_accounts[el[0]](self.bank, el[1])
        return accounts_obj

    def create_filename(self, obj):
        f_name = f"{self.name.split()[0]}_{self.name.split()[1]}_{obj.get_name()}_{obj.currency}.txt'"
        obj.filename = f_name
        self.filenames.append(obj.filename)
        return f_name

    def __iadd__(self, account_obj):
        name = account_obj.get_name()
        currency = account_obj.currency

        if name not in self.bank.bank_accounts:
            raise Exception(f"Неизвестный счет")
        if currency not in self.bank.exchanges:
            raise Exception("Неверно указана валюта")

        self.accounts[name + '_' + currency] = account_obj
        self.create_filename(account_obj)
        return self

    def __str__(self):
        return self.name

    def activate_account(self, name, currency):
        name_account = name + '_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name} в валюте {currency}")
        self.accounts[name_account].is_activated = True

    def transfer_to(self, summa, where, currency, from_, currency2, client=None):
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
                          f"Комиссия {commission} руб. Баланс {from_} счета {self.accounts[from_account].balance} "
                          f"{currency}")

        else:  # перевод себе
            if where_account not in self.accounts or from_account not in self.accounts:
                raise Exception(f"Счета не существует")
            if self.accounts[where_account].is_blocked or self.accounts[from_account].is_blocked:
                raise Exception("Счет заблокирован")
            if summa > self.accounts[from_account].balance:
                raise Exception("Недостаточно средств на счете")
            if not self.accounts[where_account].is_activated or not self.accounts[from_account].is_activated:
                raise Exception(f"Счет неактивен")

            to_rub = summa * self.bank.exchanges['rub']
            to_exchange = to_rub // self.bank.exchanges[currency2]

            self.accounts[from_account].balance -= summa
            self.accounts[where_account].balance += to_exchange
            res = (f"Выполнен перевод себе с {from_} счета на {where} счет."
                   f"Сумма перевода {summa} {currency} Баланс {from_} счета {self.accounts[from_account].balance} {currency}")
            filename = self.accounts[from_].filename
        # self.accounts[from_].add_to_history(filename, res)

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
        percent = (self.accounts[name_account].payment * period) - summa

        self.accounts[name_account].balance -= (percent + summa)  # TODO
        print(self.accounts[name_account])
        self.accounts[name_account].payment = int(numerator / denominator)  # TODO
        self.accounts[name_account].period = period  # TODO
        self.solvency = False
        write_down = (
            f"Выдан кредит на сумму {summa} на срок {period} месяцев. "
            f"Платеж составит {self.accounts[name_account].payment} {self.accounts[name_account].currency} "
            f"Процентная ставка {self.bank.credit_percent} %")
        print(write_down)
        # filename = f"{self.name.split()[0]}_{self.name.split()[1]}_{name_account}_{currency}"
        # self.accounts[name_account].add_to_history(filename, write_down)

    def make_payment(self, summa, currency):
        credit_account = 'Credit' + '_' + currency
        debit_account = 'Debit' + '_' + currency

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
            filename = self.accounts[credit_account].filename
            # self.accounts[account].add_to_history(filename, write_down)

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
            write_down = f"Внесен платеж в размере {summa} руб.Остаток долга {self.accounts[credit_account].balance} {currency}"
            filename = self.accounts[credit_account].filename
            # self.accounts[account].add_to_history(filename, write_down)

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
        write_down = f"Счет {name} в валюте {currency} закрыт"
        filename = self.accounts[name_account].filename
        # self.accounts[account].add_to_history(filename, write_down)

    def close_credit(self, name, currency):
        if name != 'Credit':
            raise Exception("Неверный счет")
        name_account = name + '_' + currency
        if name_account not in self.accounts:
            raise Exception(f"Нет счета {name} в валюте {currency}")
        if self.accounts[name_account].balance < 0:
            raise Exception(
                f"Для закрытия кредитного счета погасите задолженность в размере {name_account.balance} {name_account.currency}")
        if self.accounts[name_account].balance == 0:
            self.accounts[name_account].is_activated = False
            write_down = f"Счет {name} в валюте {currency} закрыт"
            filename = self.accounts[name_account].filename
            # self.accounts[account].add_to_history(filename, write_down)

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
        print(f"Вывод денежных средств с инвестиционного счета в размере {summa} {currency}. Счет закрыт.")

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
        print(f"Вывод денежных средств с инвестиционного счета в размере {summa} {currency}. Счет закрыт.")

    def get_all_info(self):
        return f"Данные клиента: {self.name}\nИнформация по счетам:\n{[el.get_info() for el in self.accounts.values()]}"


# @CreateHistory
class Base(ABC):
    def __init__(self, bank, currency):
        self.balance = 0
        self.is_activated = False
        self.is_blocked = False
        self.bank = bank
        self.filename = None
        self.currency = currency
        self.first_log = False

    def check_block(self):
        if self.is_blocked:
            raise Exception("Счет заблокирован")

    def activate(self):
        self.check_block()
        self.is_activated = True

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
        self -= summa
        self.bank.change_balance(summa, self.currency)
        write_down = (f"Снятие наличных с {self.get_name()} счета в размере {summa} {self.currency}. "
                      f"Доступно {self.balance} {self.currency}.")
        # self.add_to_history(self.filename, write_down)

    def calc_commission(self, summa):
        return summa * self.bank.commission

    def __iadd__(self, summa):
        self.balance += summa
        return self

    def __isub__(self, summa):
        self.balance -= summa
        return self

    def top_up_balance(self, summa, transact=False):
        self.check_block()
        if not self.is_activated:  # ПРИ ПОПОЛНЕНИИ БАЛАНСА СЧЕТ АВТОМАТИЧЕСКИ АКТИВИРУЕТСЯ, ЕСЛИ ОН НЕАКТИВЕН
            self.activate()
        self += summa
        write_down = f"Пополнение {self.get_name()} счета в размере {summa} {self.currency}. Доступно {self.balance} {self.currency}."
        # self.add_to_history(self.filename, write_down)
        if not transact:  # если это не перевод
            self.bank.change_balance(summa, self.currency, add=True)

    def purchase(self, summa, curr, name):
        self.check_block()
        if not self.is_activated:
            raise Exception("Счет неактивен")
        if summa > self.balance:
            raise Exception(f"Недостаточно средств на счете на покупку {name}")
        self -= summa
        write_down = f"Покупка {name} в размере {summa} {self.currency} Доступно {self.balance} {self.currency}"
        # self.add_to_history(self.filename, write_down)
        self.bank.change_balance(summa, self.currency, add=False)

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


class Credit(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.payment = 0
        self.period = 0

    def withdraw(self, summa):
        raise Exception("Снятие наличных с кредитного счета недоступно")

    def purchase(self, *args):
        raise Exception("Операция недоступна")

    def credit_info(self):
        print(f"Сумма задолженности {self.balance} {self.currency}")
        print(f"Общий срок кредита {self.period} месяцев")
        print(f"Ежемесячный платеж {self.payment} {self.currency}")
        print(f"Процентная ставка {int(self.bank.credit_percent * 100)} %")

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
        result = (
            f"Вы инвестировали {summa} {self.currency}. на срок {self.period} месяцев под {int(self.bank.invest_percent * 100)} %. "
            f"Прибыль за весь период составит {int(self.balance + self.profit)} {self.currency}.")
        # self.add_to_history(self.filename, result)
        self += summa
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

    def purchase(self, *args):
        raise Exception("Операция недоступна")

    def get_name(self):
        return 'Invest'


class DailyInvest(Base):
    def __init__(self, bank, currency):
        super().__init__(bank, currency)
        self.last_interest_date = date.today()  # Дата последнего начисления процентов

    def accrue_daily_interest(self):
        # today = date.today()
        today = date(2025, 10, 15)
        days_passed = (today - self.last_interest_date).days
        if days_passed < 1:
            return  # 'Проценты уже начислялись сегодня'

        for _ in range(days_passed):
            profit = (self.balance * self.bank.daily_invest_percent) / 365
            self.balance += profit
            self.balance = round(self.balance, 2)
        self.last_interest_date = today

    def lets_invest(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        # days_rate = self.bank.daily_invest_percent / 365
        write_down = (
            f"Вы инвестировали {summa} {self.currency} под {int(self.bank.daily_invest_percent * 100)}%. ")
        # self.add_to_history(self.filename, write_down)
        self.balance += summa
        print(write_down)

    def withdraw(self, summa):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa > self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        bank.bank_currencies[self.currency] -= summa
        write_down = f"Снятие наличных в размере {summa} {self.currency}"
        # self.add_to_history(self.filename, write_down)

    def purchase(self, summa, name):
        if self.is_blocked:
            raise Exception("Счет заблокирован")
        self.accrue_daily_interest()  # начисляем проценты на сумму до снятия
        if summa > self.balance:
            raise Exception("Недостаточно средств")
        self.balance -= summa
        bank.bank_currencies[self.currency] -= summa
        write_down = f"Покупка {name} в размере {summa} {self.currency}"
        # self.add_to_history(self.filename, write_down)

    def get_name(self):
        return 'DailyInvest'


# ______________________________________________________________________________________________________________________
bank = Bank()
client1 = Client("Иванов Иван", bank, [('Debit', 'rub'), ('Debit', 'usd'), ('Invest', 'usd'),
                                       ('Credit', 'rub')])
client2 = Client("Власов Юрий", bank, [('Debit', 'usd'), ('Invest', 'usd'), ('DailyInvest', 'usd')])

client3 = Client("Игнатова Дарья", bank, [('Debit', 'rub')])

bank += client1
bank += client2
bank += client3

# print(client1.accounts)
# print(client2.accounts)
# print(client3.accounts)
# ______________________________________________________________________________________________________________________
# ПРОВЕРКА БАЛАНСА, СНЯТИЕ, ПОПОЛНЕНИЕ

# debit1 = client1.accounts['Debit_rub']
# print(debit1.balance)
# debit1.top_up_balance(50000)
# print(debit1.balance)
# debit1.withdraw(5000)
# print(debit1.balance)
# debit1.purchase(380, 'rub', 'coffee')
# print(debit1.balance)
# ______________________________________________________________________________________________________________________
# ВЗЯТЬ КРЕДИТ, СДЕЛАТЬ ПЛАТЕЖ, ПОГАСИТЬ КРЕДИТ
# TODO работает некорректно
# credit1 = Credit(bank, 'rub')
# client1 += credit1
# print(client1.accounts)
# client1.get_credit(25000, 12, 'rub')
# print(f"Общий баланс дебетового счета с учетом кредитных средств: {debit1.balance}")
# credit1.credit_info()
# ______________________________________________________________________________________________________________________
# ОТКРЫТЬ И ЗАКРЫТЬ ИНВЕСТИЦИОННЫЙ СЧЕТ

# debit2 = client2.accounts['Debit_usd']
# print(debit2.balance)
# invest2 = client2.accounts['Invest_usd']
# invest2.lets_invest(1350, 6)
# print(invest2.balance)
# client2.close_invest('usd')
# ______________________________________________________________________________________________________________________
# ОТКРЫТЬ, ЗАКРЫТЬ СЧЕТ, ПОКУПКИ, ПОПОЛНЕНИЕ, СНЯТИЕ СО СЧЕТА DailyInvest

# debit3 = Debit(bank, 'eur')
# client3 += debit3
# print(debit3.balance)
# daily_invest3 = DailyInvest(bank, 'eur')
# client3 += daily_invest3
# daily_invest3.lets_invest(1350)
# print(daily_invest3.balance)
# daily_invest3.accrue_daily_interest()
# print(daily_invest3.balance)
# daily_invest3.purchase(20, 'coca-cola')
# # client3.close_daily_invest('eur')
# print(daily_invest3.balance)
# daily_invest3.top_up_balance(300)
# print(daily_invest3.balance)
# daily_invest3.withdraw(125)
# print(daily_invest3.balance)
# ______________________________________________________________________________________________________________________
# ПЕРЕВОДЫ МЕЖДУ СВОИМИ СЧЕТАМИ

# debit1 = client1.accounts['Debit_rub']
# debit1_usd = client1.accounts['Debit_usd']
# debit1.activate()
# debit1_usd.activate()
#
# print(debit1.balance)
# print(debit1_usd.balance)
#
# debit1.top_up_balance(50000)
# print(debit1.balance)
#
# client1.transfer_to(3800, 'Debit_usd', 'usd', 'Debit_rub', 'rub')
# print(debit1.balance)
# print(debit1_usd.balance)
# ______________________________________________________________________________________________________________________
# ПЕРЕВОД ДРУГОМУ КЛИЕНТУ

# debit2 = Debit(bank, 'rub')
# client2 += debit2
# debit1 = client1.accounts['Debit_rub']
# debit1.activate()
# debit2.activate()
#
# debit1.top_up_balance(50000)
# print(debit1.balance)
#
# client1.transfer_to(3800, 'Debit_rub', 'rub', 'Debit_rub', 'rub', client=client2)
# print(debit1.balance)
# print(debit2.balance)

# ______________________________________________________________________________________________________________________
# ПРОВЕРКА КОРРЕКТНОСТИ ПЕРЕСЧЕТА ОБЩЕГО БАЛАНСА БАНКА
# TODO работает некорректно
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print(f"Баланс банка в долларах {bank.usd_balance}")
# print(f"Баланс банка в евро {bank.euro_balance}")
# print()
# debit1 = client1.accounts['Debit_rub']
# print(f"Баланс debit1 в рублях {debit1.balance}")
# debit1.top_up_balance(50000)
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print()
# debit1.withdraw(5000)
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print()
# debit1.purchase(380, 'rub', 'coffee')
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")


# ______________________________________________________________________________________________________________________
# ПРОВЕРКА КОРРЕКТНОСТИ ВЫВОДА СПРАВОЧНОЙ ИНФОРМАЦИИ
#
# debit1 = client1.accounts['Debit_rub']
# print(debit1.balance)
# debit1.top_up_balance(50000)
# print(debit1.balance)
# debit1.withdraw(5000)
# print(debit1.balance)
# debit1.purchase(380, 'rub', 'coffee')
# print(debit1.balance)
# print(client1.get_all_info())

# debit3 = Debit(bank, 'eur')
# client3 += debit3
# print(debit3.balance)
# daily_invest3 = DailyInvest(bank, 'eur')
# client3 += daily_invest3
# daily_invest3.lets_invest(1350)
# print(daily_invest3.balance)
# print(client1.get_all_info())
# print()
# bank.get_info()
# ______________________________________________________________________________________________________________________
