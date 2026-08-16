"""Test config. Deliberately avoids importing anything that needs a live
Postgres/Redis/Ollama connection or WeasyPrint's system libs (Cairo/Pango) -
these tests cover pure business logic only. Full integration testing
happens against the real docker-compose stack (see README).
"""
