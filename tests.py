from bank import *
from db import Database


bank = Bank()

client1 = Client("Иванов Иван", bank, [('Debit', 'rub'), ('Debit', 'usd'), ('Invest', 'usd')])
client2 = Client("Власов Юрий", bank, [('Debit', 'usd'), ('Invest', 'usd'), ('DailyInvest', 'usd')])
client3 = Client("Игнатова Дарья", bank, [('Debit', 'rub')])

bank += client1
bank += client2
bank += client3


#################################### ПРОВЕРКА РАБОТЫ ФУНКЦИИ SELECT ####################################

# bank.show_table(select_col=('account', 'client', 'balance', 'currency'), account=('Debit', 'Invest'), client=('Иванов Иван', ))
# bank.show_table(select_col=('account', ), client=('Игнатова Дарья', ))
# bank.show_table(timestamp=(date(2025, 5, 29), ))
# bank.show_table(status=('Заблокирован', ))
# bank.show_table(select_col=('client', 'account'))
# bank.show_table()

#################################### ПРОВЕРКА РАБОТЫ ФУНКЦИИ UPDATE ####################################
# bank.show_table(select_col=('client', 'account', 'status'))
# print()
# bank.update_table(col_name='status', new_val='Неактивен', client=('Иванов Иван', ), status=('Заблокирован', ))
# bank.show_table(select_col=('client', 'account', 'status'))

# bank.show_table(select_col=('client', 'account', 'balance'))
# print()
# bank.update_table(col_name='client', new_val='Меньшова Дарья', client=('Игнатова Дарья', ))
# bank.show_table(select_col=('client', 'account', 'balance'))




#################################### ПРОВЕРКА РАБОТЫ ФУНКЦИИ DELETE ####################################
# bank.show_table(select_col=('account', 'client'))
# print()
# bank.delete_from_db(account=('DailyInvest', ))
# bank.show_table(select_col=('account', 'client'))

# bank.show_table(select_col=('account', 'client', 'currency'))
# print()
# bank.delete_from_db(client=('Иванов Иван', ), currency=('rub', ))
# bank.show_table(select_col=('account', 'client', 'currency'))

# bank.show_table()
# print()
# bank.delete_from_db()
# bank.show_table()

#################################### ЗАПОЛНЕНИЕ БД ####################################

# CLIENT Иванов Иван
# debit1 = client1.accounts['Debit_rub']
# debit1.top_up_balance(5000)
# debit1.withdraw(500)
# debit1.purchase(380, 'coffee')
# debit1.purchase(120.70, 'coca-cola')

# credit1 = Credit(bank, 'rub')
# client1 += credit1
# client1.get_credit(25000, 12, 'rub')
# client1.make_payment(2500, 'rub')

# debit1_usd = client1.accounts['Debit_usd']
# debit1_usd.activate()

# debit1_usd.top_up_balance(325)
# client1.transfer_to(150, 'Debit_usd', 'usd', 'Debit_rub', 'rub')

# invest_usd1 = client1.accounts['Invest_usd']
# invest_usd1.activate()

# # CLIENT Власов Юрий
# debit2 = Debit(bank, 'rub')
# client2 += debit2
# debit2.activate()

# invest2 = client2.accounts['Invest_usd']
# invest2.lets_invest(1350, 6)
# client2.close_invest('usd')

# client1.transfer_to(3800, 'Debit_rub', 'rub', 'Debit_rub', 'rub', client=client2)

# # CLIENT Игнатова Дарья

# debit3 = Debit(bank, 'eur')
# client3 += debit3
# daily_invest3 = DailyInvest(bank, 'eur')
# client3 += daily_invest3
# daily_invest3.activate()

# daily_invest3.lets_invest(1350)
# daily_invest3.accrue_daily_interest()
# daily_invest3.purchase(12, 'icecream')
# daily_invest3.top_up_balance(300)
# daily_invest3.withdraw(125)

#################################### ПРОВЕРКИ РАБОТЫ ФУНКЦИЙ bank.py ####################################



# ПРОВЕРКА БАЛАНСА, СНЯТИЕ, ПОПОЛНЕНИЕ

# debit1 = client1.accounts['Debit_rub']
# print(debit1.balance)
# debit1.top_up_balance(5000)
# print(debit1.balance)
# debit1.withdraw(500)
# print(debit1.balance)
# debit1.purchase(380, 'coffee')
# print(debit1.balance)
# debit1.purchase(120, 'icecream')
# balance = debit1.balance
# debit1.withdraw(balance)



# ВЗЯТЬ КРЕДИТ, СДЕЛАТЬ ПЛАТЕЖ, ПОГАСИТЬ КРЕДИТ

# credit1 = Credit(bank, 'rub')
# client1 += credit1
# print(client1.accounts)
# client1.get_credit(25000, 12, 'rub')
# debit1 = client1.accounts['Debit_rub']
# print(f"Общий баланс дебетового счета с учетом кредитных средств: {debit1.balance}")
# credit1.credit_info()



# ОТКРЫТЬ И ЗАКРЫТЬ ИНВЕСТИЦИОННЫЙ СЧЕТ



# debit2 = client2.accounts['Debit_usd']
# print(debit2.balance)
# invest2 = client2.accounts['Invest_usd']
# invest2.lets_invest(1350, 6)
# print(invest2.balance)
# client2.close_invest('usd')



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



# ПЕРЕВОДЫ МЕЖДУ СВОИМИ СЧЕТАМИ В РАЗНОЙ ВАЛЮТЕ

# debit1 = client1.accounts['Debit_rub']
# debit1_usd = client1.accounts['Debit_usd']
# debit1.activate()
# debit1_usd.activate()

# print(f"Баланс дебетового счета: {debit1.balance} руб")
# print(f"Баланс дебетового счета: {debit1_usd.balance} usd")
# print()
# debit1_usd.top_up_balance(50000)
# print("Пополнение дебетового счета в размере 50000 usd")
# print(f"Баланс дебетового счета: {debit1_usd.balance} usd")
# print()
# client1.transfer_to(3800, 'Debit_usd', 'usd', 'Debit_rub', 'rub', )
# print("Перевод 3800 рублей на USD-счет")
# print()
# print(f"Баланс дебетового счета: {debit1.balance} руб")
# print(f"Баланс дебетового счета: {debit1_usd.balance} usd")



# ПЕРЕВОДЫ МЕЖДУ СВОИМИ СЧЕТАМИ В ОДИНАКОВОЙ ВАЛЮТЕ

# debit1_usd = client1.accounts['Debit_usd']
# invest_usd1 = client1.accounts['Invest_usd']

# debit1_usd.activate()
# invest_usd1.activate()


# print(f"Баланс дебетового счета: {debit1_usd.balance}")
# print(f"Баланс инвест счета: {invest_usd1.balance}")
# print()
# debit1_usd.top_up_balance(2400)
# print("Пополнение дебетового счета в размере 2400 usd")
# print(f"Баланс дебетового счета: {debit1_usd.balance}")
# print()
# client1.transfer_to(800, 'Debit_usd', 'usd', 'Invest_usd', 'usd')
# print("Перевод 3800 usd на инвест счет")
# print()
# print(f"Баланс дебетового счета: {debit1_usd.balance}")
# print(f"Баланс инвест счета: {invest_usd1.balance}")



# ПЕРЕВОД ДРУГОМУ КЛИЕНТУ
#
# debit2 = Debit(bank, 'rub')
# client2 += debit2
# debit1 = client1.accounts['Debit_rub']
# debit1.activate()
# debit2.activate()

# print(f"Баланс дебетового счетат клиента1: {debit1.balance} руб")
# print(f"Баланс дебетового счетат клиента2: {debit2.balance} руб")
# print()
# debit1.top_up_balance(50000)
# print(f"Баланс дебетового счетат клиента1: {debit1.balance} руб")
# print()
# client1.transfer_to(3800, 'Debit_rub', 'rub', 'Debit_rub', 'rub', client=client2)
# print("перевод 3800 руб со счета клиента1 на счет клиента2")
# print()
# print(f"Баланс дебетового счетат клиента1: {debit1.balance} руб")
# print(f"Баланс дебетового счетат клиента2: {debit2.balance} руб")



# ПРОВЕРКА КОРРЕКТНОСТИ ПЕРЕСЧЕТА ОБЩЕГО БАЛАНСА БАНКА

# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print(f"Баланс банка в долларах {bank.usd_balance}")
# print(f"Баланс банка в евро {bank.eur_balance}")
# print()
# debit1 = client1.accounts['Debit_rub']
# print(f"Баланс debit1 в рублях {debit1.balance}")
# debit1.top_up_balance(50000)
# print("Пополнение debit1 на сумму 50000 руб")
# print()
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.bank_currencies['rub']}")
# print()
# debit1.withdraw(5000)
# print("Снятие с debit1 5000 руб")
# print()
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
# print()
# debit1.purchase(380, 'coffee')
# print("Покупка на сумму 380")
# print()
# print(f"Баланс debit1 в рублях {debit1.balance}")
# print(f"Общий баланс банка {bank.overall_balance}")
# print(f"Баланс банка в рублях {bank.rub_balance}")
