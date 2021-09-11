from datetime import datetime
from decimal import Decimal
import decimal
from json import dumps
from math import trunc

try:
	from . import Counterparty
	from . import Product
except ImportError:
	from counterparty import Counterparty
	from product import Product

currencies = ["₽", "€", "Aurum", "MTSS", "RU000A101CY8", "LNTA", "YNDX", "NASDAQ: ATVI"]

datetime_input_formats = ["%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"]
datetime_output_format = "%d.%m.%Y %H:%M:%S"

class Check:
	def __init__(self):
		self._date = None
		self._products = list()
		self._counterparty = None
		self._currency = None
		self._actual_sum = Decimal(0)

	@property
	def date(self) -> str:
		return self._date

	@date.setter
	def date(self, date: str):
		ex = None
		_date = None
		for format in datetime_input_formats:
			try:
				_date = datetime.strptime(date, format)
			except Exception as e:
				ex = e
		if _date is None:
			raise ex
		self._date = date

	def date_io(self):
		self.date = input(f"Введите дату. Пример сегодняшней даты: «{datetime.now().strftime(datetime_input_formats[0])}»:\n🗓")

	@property
	def counterparty(self) -> Counterparty:
		return self._counterparty

	@counterparty.setter
	def counterparty(self, counterparty: Counterparty):
		self._counterparty = counterparty

	def counterparty_io(self):
		while True:
			try:
				self.counterparty = Counterparty.io()
			except ValueError as e:
				i = input(f"В ходе ошибки неудалось создать контрагента. Хотите повторить? («да» для повтора)\nПодробности: {e}\nТекущее состояние: {self}")
				if i.lower() == "да":
					continue
			break

	@property
	def products(self) -> list:
		return [product for product in self._products]

	def products_add(self, product: Product):
		return self._products.append(product)

	def calculate_actual_sum(self) -> Decimal:
		return sum([product.actual_sum for product in self.products])

	def products_add_io(self):
		product = None
		while True:
			try:
				product = Product.io()
			except ValueError as e:
				i = input(f"В неудалось создать позицию в ходе ошибки «{e}». Хотите повторить? («да» для повтора)\nПодробности: {e}\nТекущее состояние: {self}")
				if i.lower() == "да":
					continue
			break
		if product is None:
			print("Отменено добавление позиции")
		else:
			self.products_add(product)
			print(f"Добавлена позиция или продукт: {product}.")
			print(f"Список позиций: " + str([product.name for product in self.products]))
			print("Сумма позиций: " + str(self.calculate_actual_sum()))

	def products_add_all_io(self):
		while True:
			i = input("Добавить" + (" ещё один" if self._products else "") + " товар? «да» для добавления.\n🧺 ")
			if i.lower() != "да":
				break
			self.products_add_io()

	@property
	def currency(self) -> str:
		return self._currency

	@currency.setter
	def currency(self, currency: str):
		if currency not in currencies:
			raise ValueError("Валюта «{currency}» не добавлена в белый список.")
		self._currency = currency

	def currency_io(self):
		message = "Введите номер валюты:\n" + "\n".join([f"{index}: {currency}" for index, currency in enumerate(currencies)]) + "\n💱 "
		while True:
			user_index = input(message)
			try:
				index = int(user_index)
			except ValueError:
				print(f"Номер валюты «{index}» не является числом. Проверьте на ошибки и повторите ввод.")
				continue
			try:
				self.currency = currencies[index]
			except ValueError:
				print("Проверьте на ошибки и повторите ввод номера валюты.")
				continue
			break
		print(f"Валюта: «{self.currency}»")

	@property
	def actual_sum(self):
		return self._actual_sum

	@actual_sum.setter
	def actual_sum(self, actual_sum: str):
		try:
			self._actual_sum = Decimal(actual_sum)
		except decimal.InvalidOperation as e:
			raise ValueError(f"Не получилось прочитать суммарную стоимость. Пример правильного числа: «{Decimal('11')}»") from e

	def actual_sum_io(self):
		self.actual_sum = input(f"Сумма чека. Скорее всего ответ «{Decimal(trunc(self.calculate_actual_sum() * 100))/100}», однако это не всегда так. Посмотрите на чеке и запишите ответ:\n🧮 ")
		print(f"Сумма чека: «{self.actual_sum}»")
	
	def version(self):
		self.version = "v3"

	@classmethod
	def io(cls):
		output = cls()
		functions = [output.counterparty_io, output.date_io, output.currency_io, output.products_add_all_io, output.actual_sum_io, output.version]
		i = 0
		while i < len(functions):
			try:
				functions[i]()
			except Exception as e:
				print(output)
				while True:
					yes = input(f"В ходе выполнения «{functions[i]}» произошла ошибка «{e}». Вы можете повторить. Напишите «повторить» чтобы повторить. Напишите «не повторять» чтобы отменить.")
					if yes == "повторить":
						i -= 1
						break
					elif yes == "не повторять":
						raise ValueError("Пользователь решил отменить заполнение.") from e
					else:
						continue
			i += 1
		return output

	def as_dict(self) -> dict:
		return {
			"version": self.version,
			"date": self.date,
			"products": [product.as_dict() for product in self.products],
			"counterparty": self.counterparty.as_dict() if self.counterparty is not None else None,
			"currency": self.currency,
			"actual_sum": self.actual_sum
		}

	def __str__(self) -> str:
		return dumps(self.as_dict(), ensure_ascii=False, default=str)
