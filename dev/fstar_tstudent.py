"""
This file serves to derive the convex conjugate of the (regularized) likelihood of the t-student loss
"""

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from numba import njit

sp.init_printing(use_unicode=True)


x,b,v, gamma = sp.symbols('x,b,v, gamma')
z = sp.symbols('z', real = True)

f = sp.log(1+((z-b)**2/v)) + gamma/2*z**2
obj = x*z - f

#%% compute stationary point
gamma = 0.251
b = 1.
v = 1.
x = 1.

poly = -gamma* z**3 + (x+2*gamma*b)*z**2 +(-2*x*b-2-gamma*v-gamma*b**2)*z - (x*v+x*b**2+2*b)
poly_fun = lambda z: -gamma* z**3 + (x+2*gamma*b)*z**2 +(-2*x*b-2-gamma*v-gamma*b**2)*z - (x*v+x*b**2+2*b)

# first solution is the real one!
sol = sp.solvers.solve(poly, z)[0]
zstar = sol.simplify()

print(sp.latex(zstar))

#%% draw cubic polynomial

Z = np.linspace(-5,5,100)

plt.figure()
plt.plot(Z, poly_fun(Z))
plt.hlines(0, -5, 5)

#%% compute weak convexity constant

x,b,v = sp.symbols('x,b,v')
z = sp.symbols('z', real = True)

f = sp.log(1+((x-b)**2/v))

g = f.diff(x).simplify()
H = g.diff(x).simplify()

# get stat. point sof Hessian
sols = sp.solvers.solve(H.diff(x), x)

for s in sols:    
    print(H.subs(x, s))

#%% test poly solver

from snspp.helper.data_generation import tstudent_test

v = 1.
x = 1.
b = 1.


xsol, X_train, y_train, f, phi, X_test, y_test = tstudent_test(N = 100, n = 20, k = 3, lambda1 = 0.01, v = v,\
                                                               noise = 0.1, poly = 0, kappa = 15., dist = 'ortho')

#%%
gamma = f.gamma

@njit()
def deiters_method(x, b, tol = 1e-12, max_iter = 5):

    a2 = -(x + 2*gamma*b)/gamma
    a1 = -(-2*b*x - 2 - gamma*v - gamma*(b**2))/gamma
    a0 = -(x*v + x*b**2 + 2*b)/gamma
    
    xinfl = -a2/3
    yinfl = xinfl**3+ a2*xinfl**2 + a1*xinfl +a0
    
    d = a2**2 - 3*a1
    if d >= 0:
        if yinfl < 0 :
            z = xinfl + (2/3)*np.sqrt(d)
        else:
            z = xinfl - (2/3)*np.sqrt(d)
    else:
        z = xinfl
    
    for k in np.arange(max_iter):
        
        fun =     z**3 +   a2*z**2 + a1*z + a0
        deriv = 3*z**2 + 2*a2*z    + a1
        
        if np.abs(fun) <= tol:
            break
        
        z = z - fun/deriv
        
    
    return z

#%%


