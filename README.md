### 12. Uproszczony SQL (Mini-SELECT)
- Opis: Parser czytający zapytania przypominające język SQL.
- Zakres: Zapytania w stylu SELECT kolumna1, kolumna2 FROM tabela WHERE id > 10. Celem jest zbudowanie struktury opisującej, z jakich tabel i po jakich kryteriach ma odbyć się wyszukiwanie (bez podpinania fizycznej bazy danych).
- Czego można się nauczyć: Konstrukcja gramatyki opartej na obligatoryjnych i opcjonalnych słowach kluczowych.

## Mini-SQL parser

Projekt przyjmuje prosty zapis:

```text
SELECT kolumna1, kolumna2 FROM tabela WHERE id > 10
```

### Co robi parser

- rozpoznaje `SELECT`, `FROM` i opcjonalne `WHERE`;
- dzieli wejście na tokeny: słowa kluczowe, identyfikatory, liczby, tekst, przecinki i operatory;
- obsługuje pojedynczy `JOIN` oraz łańcuch warunków w `WHERE` z `AND` / `OR`;
- zwraca wynik jako słownik Pythona;
- zgłasza czytelne błędy, gdy zapytanie nie pasuje do gramatyki.

### Format wyniku

```python
{
	"command": "SELECT",
	"columns": ["name", "age"],
	"table": "users",
	"where": {"left": "id", "op": ">", "right": 10}
}
```

### Minimalna gramatyka

```text
query      -> SELECT columns FROM table [JOIN table ON condition] [WHERE condition (AND|OR condition)*]
columns    -> * | column (, column)*
condition  -> identifier operator value
operator   -> = | > | <
value      -> number | string | identifier
```
