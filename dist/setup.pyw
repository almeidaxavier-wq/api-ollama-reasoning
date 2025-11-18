import os

def install(instalation_path:str):
    with open(os.path.join(instalation_path, 'desktop.pyw'), 'w') as file:
        file.write('import webview\n\nwindow = webview.create_window("Sunaria AI", "https://api-ollama-reasoning-gamma.vercel.app/"'
                   'width=1000, heigth=600, resizable=True))\n\n'
                   'window.start()'
        )

if __name__ == '__main__':
    original_path, symbolic_path = None, None

    if os.name == 'posix':
        original_path = os.path.join('usr', 'opt', 'Sunaria AI')
        symbolic_path = os.path.join('usr', 'home', os.getlogin(), 'Desktop', 'Sunaria AI')

    else:
        original_path = os.path.join('C:', 'Program Files', 'Sunaria AI')
        symbolic_path = os.path.join('C:', 'Users', os.getlogin(), 'Desktop', 'Sunaria AI')

    install(original_path)
    os.symlink(symbolic_path, original_path)
