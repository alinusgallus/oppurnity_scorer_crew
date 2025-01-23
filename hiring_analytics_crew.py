import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Rest of the existing code...
