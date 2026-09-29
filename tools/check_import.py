import sys, traceback, importlib
sys.path.insert(0, 'backend')
try:
    importlib.import_module('app.main')
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
