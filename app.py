import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from update_data_cache import get_data

from pypfopt.efficient_frontier import EfficientFrontier

pio.renderers.default='browser' # use when doing dev in Spyder (to show figs)

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
    #### Result: Using the survey, your risk aversion parameter is {risk_aversion:.3f}
    ---
    ### If you want, you can override that parameter here:
    
    '''
    
    risk_aversion = st.number_input('Risk aversion parameter',0.000001,float(5),format='%0.2f',value=risk_aversion)
       
    '''
    ---
    ### Part 2: What is the most leverage are you willing to take on? 
    
    Some people are willing to put all their money in the market. For others, it might make sense to borrow additional money to put into the market. 
    
    For example, leverage is 1 when all your money is in the market, and 2 if you borrowed enough to double your investment in the market.
    
    Allowing leverage to exceed 1x is not typical. 
    '''
       
    leverage = st.number_input('Maximum leverage',1,10,value=1)
    
    '''
    ---
    ### Part 3 (Optional): Upload a custom list of tickers
    
    Must be a csv file with one ticker per line. Maximum of 100 tickers. 
    '''
    
    uploaded_file = st.file_uploader("Choose a CSV file with tickers")
    
    '''
    
    ---
    
    [Source code and contributors here.](https://github.com/donbowen/portfolio-frontier-streamlit-dashboard)
    '''

#############################################
# end: sidebar
#############################################

def get_ef_points(ef, ef_param, ef_param_range):
    """
    Helper function to get the points on the efficient frontier from an EfficientFrontier object
    
    This is _plot_ef without the plotting, and returning the points.
    """
    mus, sigmas = [], []

    # Create a portfolio for each value of ef_param_range
    for param_value in ef_param_range:
        try:
            if ef_param == "utility":
                ef.max_quadratic_utility(param_value)
            elif ef_param == "risk":
                ef.efficient_risk(param_value)
            elif ef_param == "return":
                ef.efficient_return(param_value)
            else:
                raise NotImplementedError(
                    "ef_param should be one of {'utility', 'risk', 'return'}"
                )
        except exceptions.OptimizationError:
            continue
        except ValueError:
            warnings.warn(
                "Could not construct portfolio for parameter value {:.3f}".format(
                    param_value
                )
            )

        ret, sigma, _ = ef.portfolio_performance()
        mus.append(ret)
        sigmas.append(sigma)

    return mus, sigmas 

#############################################
# start: build dashboard (this is cached because nothing here changes due to 
# user input)
#############################################

@st.cache_data
def get_plotting_structures(asset_list=None):
    '''
    Assets is a list of tickers, allowing this to be used with custom list 
    of assets. If none given, uses 200 of the S&P500 as if Feb 2023 (quick - no 
    downloads required). If list is given, will download using
    yfinance. No error handling provided. 

    Returns
    -------
    
        risk_free_rate
        assets          = [rets, vols]
        ef_points       = [rets, vols]
        tangency_port   = [ret_tangent, vol_tangent, sharpe_tangent]
        
    '''
        
    # get prices and risk free rate
    # then calc E(r), COV
    
    if not asset_list:
        
        # use default list of assets and precomputed data
        
        with open('inputs/risk_free_rate.txt', 'r') as f:
            rf_rate = float(f.read())
        
        # get the x,y values for asset in scatter
        
        e_returns = pd.read_csv('inputs/e_returns.csv',index_col=0).squeeze()
        cov_mat   = pd.read_csv('inputs/cov_mat.csv',index_col=0)        
        
    else:
        
        # download them and compute
        
        e_returns, cov_mat, rf_rate = get_data(asset_list)
        
    assets    = [e_returns, np.sqrt(np.diag(cov_mat))] 
    
    # set up the EF object & dups for alt uses
    
    ef            = EfficientFrontier(e_returns, cov_mat)
    ef_max_sharpe = EfficientFrontier(e_returns, cov_mat)
    ef_min_vol    = EfficientFrontier(e_returns, cov_mat)
    
    # # Find+plot the tangency portfolio
        
    ef_max_sharpe.max_sharpe(risk_free_rate=rf_rate)
    ret_tangent, vol_tangent, sharpe_tangent = ef_max_sharpe.portfolio_performance(risk_free_rate=rf_rate)
    
    tangency_port = [ret_tangent, vol_tangent, sharpe_tangent]
            
    # prelim step: get the min vol (vol_min_vol is where we will start the efficient frontier)
    
    ef_min_vol.min_volatility()
    ret_min_vol, vol_min_vol, _ = ef_min_vol.portfolio_performance()
    
    # get the efficient frontier 
    # use risk levels from vol_min_vol to the most risky asset's vol
    # to make faster, just 20 points
    # but we want more points at the front of EF where it is curviest --> logscale 
    
    risk_range     = np.logspace(np.log(vol_min_vol+.000001), 
                                 np.log(assets[1].max()), 
                                 20, 
                                 base=np.e)
    ret_ef, vol_ef = get_ef_points(ef, 'risk', risk_range) 
    
    ef_points      = [ret_ef,vol_ef]
    
    return rf_rate, assets, ef_points, tangency_port

###############################################################################

###############################################################################
# decide on assets: default list or uploaded list
###############################################################################

if uploaded_file is not None:
    asset_list = pd.read_csv(uploaded_file,header=None,names=['asset'])
    asset_list = asset_list['asset'].to_list()[:100] # convert to list, max 100 allowed
else:
    asset_list = None 

###############################################################################
# get E(r) vol of Max Utility portfolio with leverage and RF asset 
###############################################################################

rf_rate, assets, ef_points, tangency_port = get_plotting_structures(asset_list)    

# solve for max util (rf asset + tang port, lev allowed)

mu_cml      = np.array([rf_rate,tangency_port[0]])
cov_cml     = np.array([[0,0],
                        [0,tangency_port[1]]])
ef_max_util = EfficientFrontier(mu_cml,cov_cml,(-leverage+1,leverage))      
    
ef_max_util.max_quadratic_utility(risk_aversion=risk_aversion)

# extract portfolio ret / vol (can't use built in for some reason...)

tang_weight_util_max = ef_max_util.weights[1]
x_util_max           = tang_weight_util_max*tangency_port[1]
max_util_port        = [x_util_max*tangency_port[2]+rf_rate,
                        x_util_max]

#############################################
# start: plot
#############################################

# cml
x_high = assets[1].max()*.8
fig1 = px.line(x=[0,x_high], y=[rf_rate,rf_rate+x_high*tangency_port[2]])
fig1.update_traces(line_color='red', line_width=3)

# ef
fig2 = px.line(y=ef_points[0], x=ef_points[1])
fig2.update_traces(line_color='blue', line_width=3)

# assets 
fig3 = px.scatter(y=assets[0], x=assets[1],hover_name=assets[0].index)

# tang + max_util 
points = pd.DataFrame({
                    'port': ['Max utility<br>portfolio','Tangency<br>portfolio'],
                    'y': [max_util_port[0],tangency_port[0]],
                    'x': [max_util_port[1],tangency_port[1]],
                    'sym' : ['star','star'],
                    'size' : [2,2],
                    'color':['blue','red']})

fig4 = px.scatter(points,x='x',y='y',
                  symbol='port',
                  hover_name='port',text="port",
                  color_discrete_sequence = ['red','blue'],
                  symbol_sequence=['star','star'],
                  labels={'x':'Volatility', 'y':'Expected Returns'},
                  size=[2,2],
                  color='port')

# perfect formatting text annotation color matches marker
fig4.update_traces(showlegend=False)
def trace_specs(t):    
    # Text annotation color matches marker'
    # If statement flips the red marker underneith to avoid overlapping text'
    if t.marker.color == 'red' and (abs(max_util_port[1]-tangency_port[1])<.02):
        return t.update(textfont_color=t.marker.color, textposition='bottom center')
    else:
        return t.update(textfont_color=t.marker.color, textposition='top center')

fig4.for_each_trace(lambda t: trace_specs(t))
fig4.update_layout(yaxis_range = [0,0.5],
                   xaxis_range = [0,0.5],
                   font={'size':16},
                   yaxis = dict(tickfont = dict(size=20),titlefont = dict(size=20)),
                   xaxis = dict(tickfont = dict(size=20),titlefont = dict(size=20)),
                   
                   )

fig5 = go.Figure(data=fig1.data + fig2.data + fig3.data + fig4.data, layout = fig4.layout)
fig5.update_layout(height=600) 

st.plotly_chart(fig5,use_container_width=True)


'''
- The chart is interactive: zoom, hover to see tickers
- Expected returns and volatility are annualized measures
- The calculation of expected returns uses CAPM, but will be inaccuracute on a forward looking basis
- Blue line is the efficient frontier and the blue start is the optimal "all-equity" portfolio
- Red line is the "capital market line" representing a portfolio that combines the risk free asset and the tangency portfolio
- The red star is the optimal portfolio combining the risk free asset and the tangency portfolio, based on your risk aversion parameter and choice of maximum allowable leverage
- If your leverage is more than 1 and your risk aversion low enough, the optimal portfolio might involve borrowing money to invest in equities; if so, the red star will be to the right of the blue star
'''
