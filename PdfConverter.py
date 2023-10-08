import subprocess
import os

class PDFConverter:
    def __init__(self):
        self.target_dir = os.path.join(os.getcwd(), 'miscs')
        self.file_list = [i for i in os.listdir(self.target_dir) if '.pdf' in i]

    def batch_convert(self):
        for filename in self.file_list:
            # filepath = os.path.join(self.target_dir, filename)
            self.single_convert(filename)

    def single_convert(self, filename):
        result = subprocess.run(
            [
               'docker',
               'run',
               '-ti',
               '--rm',
               '-v',
               f'{self.target_dir}:/pdf',
               '-w',
               '/pdf',
               'pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-alpine-3.12.0-x86_64',
               '--zoom',
               '1.3',
                filename,
            ]
        )
        if result.returncode == 0:
            print(f'Success : {filename}')
        else:
            print(f'Failure : {filename}')

if __name__ == "__main__":
    converter = PDFConverter()
    converter.batch_convert()