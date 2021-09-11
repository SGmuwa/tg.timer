#!/usr/bin/python3
from json import dumps
from os import getenv
from sys import argv
from os import path
from pathlib import Path, PurePath

try:
	from . import Check
except ImportError:
	from check import Check

def main():
	identificator = argv[1] if len(argv) >= 2 else 'checks';
	result = Check.io()
	print(dumps(result.as_dict(), indent=1, ensure_ascii=False, default=str))
	l = input("Сохранить? Напишите «да» для сохранения\n💾 ")
	if l.lower() == "да":
		folder = Path(getenv("CHECKS_OUTPUT_FOLDER", "./data/"))
		folder.mkdir(parents=True, exist_ok=True)
		filepath: Path = folder / Path(identificator)
		filepath = filepath.with_suffix(".json")
		with filepath.open("a") as f:
			f.write(str(result) + "\n")
		print("Сохранено.")
	else:
		print("Отменено.")
	print("Выход.")

if __name__ == "__main__":
	main()
