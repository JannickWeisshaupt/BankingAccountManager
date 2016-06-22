import code
import numpy as np
import sys

a = np.array([1,2,4,5,6,7])


shareVars = {'Betrag':a}

terp = code.InteractiveConsole(shareVars)


code2 = """
print(Betrag.sum())
print(Betrag.mean())
print(Betrag.std())
for i in range(10):
    print(i)
    print('This is working')

print("Code ends here")
"""


import contextlib
@contextlib.contextmanager
def capture():
    import sys
    from io import StringIO
    oldout,olderr = sys.stdout, sys.stderr
    try:
        out=[StringIO(), StringIO()]
        sys.stdout,sys.stderr = out
        yield out
    finally:
        sys.stdout,sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

with capture() as out:
    for line in code2.split('\n'):
##        if len(line)>0:
        terp.push(line)

with capture() as out1:
    terp.runsource(code2)


