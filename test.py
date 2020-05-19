import numpy as np
import matplotlib.pyplot as plt
from lasso import Norm1, lsq

def lasso_test(N = 10, n = 20):
    
    m = np.ones(N, dtype = 'int')

    A = []
    for i in np.arange(N):
        A.append(np.random.rand(m[i], n))
    
    
    A = np.vstack(A)
    b = np.random.randn(m.sum())
    
    x = np.random.rand(n)
    
    phi = Norm1(.1)    
    phi.prox(np.ones(3), alpha = 1)
    
    f = lsq(A, b)

    # for testing only
    sample_size = 5
    alpha = .1
    
    xi = dict(zip(np.arange(N), [np.random.rand(m[i]) for i in np.arange(N)]))

    return
#%%

#m = np.random.randint(low = 3, high = 10, size = N)