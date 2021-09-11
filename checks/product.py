from decimal import Decimal
import decimal
from json import dumps
from math import trunc

categories= ["Вкусняшки", "Долг", "Дорога", "Дорога дальняя", "Другое", "Заработная плата Стипендия Пособия Регулярные выплаты", "Здоровье", "Инвестиции", "Канцтовары", "Коммунальные услуги", "Коммуникация", "Подарок", "Продукты", "Развлечения", "Столовая и кафе и рестораны", "Учёт", "Хозяйство"]

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
