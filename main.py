"""Mini-SQL parser for a limited SELECT grammar.

Supported shape:
	SELECT column1, column2 FROM table WHERE id > 10

The parser returns a dictionary that describes the query structure and
does not connect to any database.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any


class ParseError(ValueError):
	"""Raised when the input query does not match the grammar."""


@dataclass(frozen=True)
class Token:
	kind: str
	value: str
	line: int
	column: int


KEYWORDS = {"SELECT", "FROM", "WHERE"}
OPERATORS = {"=", ">", "<"}


def tokenize(text: str) -> list[Token]:
	tokens: list[Token] = []
	index = 0
	line = 1
	column = 1

	while index < len(text):
		char = text[index]

		if char.isspace():
			if char == "\n":
				line += 1
				column = 1
			else:
				column += 1
			index += 1
			continue

		start_line = line
		start_column = column

		if char == ",":
			tokens.append(Token("COMMA", char, start_line, start_column))
			index += 1
			column += 1
			continue

		if char == "*":
			tokens.append(Token("STAR", char, start_line, start_column))
			index += 1
			column += 1
			continue

		if char in "=><!":
			next_char = text[index + 1] if index + 1 < len(text) else ""
			if char in "><!" and next_char == "=":
				raise ParseError(
					f"Unsupported operator {char + '='!r} at line {start_line}, column {start_column}"
				)
			if char == "!":
				raise ParseError(f"Unexpected character '!' at line {start_line}, column {start_column}")
			tokens.append(Token("OPERATOR", char, start_line, start_column))
			index += 1
			column += 1
			continue

		if char in "'\"":
			quote = char
			index += 1
			column += 1
			value_parts: list[str] = []

			while index < len(text):
				current = text[index]
				if current == "\\" and index + 1 < len(text):
					value_parts.append(text[index + 1])
					index += 2
					column += 2
					continue
				if current == quote:
					break
				if current == "\n":
					raise ParseError(
						f"Unterminated string at line {start_line}, column {start_column}"
					)
				value_parts.append(current)
				index += 1
				column += 1

			if index >= len(text) or text[index] != quote:
				raise ParseError(
					f"Unterminated string at line {start_line}, column {start_column}"
				)

			tokens.append(Token("STRING", "".join(value_parts), start_line, start_column))
			index += 1
			column += 1
			continue

		if char.isdigit():
			start = index
			while index < len(text) and text[index].isdigit():
				index += 1
				column += 1
			tokens.append(Token("NUMBER", text[start:index], start_line, start_column))
			continue

		if char.isalpha() or char == "_":
			start = index
			while index < len(text) and (text[index].isalnum() or text[index] == "_"):
				index += 1
				column += 1
			raw = text[start:index]
			upper = raw.upper()
			kind = "KEYWORD" if upper in KEYWORDS else "IDENTIFIER"
			tokens.append(Token(kind, upper if kind == "KEYWORD" else raw, start_line, start_column))
			continue

		raise ParseError(f"Unexpected character {char!r} at line {line}, column {column}")

	tokens.append(Token("EOF", "", line, column))
	return tokens


class Parser:
	def __init__(self, tokens: list[Token]) -> None:
		self.tokens = tokens
		self.position = 0

	def current(self) -> Token:
		return self.tokens[self.position]

	def advance(self) -> Token:
		token = self.current()
		if token.kind != "EOF":
			self.position += 1
		return token

	def match(self, kind: str, value: str | None = None) -> bool:
		token = self.current()
		if token.kind != kind:
			return False
		if value is not None and token.value != value:
			return False
		self.advance()
		return True

	def expect(self, kind: str, value: str | None = None) -> Token:
		token = self.current()
		if token.kind != kind or (value is not None and token.value != value):
			if value is None:
				expected = kind
			else:
				expected = f"{kind}({value})"
			raise ParseError(
				f"Expected {expected} at line {token.line}, column {token.column}, got {token.kind}({token.value!r})"
			)
		self.advance()
		return token

	def parse(self) -> dict[str, Any]:
		query = self.parse_select()
		self.expect("EOF")
		return query

	def parse_select(self) -> dict[str, Any]:
		self.expect("KEYWORD", "SELECT")
		columns = self.parse_columns()
		self.expect("KEYWORD", "FROM")
		table = self.expect("IDENTIFIER").value

		result: dict[str, Any] = {
			"command": "SELECT",
			"columns": columns,
			"table": table,
		}

		if self.match("KEYWORD", "WHERE"):
			result["where"] = self.parse_condition()

		return result

	def parse_columns(self) -> list[str]:
		if self.match("STAR"):
			return ["*"]

		columns = [self.expect("IDENTIFIER").value]
		while self.match("COMMA"):
			columns.append(self.expect("IDENTIFIER").value)
		return columns

	def parse_condition(self) -> dict[str, Any]:
		left = self.expect("IDENTIFIER").value
		operator = self.expect("OPERATOR").value

		if operator not in OPERATORS:
			token = self.current()
			raise ParseError(
				f"Unsupported operator {operator!r} at line {token.line}, column {token.column}"
			)

		right_token = self.current()
		if right_token.kind == "NUMBER":
			right = int(self.advance().value)
		elif right_token.kind == "STRING":
			right = self.advance().value
		elif right_token.kind == "IDENTIFIER":
			right = self.advance().value
		else:
			raise ParseError(
				f"Expected number, string, or identifier at line {right_token.line}, column {right_token.column}"
			)

		return {"left": left, "op": operator, "right": right}


def parse_sql(text: str) -> dict[str, Any]:
	"""Parse a mini-SQL SELECT query and return its dictionary form."""

	if not text or not text.strip():
		raise ParseError("Query cannot be empty")

	tokens = tokenize(text)
	parser = Parser(tokens)
	return parser.parse()


def main() -> None:
	if len(sys.argv) > 1:
		query = " ".join(sys.argv[1:])
	else:
		query = input("SQL> ").strip()

	try:
		result = parse_sql(query)
	except ParseError as exc:
		print(f"Error: {exc}")
		return

	print(result)


if __name__ == "__main__":
	main()