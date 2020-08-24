"""
@author: Fabian Schaipp
"""

import numpy as np
import matplotlib.pyplot as plt
from ..solver.opt_problem import color_dict

def plot_multiple(allP, ax = None, label = "ssnsp", name = None):
    
    if name is None:
        name = label
    
    if ax is None:
            fig, ax = plt.subplots()
            
    K = len(allP)
    
    all_obj = np.vstack([allP[k]["objective"] for k in range(K)])
    all_mean = all_obj.mean(axis=0)
    all_std = all_obj.std(axis=0)

    all_rt = np.vstack([allP[k]["runtime"] for k in range(K)]).mean(axis=0).cumsum()
    
    try:
        c = color_dict[label]
    except:
        c = color_dict["default"]
        
    ax.plot(all_rt, all_mean, marker = 'o', color = c, label = name)
    ax.fill_between(all_rt, all_mean-2*all_std, all_mean+2*all_std, \
                    color = c, alpha = .5)
        
    return
