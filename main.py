from bank import *
from db import Database


bank = Bank()
client1 = Client("Иванов Иван", bank, [('Debit', 'rub'), ('Debit', 'usd'), ('Invest', 'usd'),
                                       ('Credit', 'rub')])
client2 = Client("Власов Юрий", bank, [('Debit', 'usd'), ('Invest', 'usd'), ('DailyInvest', 'usd')])
#
client3 = Client("Игнатова Дарья", bank, [('Debit', 'rub')])
#
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
#
# debit2 = Debit(bank, 'rub')
# client2 += debit2
# debit1 = client1.accounts['Debit_rub']
# debit1.activate()
# debit2.activate()
#
# debit1.top_up_balance(50000)
# print(debit1.balance)

# client1.transfer_to(3800, 'Debit_rub', 'rub', 'Debit_rub', 'rub', client=client2)
# print(debit1.balance)
# print(debit2.balance)

# ______________________________________________________________________________________________________________________
# ПРОВЕРКА КОРРЕКТНОСТИ ПЕРЕСЧЕТА ОБЩЕГО БАЛАНСА БАНКА
# TODO работает некорректно
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print(f"Баланс банка в долларах {bank.usd_balance}")
# print(f"Баланс банка в евро {bank.eur_balance}")
# print()
# debit1 = client1.accounts['Debit_rub']
# print(f"Баланс debit1 в рублях {debit1.balance}")
# debit1.top_up_balance(50000)
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.bank_currencies['rub']}")
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
