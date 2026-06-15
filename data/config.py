from pathlib import Path
import os, dotenv
from urllib.parse import quote

dotenv.load_dotenv()

images_path = Path(os.getenv('IMAGES_PATH'))
db_host = os.getenv('DB_HOST')
db_pass = quote(os.getenv('DB_PASS'))
