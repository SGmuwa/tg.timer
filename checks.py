#!/usr/bin/python3.8
from datetime import datetime
from decimal import Decimal
import decimal
from json import dumps
from math import trunc
from os import getenv
from sys import argv

categories= ["Вкусняшки", "Долг", "Дорога", "Дорога дальняя", "Другое", "Заработная плата Стипендия Пособия Регулярные выплаты", "Здоровье", "Инвестиции", "Канцтовары", "Коммунальные услуги", "Коммуникация", "Подарок", "Продукты", "Развлечения", "Столовая и кафе и рестораны", "Учёт", "Хозяйство"]

currencies = ["₽", "€", "Aurum", "MTSS", "RU000A101CY8", "LNTA", "YNDX", "NASDAQ: ATVI"]

typeo_all = ["Индивидуальный предприниматель (ИП)", "Общество с ограниченной ответственностью (ООО)", "Акционерное общество (АО)", "Некоммерческая организация (НКО)", "Обособленное подразделение (ОП)", "Товарищество собственников жилья (ТСЖ)", "Физическое лицо (ФЛ)"]

class Counterparty:
	@property
	def location(self) -> str:
		return self._location
	
	@location.setter
	def location(self, location: str):
		if type(location) != str:
			raise ValueError(f"Местоположение не может быть «{location}» ({type(location)}).")
		self._location = location
	
	def location_io(self):
		self.location = input("Введите местоположение транзакции (адрес):\n📍 ")
		print(f"Местоположение транзакции: «{self.location}»")
	
	@property
	def typeo(self) -> str:
		return self._typeo
	
	@typeo.setter
	def typeo(self, typeo: str):
		if typeo not in typeo_all:
			raise ValueError(f"Категория не может быть «{typeo}» ({type(typeo)}), она должна быть одна из: {typeo_all}")
		self._typeo = typeo
	
	def typeo_io(self):
		message = "Введите номер типа организации:\n" + "\n".join([f"{index}: {typeo}" for index, typeo in enumerate(typeo_all)]) + "\n🐝 "
		user_index = input(message)
		try:
			index = int(user_index)
		except ValueError as e: # if index is not int
			#if user_index not in typeo_all:
				#print(f"Внимание, выбран тип организации «{user_index}» (не число и нет среди стандартных)")
			self.typeo = user_index
		else:
			self.typeo = typeo_all[index]
		print(f"Тип организации: «{self.typeo}»")
	
	@property
	def name(self) -> str:
		return self._name
	
	@name.setter
	def name(self, name: str):
		if type(name) != str:
			raise ValueError(f"Название должно быть строкой. «{name}» ({type(name)})")
		if name == "":
			raise ValueError(f"Название не может быть пустым")
		self._name = name
	
	def name_io(self):
		self.name = input("Название организации или ИОФ человека если ФЛ:\n🕴 ")
		print(f"Имя контрагента: «{self.name}»")
	
	@classmethod
	def io(cls) -> "Counterparty":
		output = cls()
		print("Заполнение контрагента.")
		output.location_io()
		output.typeo_io()
		output.name_io()
		print(f"Контрагент: {output}")
		return output
	
	def as_dict(self) -> dict:
		return {"location": self.location, "typeo": self.typeo, "name": self.name}
	
	def __str__(self):
		return dumps(self.as_dict(), ensure_ascii=False)

currency_names = ["₽", "€", "Aurum", "MTSS", "RU000A101CY8", "LNTA", "YNDX", "NASDAQ: ATVI"]

class Product:
	def __init__(self):
		self._name = ""
		self._price = Decimal(0)
		self._count = Decimal(0)
		self._actual_sum = Decimal(0)
		self._category = None
	
	@property
	def name(self) -> str:
		return self._name
	
	@name.setter
	def name(self, name: str):
		if not name:
			raise ValueError(f"Название продукта «{name}» пустое.")
		self._name = name
	
	def name_io(self):
		self.name = input("Введите название продукта:\n🕯 ")
		print(f"Название продукта: «{self.name}»")
	
	@property
	def category(self) -> str:
		return self._category
	
	@category.setter
	def category(self, category: str):
		if category not in categories:
			raise ValueError("Категория «{category}» не добавлена в белый список.")
		self._category = category
	
	def category_io(self):
		message = "Введите номер категории:\n" + "\n".join([f"{index}: {category}" for index, category in enumerate(categories)]) + "\n🚤 "
		while True:
			user_index = input(message)
			try:
				index = int(user_index)
			except ValueError:
				print(f"Номер категории «{index}» не является числом. Проверьте на ошибки и повторите ввод.")
				continue
			try:
				self.category = categories[index]
			except ValueError:
				print("Проверьте на ошибки и повторите ввод номера категории.")
				continue
			break
		print(f"Категория: «{self.category}»")
	
	@property
	def price(self) -> Decimal:
		return self._price
	
	@price.setter
	def price(self, price: str):
		try:
			self._price = Decimal(price)
		except decimal.InvalidOperation as e:
			raise ValueError(f"Не получилось прочитать стоимость. Пример правильного числа: «{Decimal('3.14')}»") from e
	
	def price_io(self):
		self.price = input(f"Введите стоимость одной единицы товара (сколько рублей за одну упаковку, киллограмм, литр и так далее…). Пример: «{Decimal('99.99')}»\n🔧 ")
		print(f"Цена товара: {self.price}")
	
	@property
	def count(self):
		return self._count
	
	@count.setter
	def count(self, count: str):
		try:
			self._count = Decimal(count)
		except decimal.InvalidOperation as e:
			raise ValueError(f"Не получилось прочитать количество. Пример правильного числа: «{Decimal('3.14')}»") from e
	
	def count_io(self):
		self.count = input(f"Введите количество (сколько упаковок, килограмм, грамм, литров) купленного товара. Пример: «{Decimal('8')}»\n🔨 ")
		print(f"Количество: «{self.count}»")
	
	@property
	def actual_sum(self):
		return self._actual_sum
	
	@actual_sum.setter
	def actual_sum(self, actual_sum: str):
		try:
			self._actual_sum = Decimal(actual_sum)
		except decimal.InvalidOperation as e:
			raise ValueError(f"Не получилось прочитать цену позиции в чеке. Пример правильного числа: «{Decimal('25.12')}»") from e
	
	def actual_sum_io(self):
		self.actual_sum = input(f"Введите, сколько рублей вышло за товар. Скорее всего ответ «{Decimal(trunc((self.price * self.count) * 100))/100}», однако это не всегда так. Посмотрите на чеке и запишите ответ:\n🛠 ")
		print(f"Сумма позиции: «{self.actual_sum}»")
	
	@classmethod
	def io(cls):
		output = cls()
		output.name_io()
		output.category_io()
		output.price_io()
		output.count_io()
		output.actual_sum_io()
		print(f"Продукт: «{output}»")
		return output
	
	def as_dict(self) -> dict:
		return {
			"name": self.name,
			"category": self.category,
			"price": self.price,
			"count": self.count,
			"actual_sum": self.actual_sum
		}
	
	def __str__(self) -> str:
		return dumps(self.as_dict(), default=str, ensure_ascii=False)

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
	
	@classmethod
	def io(cls):
		output = cls()
		functions = [output.counterparty_io, output.date_io, output.currency_io, output.products_add_all_io, output.actual_sum_io]
		i = 0
		while i < len(functions):
			try:
				functions[i]()
			except Exception as e:
				print(output)
				yes = input(f"В ходе выполнения «{functions[i]}» произошла ошибка «{e}». Вы можете повторить. Напишите «да» чтобы повторить.")
				if yes == "да":
					continue
				else:
					raise ValueError("Пользователь решил отменить заполнение.") from e
			i += 1
		return output
	
	def as_dict(self) -> dict:
		return {
			"date": self.date,
			"products": [product.as_dict() for product in self.products],
			"counterparty": self.counterparty.as_dict() if self.counterparty is not None else None,
			"currency": self.currency,
			"actual_sum": self.actual_sum
		}
	
	def __str__(self) -> str:
		return dumps(self.as_dict(), ensure_ascii=False, default=str)


def main():
	identificator = f"{argv[0]}." if len(argv) >= 1 else '';
	result = Check.io()
	print(dumps(result.as_dict(), indent=1, ensure_ascii=False, default=str))
	l = input("Сохранить? Напишите «да» для сохранения\n💾 ")
	if l.lower() == "да":
		with open(os.getenv("OUTPUT_FOLDER", "./data/") + identificator + "json.log", "a") as f:
			f.write(str(result) + "\n")
		print("Сохранено.")
	else:
		print("Отменено.")
	print("Выход.")

if __name__ == "__main__":
	main()
