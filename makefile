PYTHON = uv run
SEEDER = app/database/seeders/databaseSeeder.py

migrate-fresh:
	@$(PYTHON) alembic downgrade base
	@$(PYTHON) alembic upgrade head

migrate-fresh-seed:
	@$(PYTHON) alembic downgrade base
	@$(PYTHON) alembic upgrade head
	@$(PYTHON) $(SEEDER)