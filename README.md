# What is this?

Previous students wrote a web app, and I'm porting it here to demonstrate the use of streamlit. 

Powered by [Streamlit](https://streamlit.io), [pandas](https://pandas.pydata.org/docs/), and [seaborn](seaborn.pydata.org/).

## Local setup

Assumes you have a [working python 3.9 installation](https://tech.gerardbentley.com/python/beginner/2022/01/29/install-python.html).

```sh
git clone git@github.com:donbowen/dashboard_experiments.git
cd dashboard_experiments

conda env create -f environment.yml
conda activate streamlit-env

streamlit run app.py

spyder # open any IDE you want to modify app 
```

## Further ideas 

1. Github actions to update asset download once a month.
1. Download more assets, including non-ETFs
1. Use plotly so that output graph is interactive. 
	- see code belw 
	- `cov_mat` has asset names, add these as labels
	
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