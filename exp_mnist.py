import sys

if len(sys.argv) > 1:
    save = sys.argv[1]
else:
    save = False

#%%
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from snspp.solver.opt_problem import problem
from snspp.helper.data_generation import get_mnist
from snspp.experiments.experiment_utils import params_tuner, plot_multiple, plot_multiple_error, eval_test_set, initialize_solvers,\
                                                convert_to_dict, logreg_loss

from sklearn.linear_model import LogisticRegression


f, phi, X_train, y_train, X_test, y_test = get_mnist()

#plt.imshow(X_train[119,:].reshape(28,28))

print("Regularization parameter lambda:", phi.lambda1)

#%% solve with scikit (SAGA)

sk = LogisticRegression(penalty = 'l1', C = 1/(f.N * phi.lambda1), fit_intercept= False, tol = 1e-9, \
                        solver = 'saga', max_iter = 300, verbose = 1)


start = time.time()
sk.fit(X_train, y_train)
end = time.time()

print(f"Computing time: {end-start} sec")

x_sk = sk.coef_.copy().squeeze()

psi_star = f.eval(x_sk) + phi.eval(x_sk)
print("psi(x*) = ", psi_star)

initialize_solvers(f, phi)

#%% params

params_saga = {'n_epochs': 20, 'alpha': 55.}

params_svrg = {'n_epochs': 20, 'batch_size': 650, 'alpha': 50000.}

params_adagrad = {'n_epochs' : 120, 'batch_size': int(f.N*0.05), 'alpha': 0.03}

params_snspp = {'max_iter' : 70, 'batch_size': 560, 'sample_style': 'fast_increasing', \
          'alpha' : 6., 'reduce_variance': True}
    
    
#params_tuner(f, phi, solver = "svrg", alpha_range = np.linspace(2e4, 6e4, 7), batch_range = np.array([100, 650]))
#params_tuner(f, phi, solver = "saga", alpha_range = np.linspace(50, 120, 8))
#params_tuner(f, phi, solver = "adagrad", batch_range = np.array([100, 1000, 3000]))

#%% solve with SAGA

Q = problem(f, phi, tol = 1e-9, params = params_saga, verbose = True, measure = True)

Q.solve(solver = 'saga')

print(f.eval(Q.x)+phi.eval(Q.x))

#%% solve with ADAGRAD

Q1 = problem(f, phi, tol = 1e-9, params = params_adagrad, verbose = True, measure = True)

Q1.solve(solver = 'adagrad')

print(f.eval(Q1.x)+phi.eval(Q1.x))

#%% solve with SVRG

Q2 = problem(f, phi, tol = 1e-9, params = params_svrg, verbose = True, measure = True)

Q2.solve(solver = 'svrg')

print(f.eval(Q2.x)+phi.eval(Q2.x))

#%% solve with SSNSP

P = problem(f, phi, tol = 1e-9, params = params_snspp, verbose = True, measure = True)
P.solve(solver = 'snspp')


#%%

###########################################################################
# multiple execution and plotting
############################################################################

#%% solve with SAGA (multiple times)

K = 20
allQ = list()
for k in range(K):
    
    Q_k = problem(f, phi, tol = 1e-9, params = params_saga, verbose = True, measure = True)
    Q_k.solve(solver = 'saga')
    allQ.append(Q_k)

#%% solve with ADAGRAD (multiple times)

allQ1 = list()
for k in range(K):
    
    Q1_k = problem(f, phi, tol = 1e-9, params = params_adagrad, verbose = True, measure = True)
    Q1_k.solve(solver = 'adagrad')
    allQ1.append(Q1_k)

#%% solve with SVRG (multiple times)

allQ2 = list()
for k in range(K):
    
    Q2_k = problem(f, phi, tol = 1e-9, params = params_svrg, verbose = True, measure = True)
    Q2_k.solve(solver = 'svrg')
    allQ2.append(Q2_k)
    
#%% solve with SSNSP (multiple times, VR)

allP = list()
for k in range(K):
    
    P_k = problem(f, phi, tol = 1e-9, params = params_snspp, verbose = False, measure = True)
    P_k.solve(solver = 'snspp')
    allP.append(P_k)


#%% eval test set loss

kwargs2 = {"A": X_test, "b": y_test}

for P in allP: P.info['test_error'] = eval_test_set(X = P.info["iterates"], loss = logreg_loss, **kwargs2)
for Q in allQ: Q.info['test_error'] = eval_test_set(X = Q.info["iterates"], loss = logreg_loss, **kwargs2)
for Q in allQ1: Q.info['test_error'] = eval_test_set(X = Q.info["iterates"], loss = logreg_loss, **kwargs2)
for Q in allQ2: Q.info['test_error'] = eval_test_set(X = Q.info["iterates"], loss = logreg_loss, **kwargs2)
    
#%% coeffcient frame

all_x = pd.DataFrame(np.vstack((x_sk, P.x, Q.x, Q1.x)).T, columns = ['scikit', 'spp', 'saga', 'adagrad'])

res_to_save = dict()
res_to_save.update(convert_to_dict(allQ))
res_to_save.update(convert_to_dict(allQ1))
res_to_save.update(convert_to_dict(allQ2))
res_to_save.update(convert_to_dict(allP))

np.save('data/output/exp_mnist.npy', res_to_save)

#%% objective plot

fig,ax = plt.subplots(figsize = (4.5, 3.5))

kwargs = {"psi_star": psi_star, "log_scale": True, "lw": 0.4, "markersize": 3}

#Q.plot_objective(ax = ax, ls = '--', **kwargs)
#Q1.plot_objective(ax = ax, ls = '-.', **kwargs)
#Q2.plot_objective(ax = ax, ls = '-.', **kwargs)
#P.plot_objective(ax = ax, **kwargs)


plot_multiple(allQ, ax = ax , label = "saga", ls = '--', **kwargs)
plot_multiple(allQ1, ax = ax , label = "adagrad", ls = '--', **kwargs)
plot_multiple(allQ2, ax = ax , label = "svrg", ls = '--', **kwargs)
plot_multiple(allP, ax = ax , label = "snspp", **kwargs)

ax.set_xlim(-.1,4)
ax.set_ylim(1e-7,)

ax.legend()

fig.subplots_adjust(top=0.96,
                    bottom=0.14,
                    left=0.165,
                    right=0.965,
                    hspace=0.2,
                    wspace=0.2)

if save:
    fig.savefig(f'data/plots/exp_mnist/obj.pdf', dpi = 300)

#%% coefficent plot


fig,ax = plt.subplots(2, 2,  figsize = (7,5))
allQ[0].plot_path(ax = ax[0,0], xlabel = False)
allQ1[0].plot_path(ax = ax[0,1], xlabel = False, ylabel = False)
allQ2[0].plot_path(ax = ax[1,0])
allP[0].plot_path(ax = ax[1,1], ylabel = False)

for a in ax.ravel():
    a.set_ylim(-.25,.25)
    
plt.subplots_adjust(hspace = 0.33)

if save:
    fig.savefig(f'data/plots/exp_mnist/coeff.pdf', dpi = 300)




#%%
fig,ax = plt.subplots(figsize = (4.5, 3.5))

kwargs = {"lw": 1, "markersize": 3}

plot_multiple_error(allQ, ax = ax , label = "saga", ls = '--', **kwargs)
plot_multiple_error(allQ1, ax = ax , label = "adagrad", ls = '--', **kwargs)
plot_multiple_error(allQ2, ax = ax , label = "svrg", ls = '--', **kwargs)
plot_multiple_error(allP, ax = ax , label = "snspp", **kwargs)

ax.set_xlim(-.1,4)
ax.set_ylim(0.46, 0.48)
ax.legend(fontsize = 10)

fig.subplots_adjust(top=0.96,
                    bottom=0.14,
                    left=0.165,
                    right=0.965,
                    hspace=0.2,
                    wspace=0.2)


if save:
    fig.savefig(f'data/plots/exp_mnist/error.pdf', dpi = 300)
    
#%%
# def predict(A,x):
    
#     h = np.exp(A@x)
#     odds = h/(1+h)    
#     y = (odds >= .5)*2 -1
    
#     return y

# def sample_error(A, b, x):
    
#     b_pred = predict(A,x)
#     return (np.sign(b_pred) == np.sign(b)).sum() / len(b)


# sample_error(X_test, y_test, x_sk)
# sample_error(X_test, y_test, Q.x)
# sample_error(X_test, y_test, Q1.x)
# sample_error(X_test, y_test, P.x)



