"""
@author: Fabian Schaipp
"""

import numpy as np


from sklearn.datasets import fetch_openml
from sklearn.datasets import fetch_rcv1
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state

#from sklearn.datasets import load_digits
#from scipy.stats import ortho_group

from .lasso import Norm1, lsq, block_lsq, logistic_loss
from .tstudent import tstudent_loss

############################################################################################
### Synthetic data
############################################################################################
def standardize(A):   
    # standardize
    M = A - A.mean(axis=0)
    M = (1/M.std(axis=0)) * M
        
    assert max(abs(M.mean(axis=0))) <= 1e-5
    assert max(abs(M.std(axis=0) - 1)) <= 1e-5
    
    return M

def A_target_condition(N, n, smax = 100, smin = 1):
    """creates matrix with condition sqrt(kappa)
    """
    A = np.random.randn(N,n)
    
    U,_,V = np.linalg.svd(A, full_matrices = False)
    
    d = np.linspace(np.sqrt(smax), np.sqrt(smin), min(n,N))
    
    D = np.diag(d)
    A = U @ D @ V
    
    return A
 
def lasso_test(N = 10, n = 20, k = 5, lambda1 = .1, block = False, noise = 0., kappa = None):
    """
    generates data for a LASSO problem with n variables and N samples, where solution has k non-zero entries
    lambda1: regularization parameter of 1-norm
    block: if True, the A_i have different dimensions (>1 rows)
    noise: std. deviation of Gaussian noise added to measurements b
    kappa: if not None, A is created such that is has condition sqrt(kappa)
    """
    if block:
        m = np.random.randint(low = 3, high = 10, size = N)
    else:
        m = np.ones(N, dtype = 'int')
    
    if kappa is None:     
        A = np.random.randn(m.sum(),n)
        A = standardize(A)
    
    else:
        assert kappa > 1
        A = A_target_condition(m.sum(), n, smax = kappa)
    
    # create true solution
    x = np.random.randn(k) 
    x = np.concatenate((x, np.zeros(n-k)))
    np.random.shuffle(x)
    
    # create measurements
    b = A @ x + noise*np.random.randn(N)
    
    A = np.ascontiguousarray(A.astype('float64'))
    b = b.astype('float64')
    x = x.astype('float64')
    
    phi = Norm1(lambda1)    
    if block:
        f = block_lsq(A, b, m)
    else:
        f = lsq(A, b)
        

    return x, A, b, f, phi

def logreg_test(N = 10, n = 20, k = 5, lambda1 = .1, noise = 0, kappa = None):
    """
    creates data for l1-regularized logistic regression with n variables and N samples, where solution has k non-zero entries
    lambda1: regularization parameter of 1-norm
    b \in{-1,1}
    noise = probability of flipping b after generation --> the closer noise is to 1, the nosier the problem becomes
    """
    #np.random.seed(1234)
    
    if kappa is None:     
        A = np.random.randn(N,n) 
        A = standardize(A)
    else:
        assert kappa > 1
        A = A_target_condition(N, n, smax = kappa)
        
    # create true solution
    x = np.random.randn(k) 
    x = np.concatenate((x, np.zeros(n-k)))
    np.random.shuffle(x)
    
    h = np.exp(A@x)
    odds = h/(1+h)
    
    b = (odds >= .5)*2 -1
    #b = np.random.binomial(1,p=odds)*2 - 1
    
    if noise > 0:
        assert noise <= 1
        f = np.random.binomial(n=1, p = noise, size = N)
        f = (1 - f * 2)      
        print((f==-1).sum())      
        # flip signs (f in {-1,1})
        b = b * f
     
    A = np.ascontiguousarray(A.astype('float64'))
    b = b.astype('float64')
    x = x.astype('float64')
    
    phi = Norm1(lambda1) 
    f = logistic_loss(A,b)
    
    return x, A, b, f, phi

def tstudent_test(N = 10, n = 20, k = 5, lambda1 = .1, v = 1, noise = 0.1, scale = 1.):
    """
    """ 
    A = np.random.randn(N,n)
    A = standardize(A)
    A = scale*A
    
    #A = A_target_condition(N, n, smax = 1e6)
    
    # create true solution
    x = np.random.randn(k) 
    x = np.concatenate((x, np.zeros(n-k)))
    np.random.shuffle(x)
       
    b = A@x + noise*np.random.standard_t(v, size = N)
     
    A = np.ascontiguousarray(A.astype('float64'))
    b = b.astype('float64')
    x = x.astype('float64')
    
    phi = Norm1(lambda1) 
    f = tstudent_loss(A,b,v=v)
    
    A_test = standardize(np.random.randn(1000,n))
    b_test = A_test@x + noise*np.random.standard_t(v, size = 1000)
    return x, A, b, f, phi, A_test, b_test

############################################################################################
### Actual data
############################################################################################

def get_mnist(lambda1 = 0.02, train_size = .8, scale = True):

    # Load data from https://www.openml.org/d/554
    X, y0 = fetch_openml('mnist_784', version=1, return_X_y=True)
    y0 = y0.astype('float64')
    y = y0.copy()
    
    set1 = [0,3,6,8,9]
    set2 = [1,2,4,5,7]
    
    y[np.isin(y0, set1)] = 1
    y[np.isin(y0, set2)] = -1
    
    assert np.all(np.isin(y,[-1,1]))
    
    #random_state = check_random_state(0)
    #permutation = random_state.permutation(X.shape[0])
    X = X.astype('float64')
    y = y.astype('float64')
    #X = X.reshape((X.shape[0], -1))
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size = train_size,\
                                                        random_state = 12345)
    
    if scale:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
    
    phi = Norm1(lambda1) 
    f = logistic_loss(X_train, y_train)

    return f, phi, X_train, y_train, X_test, y_test

def get_gisette(lambda1 = 0.02, train_size = .8):
    X = np.load('data/gisette_X.npy')
    y = np.load('data/gisette_y.npy')
    
    assert np.all(np.isin(y,[-1,1]))
    
    X = X.astype('float64')
    y = y.astype('float64')
    
    np.nan_to_num(X, copy = False)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size = train_size,\
                                                        random_state = 1234)
    
    phi = Norm1(lambda1) 
    f = logistic_loss(X_train, y_train)
        
    return f, phi, X_train, y_train, X_test, y_test

#%% misc snippets

# for loading gisette from .txt

# with open('data/gisette_scale', 'r') as f:
        
#         data = []
#         labels = []
#         for line in f:
            
#             tmp = line.split(' ')
#             label = int(tmp[0])
#             feat = tmp[1:]
            
#             keys = []
#             vals = []
#             for f in feat:
#                 if f == '\n':
#                     continue
#                 f.split(':')
#                 keys.append(f.split(':')[0])
#                 vals.append(float(f.split(':')[1]))
            
#             d = dict(zip(keys,vals))
#             data.append(d)
#             labels.append(label)
    
#     print("Done reading")
            
#     y = np.array(labels)
#     X = pd.DataFrame(data).values.astype('float64')
    
# def get_rcv1(lambda1 = 0.02, train_size = .8, scale = True):
    
#     rcv1 = fetch_rcv1()
    
#     X = rcv1.data.astype('float64')
#     y = rcv1.target[:,0].astype('float64')
    
#     X_train, X_test, y_train, y_test = train_test_split(X, y, train_size = train_size)
    
#     if scale:
#         scaler = StandardScaler()
#         X_train = scaler.fit_transform(X_train)
#         X_test = scaler.transform(X_test)
    
#     phi = Norm1(lambda1) 
#     f = logistic_loss(X_train, y_train)
    
#     return f, phi, X_train, y_train, X_test, y_test
