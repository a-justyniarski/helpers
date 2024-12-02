import hashlib
import importlib
import inspect
import sys
import time
from dataclasses import make_dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import unicodedata

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import TimeoutException, NoSuchElementException, ElementNotInteractableException
from typing_extensions import Union

from func_const import Months

DECORATORS_COUNT = 3

def count_functions_in_current_module():
	current_module = sys.modules[__name__]
	functions = inspect.getmembers(current_module, inspect.isfunction)
	return len(functions)


# DECORATORS
def wait_for(func: callable):
	def decorator(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
			return None

	return decorator


def wait_for_list(func: callable):
	def decorator(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
			return list()

	return decorator


def get_func_or_eptstr(func: callable):
	def decorator(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
			return ''

	return decorator


# Dynamic classes
def create_dataclass(class_name: str, fields: dict, namespace: dict = None):
	if namespace is None:
		namespace = dict()
	annotations = [(field_name, field_type) for field_name, field_type in fields.items()]
	cls = make_dataclass(class_name, annotations, namespace={'__annotations__': annotations, **namespace})
	return cls


# Selenium functions
@wait_for
def buffer(driver, css_selector: str, twait: Union[float, int] = 0.2) -> WebElement or None:
	if css_selector == '':
		return None
	return WebDriverWait(driver, twait).until(ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)))


@wait_for_list
def buffer_all(driver, css_selector, twait: Union[float, int] = 0.2) -> list:
	if css_selector == '':
		return list()
	return WebDriverWait(driver, twait).until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))


@wait_for
def buffer_interactable(driver, css_selector, twait: Union[float, int] = 0.2) -> WebElement or None:
	if css_selector == '':
		return None
	return WebDriverWait(driver, twait).until(ec.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))


def buffer_until_page_fully_loaded(driver, tsleep: float = 2) -> None:
	md5: str = hashlib.md5(bytearray(driver.page_source, 'utf-8')).hexdigest()
	changed: bool = False
	while changed:
		time.sleep(tsleep)
		md5new: str = hashlib.md5(bytearray(driver.page_source, 'utf-8')).hexdigest()
		changed = md5 != md5new
		md5 = md5new


def get_overlapping_element(driver, element) -> WebElement or None:
	rect = element.rect
	result = driver.execute_script(
		"return document.elementFromPoint(arguments[0], arguments[1]);",
		rect['x'] + rect['width'] // 2, rect['y'] + rect['height'] // 2
	)
	if result == element:
		result = None
	return result


@get_func_or_eptstr
def wait_for_text_content(driver, css_selector: str, twait: Union[float, int] = 0.2) -> str:
	"""
	:param twait:
	:param driver: WebDriver
	:param css_selector: CSS Selector
	:return: text content -> str
	"""
	return (
		WebDriverWait(driver, twait)
		.until(ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
		.get_attribute('textContent').strip()
	)


@get_func_or_eptstr
def wait_for_text_content_norm(driver, css_selector: str, twait: Union[float, int] = 0.2) -> str:
	"""
	:param twait:
	:param driver: WebDriver
	:param css_selector: CSS Selector
	:return: text content -> str
	"""
	return " ".join(
		WebDriverWait(driver, twait).until(ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
		.get_attribute('textContent').split()
	).strip().lower()


# Normalization functions
def normalize_string(s: str) -> str:
	return "".join([i.replace(i, normalize_char(i)) for i in s])


def normalize_char(c: str) -> str:
	try:
		cname = unicodedata.name(c)
		cname = cname[:cname.index(' WITH')]
		return unicodedata.lookup(cname)
	except (ValueError, KeyError):
		return c


def prep_decimal_from_string(s: str, precision_fp: int = 2) -> Decimal:
	if precision_fp > 20:
		raise ValueError('Precision has to be smaller than 1E-20')
	precision = str(1 / (10 ** precision_fp))
	if not s.replace('.', '').isdigit():
		return Decimal('0').quantize(Decimal(precision))
	return Decimal(s).quantize(Decimal(precision))


def translate_word_containing_substring(s: str, translator_tuple: tuple[tuple[str, str], ...]) -> str:
	"""
	Translates string s into another string if contains substring from translator_tuple. Otherwise, empty string.
	:param s: any phrase
	:param translator_tuple: tuple of tuple-pairs (substring, translated phrase)
	:return: translated phrase or empty string
	"""
	return "".join(next(iter(list(filter(lambda x: x[0] in s, translator_tuple))), ('', ''))[1])


# Refine functions
def refine_price_val(price_string: str) -> str:
	debt_value_refined: str = "".join(
		[i for i in price_string.replace(',', '.').split() if i.replace('.', '').isdigit()]
	)
	return debt_value_refined or '0'


def refine_eng_capacity(eng_cap_str: str) -> int:
	eng_cap_str: str = "".join(eng_cap_str.replace(',', '.').strip().split('cm')[:-1])
	try:
		return int("".join(
			[i for i in eng_cap_str.strip().split() if i.replace('.', '').isdigit()]
		))
	except ValueError:
		return 0


def refine_mileage(mileage_str: str) -> int:
	try:
		return int("".join(
			[i for i in mileage_str.replace(',', '.').split() if i.replace('.', '').isdigit()]
		))
	except ValueError:
		return 0


def refine_integer(integer_str: str) -> int:
	try:
		return int("".join(
			[i for i in integer_str.replace(',', '.').split() if i.replace('.', '').isdigit()]
		))
	except ValueError:
		return 0


def refine_str_to_digit(s: str):
	return "".join([i for i in s if i.isdigit()])


def refine_timedelta(time_string: str) -> str:
	return "".join([i for i in time_string.split() if i.isdigit()])


# Date functions
def date_d_days_before_now(d: Union[str, int, float]) -> str:
	"""
	:param d: days
	:return: string date format: Y-M-D
	"""
	return (datetime.now() - timedelta(days=float(d))).strftime('%Y-%M-%d')


def format_date_string_d_mword_y(s: str) -> str:
	date: list = s.split()
	try:
		return datetime(
			int(date[-1]), Months.TRANSLATE_POLISH_TO_ENGLISH_FULL_CONJ.get(date[1]),
			int(date[0])
		).strftime('%Y-%m-%d')
	except (IndexError, TypeError):
		return ''


def format_date_string_mword_y(s: str) -> str:
	date: list = s.split()
	try:
		return datetime(int(date[-1]), Months.TRANSLATE_POLISH_TO_ENGLISH_FULL.get(date[0]), 1).strftime('%Y-%m-%d')
	except (IndexError, TypeError):
		return ''


def format_date_string_d_m_y(s: str) -> str:
	date_list: list = s.split('.') if '.' in s else s.split('-')
	if len(date_list) == 3:
		if '.' in s:
			if len(date_list[2]) == 4:
				return datetime.strptime(s, '%d.%m.%Y').strftime('%Y-%m-%d')
			if len(date_list[2]) == 2:
				return datetime.strptime(s, '%d.%m.%y').strftime('%Y-%m-%d')
		if '-' in s:
			if len(date_list[2]) == 4:
				return datetime.strptime(s, '%d-%m-%Y').strftime('%Y-%m-%d')
			if len(date_list[2]) == 2:
				return datetime.strptime(s, '%d-%m-%y').strftime('%Y-%m-%d')
	else:
		return ''


def format_date_string_y_m_d(s: str) -> str:
	date_list: list = s.split('.') if '.' in s else s.split('-')
	if len(date_list) == 3:
		if '.' in s:
			if len(date_list[0]) == 4:
				return datetime.strptime(s, '%Y.%m.%d').strftime('%Y-%m-%d')
			if len(date_list[0]) == 2:
				return datetime.strptime(s, '%y.%m.%d').strftime('%Y-%m-%d')
		if '-' in s:
			if len(date_list[0]) == 4:
				return s
			if len(date_list[0]) == 2:
				return datetime.strptime(s, '%y-%m-%d').strftime('%Y-%m-%d')
	else:
		return ''


# List functions
def get_first_elem(lst: list) -> str or int or float:
	"""Returns first element of a list or empty string if list is empty"""
	return next(iter(lst), '')


def get_first_n_elem_as_str(lst: list, n: int) -> str or int or float:
	"""Returns first n elements of a list as a string or empty string if list is empty"""
	gen = iter(lst)
	s = ''
	for i in range(n):
		try:
			s += next(gen) + ' '
		except StopIteration:
			break
	return s.strip()


def custom_slugify(text: str, separator: str = '-') -> str:
	text = normalize_string(text).replace(' ', separator).lower()
	return text


def calculate_md5(text: str) -> str:
	return hashlib.md5(text.encode("utf-8")).hexdigest()


def calculate_hash(text: str, salt: str = "", shift: int = 0):
	hash_digest = hashlib.md5((text + salt).encode("UTF-8")).digest()
	shifted_digest = bytes((byte + shift) % 256 for byte in hash_digest)
	return shifted_digest.hex()


def soup_get_text_first(parent):
	first_text_occurrence = parent.find_all(text=True, recursive=False)
	return first_text_occurrence[0].strip() if first_text_occurrence else ""


def kebabcase_to_pascalcase(s: str):
	"""Need to be proper kebab-case name"""
	s = s.capitalize()
	new_str_list = [""] * len(s)

	for idx, char in enumerate(reversed(s)):
		real_idx = len(s) - 1 - idx
		if char == "-":
			new_str_list[real_idx+1] = new_str_list[real_idx+1].upper()
			char = ""
		new_str_list[real_idx] = char
	return "".join(new_str_list)


def import_class(module_path: str, class_name: str):
	module = importlib.import_module(module_path)
	return getattr(module, class_name)


if __name__ == '__main__':
	print(f"Function score: {count_functions_in_current_module() + DECORATORS_COUNT*2}")