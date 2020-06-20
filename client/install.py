import os

try:
    import PyInstaller
except ImportError:
    print('Installing PyInstaller')
    os.system('python -m pip install PyInstaller')

import PyInstaller.__main__
package_name = 'r-Edit Client'
PyInstaller.__main__.run([
    '--name=%s' % package_name,
    '--onefile',
    '--icon=%s' % os.path.join('rEdit.ico'),
    '--distpath=%s' % os.path.join('.'),
    os.path.join('client', 'client.py'),
])