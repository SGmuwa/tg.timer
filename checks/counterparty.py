from json import dumps

typeo_all = [
	"Индивидуальный предприниматель (ИП)",
	"Общество с ограниченной ответственностью (ООО)",
	"Акционерное общество (АО)",
	"Некоммерческая организация (НКО)",
	"Обособленное подразделение (ОП)",
	"Товарищество собственников жилья (ТСЖ)",
	"Физическое лицо (ФЛ)"
]

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

	@property
	def nickname(self) -> str:
		return self._nickname

	@nickname.setter
	def nickname(self, nickname: str):
		if type(nickname) != str:
			raise ValueError(f"Кличка должна быть строкой. «{nickname}» ({type(nickname)})")
		if nickname == "":
			raise ValueError(f"Кличка не может быть пустым")
		self._nickname = nickname

	def nickname_io(self):
		self.nickname = input("Кличка организации или человека:\n🕶 ")
		print(f"Имя контрагента: «{self.nickname}»")

	@classmethod
	def io(cls) -> "Counterparty":
		output = cls()
		print("Заполнение контрагента.")
		output.nickname_io()
		output.typeo_io()
		output.name_io()
		output.location_io()
		print(f"Контрагент: {output}")
		return output

	def as_dict(self) -> dict:
		return {"location": self.location, "typeo": self.typeo, "name": self.name, "nickname": self.nickname}

	def __str__(self):
		return dumps(self.as_dict(), ensure_ascii=False)
