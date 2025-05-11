"""
@author: Cobra Micro Solutions

"""
import numpy as np 
import pandas as pd  
import plotly.express as px 
import streamlit as st 
from streamlit_autorefresh import st_autorefresh
import subprocess
import random
from datetime import datetime, timedelta, date
from faker import Faker
import faker_commerce

year = int((datetime.now() - timedelta(days=7)).strftime("%Y"))
month = int((datetime.now() - timedelta(days=7)).strftime("%m"))
day = int((datetime.now() - timedelta(days=7)).strftime("%d"))
year_2 = int((datetime.now() + timedelta(days=21)).strftime("%Y"))
month_2 = int((datetime.now() + timedelta(days=21)).strftime("%m"))
day_2= int((datetime.now() + timedelta(days=21)).strftime("%d"))

st.set_page_config(
    page_title="Real-Time Productie Planning Dashboard",
    page_icon="✅",
    layout="wide"
)
    
st_autorefresh(interval=0.5 * 60 * 1000, key="dataframerefresh")

fake = Faker()
fake.add_provider(faker_commerce.Provider)
product_list = []
production_data_dict = {'Start_date' : [],
                   'Week' : [],
                   'Bweek' : [],
                   'Product_name' : [],
                   'Operation' : [],
                   'Hours' : [],}
for _ in range(15):
    product_name = fake.ecommerce_name()
    product_list.append(product_name)

operations = ['Welding', 'Milling', 'Lathe']

for operation in operations:
    for _ in range(250):  
        start_date = fake.date_between(start_date=date(year,month,day), end_date=date(year_2,month_2,day_2))
        Week = start_date.strftime('%Y%U')
        bweek = 'Backlog' if start_date < date.today() else ''
        production_data_dict['Hours'].append(random.randint(2, 12)) 
        production_data_dict['Start_date'].append(start_date)
        production_data_dict['Week'].append(Week)
        production_data_dict['Bweek'].append(bweek)  
        production_data_dict['Operation'].append(operation)  
        production_data_dict['Product_name'].append(product_list[random.randint(0,14)])
df = pd.DataFrame(production_data_dict).sort_values('Start_date')

st.title("Real-Time Productie Planning Dashboard")

if st.button('Rerun App'):
    st.rerun()


job_filter = st.selectbox("Selecteer een bewerking", pd.unique(df["Operation"]))
placeholder = st.empty()
df = df[df["Operation"] == job_filter]

graph_df = (df
        .groupby(['Week'])['Hours'].sum()
        .reset_index()
        .sort_values('Week', ascending=True)
        .assign(drop=1)
        .assign(row_num=lambda x: x.groupby('drop').cumcount())
        .drop('drop',axis=1)
        )

backlog_kpi = df[df['Bweek']=='Backlog']
backlog_kpi = np.sum(backlog_kpi['Hours'])
realized_hours_df = pd.DataFrame({'row_number': range(0,11), 'Hours': [random.randint(95, 140) for _ in range(11)]})
realized_hours_kpi = realized_hours_df[realized_hours_df['row_number']==10]
realized_hours_kpi = int(realized_hours_kpi['Hours'].to_string(header=False, index=False))
final_df = df.rename(columns={'Start_date' : 'Start date', 'Product_name' : 'Productname'})

with placeholder.container():
    kpi1, kpi2 = st.columns(2)
    kpi1.metric(
        label=f"Backlog: {job_filter}",
        value=round(backlog_kpi)
    )

    kpi2.metric(
        label=f"Realized hours week 202350:",
        value=realized_hours_kpi,
        delta=-120 + realized_hours_kpi,
    )
    fig_col1, spacer, fig_col2 = st.columns([1, 0.1, 1])
    with fig_col1:
        st.markdown(f"### Load for {job_filter}:")
        present_weeks = graph_df['Week'].drop_duplicates().sort_values().tolist()
        row_num = graph_df['row_num'].drop_duplicates().sort_values().tolist()
        fig = px.bar(graph_df, x='row_num', y='Hours',
                     labels={
                         'row_num' : 'Weeks'
                     })
        line_fig = px.line(graph_df, x='row_num', y=[120] * len(row_num))
        for trace in line_fig.data:
            trace.update(line=dict(color='red')) 
        for trace in line_fig.data:
            fig.add_trace(trace)

        fig.update_layout(
            xaxis = dict(
            tickmode = 'array',
            tickvals = row_num,
            ticktext = present_weeks
            )
        )
        st.write(fig)
        with fig_col2:
            st.markdown("### Realized hours (last 10 weeks):")
            fig2 = px.bar(realized_hours_df, x='row_number', y='Hours',
                     labels={
                         'row_number' : 'Weeks'
                     })
            line_fig = px.line(realized_hours_df, x='row_number', y=[120] * 11)
            for trace in line_fig.data:
                trace.update(line=dict(color='red'))  
            for trace in line_fig.data:
                fig2.add_trace(trace)
                
            fig2.update_layout(
                xaxis = dict(
                tickmode = 'array',
                tickvals = row_num,
                ticktext = [f"2023{week}" for week in range(40, 51)]
            )
            )
            
            st.write(fig2)
            
    def color_past_dates(row):
        today = datetime.now().date()
        if pd.to_datetime(row['Start date']).date() < today:
            return ['background-color: lightcoral']*len(row)
        else:
            return ['']*len(row)
    st.markdown("### Detailed Data View")
    st.dataframe(final_df.style.apply(color_past_dates, axis=1), hide_index=True, width=2500)
    