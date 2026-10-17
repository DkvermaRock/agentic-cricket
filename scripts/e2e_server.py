import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import uvicorn

with tempfile.TemporaryDirectory(prefix='boundary-e2e-') as directory:
    for name in ('DATABASE_URL','RENDER','CRICKET_REQUIRE_AUTH','CRICKET_DEMO_PASSWORD'):
        os.environ.pop(name,None)
    os.environ['CRICKET_DB_PATH']=str(Path(directory)/'arena.sqlite3')
    uvicorn.run('backend.app:app',host='127.0.0.1',port=8011)
