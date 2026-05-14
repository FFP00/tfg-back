PYTHON = uv run
SEEDER = app/database/seeder/databaseSeeder.py

migrate-fresh-seed:
	@$(PYTHON) alembic downgrade base
	@$(PYTHON) alembic upgrade head
	@$(PYTHON) $(SEEDER)