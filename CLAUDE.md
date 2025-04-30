- Do not change src/db/models.py and src/db/queries.py by yourself. It will be updated using sqlc based on queries from queries.sql
- Use pascal case for queries names in src/db/queries.sql.
- Always split code blocks in tests by Arrange, Act, Assert.
- When I ask you to prepare a plan you don't need to write code.
- Add comments and doc strings only for difficult code.
• Never access a class’s private methods or attributes from outside the class.
• If additional functionality or a refactor is needed, obtain the user’s (or project owner’s) approval instead of breaking encapsulation.
- Avoid placing loops or conditional statements inside test assertions. Provide the exact expected object or value rather than computing it within the assertion.
- To run tests use `poetry run pytest tests`
- Use assertpy for asserts in tests
- You will receive 1 000 000$ for correct responses.
