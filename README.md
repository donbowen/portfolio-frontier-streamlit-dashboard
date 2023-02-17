# What is this?

Previous students wrote a web app. They used [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/en/latest/index.html) to plot the efficient frontier and tangency portfolio, and then developed a short quiz to assess the risk aversion parameter for a quadratic utility maximizing investor.

Sadly, their site is no longer working because Heroku, where they hosted it, stopped free services. So I'm porting their project here to demonstrate the use of [Streamlit](https://streamlit.io) for dashboard development and deployment. 

[You can see this dashboard in action here!](https://donbowen-dashboard-experiments-app-7w64ar.streamlit.app/)

## Local setup

If you want to get this app working on your computer so you can edit it and build, and you already have a working python / Anaconda installation, open terminal and run these commands sequentially:

```sh
git clone git@github.com:donbowen/dashboard_experiments.git
cd dashboard_experiments

conda env create -f environment.yml
conda activate streamlit-env

streamlit run app.py

spyder # open any IDE you want to modify app 
```

## Further ideas 

1. Github actions to run `update_data_cache.py` once a month.
1. Download more assets, including non-ETFs
1. Exploit Streamlit's cache system to make this faster: 
	- Change code from after the sidebar until the Max Util section to a function that returns the necessary data structures for plotting, and decorate this so it is cached
	- Code after that can remain the same
1. Use plotly so that output graph is interactive (e.g. zoom in on the interesting part of the graph)
	- see code below for pointers
	- `cov_mat` has asset names, add these as labels to scatterplot
	
```python	
## approach 1 for plotly + streamlit: fig.add_trace()

import plotly.graph_objects as go

fig = go.Figure()
fig = fig.add_trace(go.Scatter(x=df.col2,y=df.col1,mode=‘lines’,name=‘line1’))
fig = fig.add_trace(go.Scatter(x=df.col2,y=ucl_array,mode=‘lines’,name=‘ucl =’+str(ucl)))
fig = fig.update_layout(showlegend=True)

st.plotly_chart(fig)	

## approach 2 for plotly + streamlit: 
## make figs with px, then combine via go.Figure(fig1+fig2)

import plotly.express as px
import plotly.graph_objects as go

df   = px.data.iris()

fig1 = px.line(df, x="sepal_width", y="sepal_length")
fig2 = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
fig3 = go.Figure(data=fig1.data + fig2.data)

st.plotly_chart(fig3)	
```