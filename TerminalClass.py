import code
import contextlib
import sys
from io import StringIO

@contextlib.contextmanager
def capture():
    oldout,olderr = sys.stdout, sys.stderr
    try:
        out=[StringIO(), StringIO()]
        sys.stdout,sys.stderr = out
        yield out
    finally:
        sys.stdout,sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

class PythonTerminal(code.InteractiveConsole):


    def __init__(self, shared_vars):
        self.shared_vars = shared_vars
        super().__init__(shared_vars)
        self.out_history = []

    def run_code(self,code_string):
        with capture() as out:
            for line in code_string.split('\n'):
                self.push(line)

        self.out_history.append(out)
        return out

    def restart_interpreter(self):
        self.__init__(self.shared_vars)

if __name__ == '__main__':
    import numpy as np
    a = np.array(range(10))
    PyTerm = PythonTerminal({'Betrag': a})
    test_code = """
print(Betrag.sum())
print(Betrag.mean())
print(Betrag.std())
for i in range(10):
    print(i)
    print('This is working')


print("Code ends here")
import matplotlib.pyplot as plt

# plt.figure()
# plt.plot([1,2,3],[1,2,3])
# plt.show()
#
# plt.figure()
# plt.plot([1,2,3],[1,4,9])
# plt.show()

test_awesomeness = 'This is awesome'

"""
    test2 = """

print(test_awesomeness)
print(test_awesomeness)
print('Yeah')

"""

    out = PyTerm.run_code(test_code)
    print(out)

    out2 = PyTerm.run_code(test2)
    print(out2)

