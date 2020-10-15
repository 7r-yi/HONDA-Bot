import subprocess


if __name__ == '__main__':
    while True:
        output = subprocess.run(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if "shutdown" in str(output.stdout):
            break
