import numpy as np
import pandas as pd
import streamlit as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pypfopt import plotting
from pypfopt.efficient_frontier import EfficientFrontier

import copy

# Page config
st.set_page_config(
    "Portfolio Opt by WSB, Ported to Streamlit by Don Bowen",
    "📊",
    initial_sidebar_state="expanded",
    layout="wide",
)

"""
# CAPM Portfolio Optimization with Risk Aversion Adjustment 
"""

#############################################
# start: sidebar
#############################################

with st.sidebar:

    # % chance lose, $ lose, % chance win, $win, CARA formula e, CARA formula V
    qs ={1 :[.50,0,.50,10   ],
         2 :[.50,0,.50,1000 ],
         3 :[.90,0,.10,10   ],
         4 :[.90,0,.10,1000 ],
         5 :[.25,0,.75,100  ],
         6 :[.75,0,.25,100  ]}    

    """
    ## Risk aversion assessment

    ### Part 1: How much would you pay to enter the following lotteries?
    """
    ans = {}
    for i in range(1,len(qs)+1):
        rn = qs[i][0]*qs[i][1] + qs[i][2]*qs[i][3]
        ans[i] = st.slider(f'{int(qs[i][0]*100)}% chance of \${qs[i][1]} and {int(qs[i][2]*100)}% chance of \${qs[i][3]}',
                           0.0,rn,rn,0.1, key=i)
    
    risk_aversion = 0
    for i in range(1,len(qs)+1):
        
        # quadratic util: mu - 0.5 * A * var
        # here, set util = willing to pay, solve for A
        
        exp = qs[i][0]* qs[i][1]          +  qs[i][2]* qs[i][3]
        var = qs[i][0]*(qs[i][1]-exp)**2  +  qs[i][2]*(qs[i][3]-exp)**2
        
        implied_a = 2*(exp-ans[i])/var
           
        risk_aversion += implied_a
  
    if risk_aversion < 0.000001: # avoid the float error when risk_aversion is too small
       risk_aversion = 0.000001    
       
    f'''
    ### Result: Your risk aversion parameter is {risk_aversion:.3f}
    '''
       
    '''
    ### Part 2: What is the most leverage are you willing to take on? 
    
    For example, some people are willing to put all their money in the market. For others, it might make sense to borrow additional money to put into the market. 
    
    For example, leverage is 1 when all your money is in the market, and 2 if you borrowed enough to double your investment in the market.
    '''
       
    leverage = st.slider('',1,10,1)   
    
    '''
    
    ---
    
    [Source code and contributors here.](https://github.com/donbowen/portfolio-frontier-streamlit-dashboard)
    '''

#############################################
# end: sidebar
#############################################

#############################################
# start: build dashboard (everything here can be in function and cached)
#############################################

# get prices and risk free rate
# then calc E(r), COV

with open('inputs/risk_free_rate.txt', 'r') as f:
    risk_free_rate = float(f.read())

e_returns = pd.read_csv('inputs/e_returns.csv',index_col=0).squeeze()
cov_mat   = pd.read_csv('inputs/cov_mat.csv',index_col=0)

x_vals      = np.sqrt(np.diag(cov_mat.to_numpy()))

# start plotting

fig, ax = plt.subplots(figsize=(8, 4))

# set up the EF object & dups for alt uses

ef            = EfficientFrontier(e_returns, cov_mat)
ef_max_sharpe = copy.copy(ef)
ef_min_vol    = copy.copy(ef)

# get the min vol (std_min_vol is where we will start the efficient frontier)

ef_min_vol.min_volatility()
ret_min_vol, std_min_vol, _ = ef_min_vol.portfolio_performance()

# now plot the efficient frontier for each risk level from minimum to max

risk_range = np.linspace(std_min_vol, x_vals.max(), 200)
plotting.plot_efficient_frontier(ef, ef_param="risk", ef_param_range=risk_range,
                                 ax=ax, show_assets=True)
 
# # Find+plot the tangency portfolio

ef_max_sharpe.max_sharpe(risk_free_rate=risk_free_rate)
ret_tangent, std_tangent, sharpe_tangent = ef_max_sharpe.portfolio_performance()
ax.scatter(std_tangent, ret_tangent, marker="*", s=100, c="r", label="Max Sharpe")

# add the CML line from (0,rf) to (x,rf+sharpe*x) for some sensible x

x_vals      = np.sqrt(np.diag(cov_mat.to_numpy()))
x_to_plot   = x_vals.max()*.8
x_values    = [0,              x_to_plot]
y_values    = [risk_free_rate, x_to_plot*sharpe_tangent+risk_free_rate]

plt.plot(x_values, y_values,label='Capital Market Line')

# get the max utility port by giving the package 2 assets: the rf asset and tang port

mu_cml      = np.array([risk_free_rate,ret_tangent])
cov_cml     = np.array([[0,0],[0,std_tangent]])

#############################################
# start: update dashboard with Max Utility suggestion (risk aversion input)
#############################################

ef_max_util = EfficientFrontier(mu_cml,cov_cml,(-leverage+1,leverage))      
         
ef_max_util.max_quadratic_utility(risk_aversion=risk_aversion)

# the weight in the tangency port is 
tang_weight = ef_max_util.weights[1]

# which implies the ret_maxU port and vol of that port
x_util_max  = tang_weight*std_tangent
y_util_max  = x_util_max*sharpe_tangent+risk_free_rate

# note: the following commented line yields ret_maxU, which equals y_util_max above
# HOWEVER, std_maxU is incorrect (squaring or sqrt it doesn't fix)     
# ret_maxU, std_maxU, _ = ef_max_util.portfolio_performance()

ax.scatter(x_util_max, y_util_max, marker="*", s=100, c="blue", label="Max Util")

# Output
ax.legend(loc='lower right')
plt.tight_layout()

st.pyplot(fig=fig)
