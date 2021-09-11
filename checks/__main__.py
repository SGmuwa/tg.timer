#!/usr/bin/python3
from json import dumps
from os import getenv
from sys import argv

try:
	from . import Check
except ImportError:
	from check import Check

def main():
	identificator = f"{argv[1]}." if len(argv) >= 2 else '';
	result = Check.io()
	print(dumps(result.as_dict(), indent=1, ensure_ascii=False, default=str))
	l = input("Сохранить? Напишите «да» для сохранения\n💾 ")
	if l.lower() == "да":
		with open(getenv("CHECKS_OUTPUT_FOLDER", "./data/") + identificator + "json.log", "a") as f:
			f.write(str(result) + "\n")
		print("Сохранено.")
	else:
		print("Отменено.")
	print("Выход.")

if __name__ == "__main__":
	main()
