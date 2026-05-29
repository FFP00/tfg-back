PYTHON = uv run
SEEDER = app/database/seeders/databaseSeeder.py

migrate-up:
	@$(PYTHON) alembic upgrade head

migrate-down:
	@$(PYTHON) alembic downgrade base

migrate-fresh:
	@$(PYTHON) alembic downgrade base
	@$(PYTHON) alembic upgrade head

migrate-fresh-seed:
	@$(PYTHON) alembic downgrade base
	@$(PYTHON) alembic upgrade head
	@$(PYTHON) $(SEEDER)