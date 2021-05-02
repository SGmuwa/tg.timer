#!/usr/bin/python3.9
from datetime import datetime
from enum import Enum
from decimal import Decimal
from dataclasses import dataclass, field
from json import dumps
from types import Callable, Optional

#@dataclass
#class Field
	#name: Callable[["Field", str]]
	#setter: Callable[[str]]
	#getter: Callable[[str]]
	#examples: Callable[[str]]

class IO:
	def previous_field(self, current_filed: str) -> dict:
		raise NotImplementedError
	
	def next_field(self, current_field: str) -> dict:
		raise NotImplementedError

categories: list[str] = ["Вкусняшки", "Долг", "Дорога", "Дорога дальняя", "Другое", "Заработная плата Стипендия Пособия Регулярные выплаты", "Здоровье", "Инвестиции", "Канцтовары", "Коммунальные услуги", "Коммуникация", "Подарок", "Продукты", "Развлечения", "Столовая и кафе и рестораны", "Учёт", "Хозяйство"]

class Category:
	pass
	#def __init__(self):
		#if name not in categories:
			#raise ValueError(f"{name} не может быть категорией.")
		#self.name = name

typeo_all = ["Индивидуальный предприниматель (ИП)", "Общество с ограниченной ответственностью (ООО)", "Акционерное общество (АО)", "Некоммерческая организация (НКО)", "Обособленное подразделение (ОП)", "Товарищество собственников жилья (ТСЖ)"]

class Company:
	@property
	def location(self) -> str:
		return self._location
	
	@location.setter
	def location_set(self, location: str):
		if type(location) != str:
			raise ValueError(f"Местоположение не может быть «{location}» ({type(location)}).")
		self._location = location
	
	def location_io(self):
		self._location = input("Введите местоположение организации: ")
	
	@property
	def typeo(self) -> str:
		return self._typeo
	
	@typeo.setter
	def typeo_set(self, typeo: str):
		if typeo not in typeo_all:
			raise ValueError(f"Категория не может быть «{typeo}» ({type(typeo)}), она должна быть одна из: {typeo_all}")
		self._typeo = typeo
	
	def typeo_io(self):
		message = "Введите номер типа организации:\n" + "\n".join([f"{index}: {typeo}" for index, typeo in enumerate(typeo_all)]) + "\n"
		user_index = input(message)
		index = int(user_index)
		self._typeo = typeo_all[index]
	
	@property
	def name(self) -> str:
		return self._name
	
	@name.setter
	def name_set(self, name: str):
		if type(name) != str:
			raise ValueError(f"Название должно быть строкой. «{name}» ({type(name)})")
		if name == "":
			raise ValueError(f"Название не может быть пустым")
		self._name = name
	
	def name_io(self):
		self._name = input("Название организации: ")
	
	@classmethod
	def io(cls) -> "Company":
		output = cls()
		output.location_io()
		output.typeo_io()
		output.name_io()
		return output

currency_names = ["₽", "€", "Aurum", "MTSS", "RU000A101CY8", "LNTA", "YNDX", "NASDAQ: ATVI"]

class Currency:
	@property
	def name(self) -> str:
		return self.name
	
	@name.setter
	def name_set(self, name: str):
		if name not in currency_names:
			raise ValueError(f"Невозможное название валюты «{name}» ({type(name)}). Возможные названия: {currency_names}")
		self._name = name

@dataclass
class Product:
	name: str = ""
	price: Decimal = Decimal(0)
	count: Decimal = Decimal(0)
	actual_sum: Decimal = Decimal(0)

@dataclass
class Check:
	date: datetime = datetime.min
	company: Company = Company()
	products: list[Product] = field(default_factory=list)
	category: Category = Category()
	currency: Currency = Currency()
	
	def __init__(self):
		pass

def main():
	print(dumps(Company.io().__dict__, ensure_ascii=False))

if __name__ == "__main__":
	main()
