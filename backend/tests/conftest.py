import os
import tempfile

# Must run before any backend module is imported so tests never touch a real database.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="urbanpulse-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TEST_DB_DIR, 'test.db')}"
os.environ["SUPABASE_DB_URL"] = ""
os.environ["SUPABASE_DB_PASSWORD"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_ANON_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
